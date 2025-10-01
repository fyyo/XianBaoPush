# main.py - Application entry point
import sys
import threading
from PyQt6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from apscheduler.schedulers.background import BackgroundScheduler
from src.core.config_manager import load_rss_configs, save_config, load_affiliate_config
from src.core.rss_fetcher import parse_feed, generate_entry_id, fetch_webpage_content
from src.core.qq_pusher import send_group_message
from src.core.affiliate_converter import AffiliateConverter
from src.utils.text_cleaner import summarize_text, clean_html_tags
import logging
import os
import json
from logging.handlers import RotatingFileHandler

# 创建全局停止标志
_stop_flag = threading.Event()

# 创建一个主日志记录器（避免重复日志）
logger = logging.getLogger(__name__)
if not logger.handlers:  # 避免重复添加处理器
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # 控制台处理器
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    # 确保logs目录存在
    import os
    if not os.path.exists("logs"):
        os.makedirs("logs")

    # 文件处理器（带轮换）
    file_handler = RotatingFileHandler("logs/rss_qq_app.log", maxBytes=1024*1024, backupCount=5, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 强制刷新日志处理器
    logger.handlers[0].flush()
    logger.handlers[1].flush()

# 为apscheduler单独设置日志级别
logging.getLogger('apscheduler').setLevel(logging.WARNING)

# 全局调度器变量 - 使用线程锁保护
scheduler = None
scheduler_lock = threading.Lock()
SENT_ENTRIES_FILE = "sent_entries.json"
sent_entries_lock = threading.Lock()

def load_system_state():
    """加载系统状态（包含已发送条目、首次运行状态、时间分界点）"""
    with sent_entries_lock:
        default_state = {
            "sent_entries": [],
            "first_run_completed": False,
            "last_processed_time": {}
        }
        
        if not os.path.exists(SENT_ENTRIES_FILE):
            return default_state
        
        try:
            with open(SENT_ENTRIES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 兼容旧格式：如果文件只包含数组，转换为新格式
            if isinstance(data, list):
                return {
                    "sent_entries": data,
                    "first_run_completed": True,  # 如果有旧数据，说明不是首次运行
                    "last_processed_time": {}
                }
            
            # 确保所有必要的字段存在
            state = default_state.copy()
            state.update(data)
            return state
            
        except Exception as e:
            logging.error(f"加载系统状态失败: {e}")
            return default_state

def save_system_state(sent_entries, first_run_completed, last_processed_time):
    """保存系统状态"""
    with sent_entries_lock:
        try:
            state = {
                "sent_entries": list(sent_entries),
                "first_run_completed": first_run_completed,
                "last_processed_time": last_processed_time
            }
            
            with open(SENT_ENTRIES_FILE, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存系统状态失败: {e}")

def load_sent_entries():
    """加载已发送条目记录（兼容接口）"""
    state = load_system_state()
    return set(state["sent_entries"])

def is_first_run():
    """检查是否为首次运行"""
    state = load_system_state()
    return not state["first_run_completed"]

def load_last_processed_time(rss_url):
    """加载RSS源的最后处理时间"""
    state = load_system_state()
    return state["last_processed_time"].get(rss_url)

def save_last_processed_time(rss_url, timestamp):
    """保存RSS源的最后处理时间"""
    state = load_system_state()
    state["last_processed_time"][rss_url] = timestamp
    
    # 保存整个状态
    save_system_state(
        set(state["sent_entries"]),
        state["first_run_completed"],
        state["last_processed_time"]
    )

def mark_first_run_completed():
    """标记首次运行完成"""
    state = load_system_state()
    state["first_run_completed"] = True
    
    # 保存整个状态
    save_system_state(
        set(state["sent_entries"]),
        True,
        state["last_processed_time"]
    )

def process_and_send():
    """处理RSS并发送消息的主函数"""
    # 检查停止标志
    if _stop_flag.is_set():
        logger.info("收到停止信号，跳过RSS处理")
        return
        
    configs = load_rss_configs()
    if not configs:
        logger.info("没有配置的RSS源，跳过处理")
        return

    # 加载完整配置（AffiliateConverter需要完整配置）
    from src.core.config_manager import load_config
    full_config = load_config()
    affiliate_config = full_config.get('affiliate_config', {})
    
    affiliate_converter = None
    if affiliate_config and any(affiliate_config.get(platform, {}).get('enabled', False)
                              for platform in ['dataoke', 'jingpinku', 'pdd']):
        affiliate_converter = AffiliateConverter(full_config)  # 传递完整配置
        logger.info("返利转链功能已启用")
    else:
        logger.info("返利转链功能未配置，将使用原始链接")

    sent_entries = load_sent_entries()
    first_run = is_first_run()
    
    if first_run:
        logger.info("首次启动，启用保护机制 - 只处理最新10条")
    
    for config in configs:
        try:
            entries = parse_feed(config["rss_url"])
            if not entries:
                logger.warning(f"RSS源 '{config['rss_url']}' 未返回任何内容，跳过处理")
                continue

            # 获取最后处理时间
            last_processed_time = load_last_processed_time(config["rss_url"])
            
            if first_run:
                # 首次启动：只处理最新10条
                entries = entries[:10]
                logger.info(f"首次启动保护：RSS源 '{config['rss_url']}' 只处理最新 {len(entries)} 条")
                
                # 记录首次启动处理的第一条线报时间作为分界点
                if entries:
                    # RSS条目通常按时间降序排列，取第一条（最新的）作为时间分界点
                    # 后续运行只处理时间晚于这个分界点的新线报
                    first_entry = entries[0]
                    if hasattr(first_entry, 'published_parsed') and first_entry.published_parsed:
                        import time
                        import calendar
                        # 正确处理时区：RSS时间通常是UTC，需要转换为本地时间戳
                        cutoff_time = calendar.timegm(first_entry.published_parsed)
                        save_last_processed_time(config["rss_url"], cutoff_time)
                        # 显示北京时间
                        beijing_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(cutoff_time))
                        logger.info(f"设置时间分界点：{beijing_time} (北京时间)")
            else:
                # 非首次启动：只处理时间晚于分界点的条目
                if last_processed_time:
                    import time as time_module
                    import calendar
                    filtered_entries = []
                    for entry in entries:
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            # 统一使用calendar.timegm处理RSS时间（UTC转时间戳）
                            entry_time = calendar.timegm(entry.published_parsed)
                            if entry_time > last_processed_time:
                                filtered_entries.append(entry)
                    
                    entries = filtered_entries
                    if entries:
                        logger.info(f"时间过滤：RSS源 '{config['rss_url']}' 发现 {len(entries)} 条新线报")
                    else:
                        logger.info(f"时间过滤：RSS源 '{config['rss_url']}' 没有新线报")
                        continue

            # 批量转链控制
            batch_settings = affiliate_config.get('batch_settings', {}) if affiliate_config else {}
            max_convert_per_batch = batch_settings.get('max_convert_per_batch', 5)
            convert_enabled = batch_settings.get('convert_enabled', True)
            
            processed_count = 0
            converted_count = 0  # 当前批次已转链数量
            
            for entry in entries:
                # 在循环中检查停止标志
                if _stop_flag.is_set():
                    logger.info("收到停止信号，中断RSS条目处理")
                    return
                    
                try:
                    entry_id = generate_entry_id(config["rss_url"], entry)
                    
                    # 去重机制：跳过已发送的条目
                    if entry_id in sent_entries:
                        continue

                    clean_title = clean_html_tags(entry.title) if entry.title else "无标题"
                    link = getattr(entry, 'link', '') or ''
                    
                    # 获取网页内容
                    webpage_content = ""
                    if link:
                        webpage_content = fetch_webpage_content(link)
                    
                    # 内容处理策略：使用高级清理功能
                    message_content = ""
                    raw_content = ""
                    
                    if webpage_content:
                        raw_content = webpage_content
                    else:
                        # 如果没有网页内容，使用RSS摘要
                        raw_content = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
                    
                    if raw_content:
                        # 使用高级文本清理功能
                        from src.utils.text_cleaner import advanced_text_cleanup
                        message_content = advanced_text_cleanup(raw_content, clean_title, max_length=1200)
                    
                    # 如果清理后内容为空，使用标题
                    if not message_content:
                        message_content = clean_title

                    # 批量返利转链处理：控制每批转链数量
                    should_convert = (convert_enabled and
                                    affiliate_converter and
                                    message_content and
                                    converted_count < max_convert_per_batch)
                    
                    if should_convert:
                        try:
                            # 检查是否包含可转换的商品链接
                            urls = affiliate_converter._extract_urls(message_content)
                            if urls:  # 只有包含商品链接才进行转换
                                converted_content = affiliate_converter.convert_links(message_content)
                                if converted_content != message_content:
                                    logger.info(f"成功转换返利链接 ({converted_count + 1}/{max_convert_per_batch}): {entry_id}")
                                    message_content = converted_content
                                    converted_count += 1
                        except Exception as e:
                            logger.error(f"返利转链处理失败: {e}")
                            # 转链失败时保留原内容，不影响推送

                    # 长度控制：自动截断过长内容
                    if len(message_content) > 1500:
                        message_content = message_content[:1500] + "..."
                        logger.info(f"内容过长，已截断: {entry_id}")

                    # 推送策略：在消息末尾添加原链接
                    if link:
                        if message_content:
                            message_content += f"\n\n📰 完整线报：{link}"
                        else:
                            message_content = f"📰 完整线报：{link}"

                    # 发送消息
                    if message_content and send_group_message(config['llonebot_api_url'], config["group_id"], message_content):
                        sent_entries.add(entry_id)
                        processed_count += 1
                        logger.info(f"成功推送: {clean_title[:50]}...")
                    else:
                        logger.warning(f"推送失败: {clean_title[:50]}...")
                
                except Exception as e:
                    logger.error(f"处理RSS条目 '{getattr(entry, 'title', 'N/A')}' 时出错: {e}", exc_info=True)
            
            # 更新时间分界点：处理完成后，将最新条目的时间设为新的分界点
            if processed_count > 0:
                logger.info(f"RSS源 '{config['rss_url']}' 成功处理 {processed_count} 条新内容")
                
                # 更新时间分界点到最新处理的条目
                if entries:
                    # 取第一条条目（最新的）作为新的时间分界点
                    latest_entry = entries[0]
                    if hasattr(latest_entry, 'published_parsed') and latest_entry.published_parsed:
                        import time
                        import calendar
                        # 正确处理时区：RSS时间通常是UTC，需要转换为本地时间戳
                        new_cutoff_time = calendar.timegm(latest_entry.published_parsed)
                        save_last_processed_time(config["rss_url"], new_cutoff_time)
                        # 显示北京时间
                        beijing_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(new_cutoff_time))
                        logger.info(f"更新时间分界点：{beijing_time} (北京时间)")
        
        except Exception as e:
            logger.error(f"处理RSS源 '{config.get('rss_url', 'N/A')}' 时发生严重错误: {e}", exc_info=True)
    
    # 保存系统状态（包括已发送记录、首次运行标记等）
    state = load_system_state()
    save_system_state(
        sent_entries,
        True if first_run else state["first_run_completed"],
        state["last_processed_time"]
    )
    
    # 标记首次运行完成
    if first_run:
        logger.info("首次启动保护机制已完成")

def update_scheduler(scheduler_instance, configs):
    """更新调度器"""
    if scheduler_instance:
        scheduler_instance.remove_all_jobs()
        for config in configs:
            interval = config.get("interval", 60)
            job_id = f"rss_{hash(config['rss_url'])}"
            scheduler_instance.add_job(
                process_and_send,
                'interval',
                minutes=interval,
                id=job_id,
                replace_existing=True
            )
            logger.info(f"已添加定时任务: {config['rss_url']} (间隔: {interval}分钟)")

def start_scheduler():
    """启动调度器"""
    global scheduler
    
    with scheduler_lock:
        # 检查是否已有调度器在运行
        if scheduler and scheduler.running:
            logger.info("调度器已在运行中，跳过启动")
            return
            
        # 清除停止标志
        _stop_flag.clear()
        
        configs = load_rss_configs()
        if configs:
            # 创建新的调度器实例
            scheduler = BackgroundScheduler()
            update_scheduler(scheduler, configs)
            scheduler.start()
            logger.info("RSS监控调度器已启动，将按配置的间隔时间执行定时推送")
        else:
            logger.info("没有配置RSS源，调度器未启动")

def stop_scheduler():
    """停止调度器"""
    global scheduler
    
    # 设置停止标志
    _stop_flag.set()
    logger.info("已设置停止标志")
    
    with scheduler_lock:
        if scheduler and scheduler.running:
            try:
                # 强制停止所有任务
                scheduler.remove_all_jobs()
                logger.info("已移除所有调度任务")
                
                # 等待调度器完全停止
                scheduler.shutdown(wait=True)
                logger.info("调度器已完全停止")
                
                scheduler = None
                logger.info("RSS监控调度器已停止并清空")
            except Exception as e:
                logger.error(f"停止调度器时出错: {e}")
                # 强制设置为None
                scheduler = None
        else:
            logger.info("调度器未在运行")

def main():
    """主函数 - 启动GUI应用"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("智能RSS线报推送系统")
    app.setApplicationVersion("4.0")
    app.setOrganizationName("RSS推送助手")
    
    # 创建主窗口
    main_win = MainWindow()
    main_win.show()
    
    # 启动应用循环
    sys.exit(app.exec())

if __name__ == "__main__":
    main()