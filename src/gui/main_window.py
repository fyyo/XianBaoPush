# src/gui/main_window.py - 智能RSS线报推送系统主窗口
import sys
import subprocess
import pkg_resources
import os
import time
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout,
                             QWidget, QHBoxLayout, QLabel, QFrame, QStatusBar,
                             QMessageBox, QTextEdit, QDialog, QLineEdit, QPlainTextEdit)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import QSize, Qt, QThread, pyqtSignal, QTimer
from .config_dialog import ConfigDialog
import threading

class CheckRequirementsThread(QThread):
    """检查环境的线程"""
    finished = pyqtSignal(list)

    def run(self):
        missing_packages = []
        try:
            with open('requirements.txt', 'r', encoding='utf-8') as f:
                requirements = [line.strip() for line in f if line.strip()]
            
            for package in requirements:
                try:
                    pkg_resources.require(package)
                except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
                    # 从包名中提取纯名称，例如 "PyQt6==6.7.0" -> "PyQt6"
                    package_name = package.split('==')[0].split('>')[0].split('<')[0]
                    missing_packages.append(package_name)
        except Exception as e:
            # 如果requirements.txt读取失败等
            missing_packages.append(f"检查时发生错误: {e}")
            
        self.finished.emit(missing_packages)

class InstallRequirementsThread(QThread):
    """安装依赖的线程"""
    finished = pyqtSignal(bool, str)

    def run(self):
        try:
            # 使用国内镜像加速
            command = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"]
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            self.finished.emit(True, result.stdout)
        except subprocess.CalledProcessError as e:
            self.finished.emit(False, e.stderr)
        except Exception as e:
            self.finished.emit(False, str(e))


class LogMonitorThread(QThread):
    """日志监控线程"""
    log_updated = pyqtSignal(str)
    
    def __init__(self, log_file_path):
        super().__init__()
        self.log_file_path = log_file_path
        self.running = True
        self.last_position = 0
        
    def run(self):
        """监控日志文件变化"""
        while self.running:
            try:
                if os.path.exists(self.log_file_path):
                    with open(self.log_file_path, 'r', encoding='utf-8') as f:
                        # 移动到上次读取的位置
                        f.seek(self.last_position)
                        new_lines = f.read()
                        
                        if new_lines:
                            # 发送新的日志内容
                            self.log_updated.emit(new_lines)
                            # 更新位置
                            self.last_position = f.tell()
                
                # 每秒检查一次
                time.sleep(1)
            except Exception as e:
                print(f"日志监控错误: {e}")
                time.sleep(5)  # 出错时等待更长时间
                
    def stop(self):
        """停止监控"""
        self.running = False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("智能RSS线报推送系统 v4.0")
        self.setGeometry(100, 100, 1000, 700)
        self.setMinimumSize(800, 600)
        
        # 初始化日志监控
        self.log_monitor = None
        self.log_file_path = "logs/rss_qq_app.log"

        self.setup_ui()
        self.setup_log_monitor()
        self.check_requirements()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 左侧控制面板
        control_panel = QFrame()
        control_panel.setFrameShape(QFrame.Shape.StyledPanel)
        control_panel.setMaximumWidth(300)
        
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(15, 15, 15, 15)
        control_layout.setSpacing(15)
        
        title_label = QLabel("🚀 智能RSS线报推送系统")
        title_font = QFont("Microsoft YaHei", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        control_layout.addWidget(title_label)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        control_layout.addWidget(line)

        # 环境管理按钮
        env_label = QLabel("📦 环境管理")
        env_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        control_layout.addWidget(env_label)
        
        self.check_button = self.create_button("🔄 检查环境", "检查Python依赖包是否完整")
        self.install_button = self.create_button("📥 安装依赖", "一键安装所有缺失的依赖包")
        
        control_layout.addWidget(self.check_button)
        control_layout.addWidget(self.install_button)
        
        # 分隔线
        line2 = QFrame()
        line2.setFrameShape(QFrame.Shape.HLine)
        line2.setFrameShadow(QFrame.Shadow.Sunken)
        control_layout.addWidget(line2)
        
        # 配置管理按钮
        config_label = QLabel("⚙️ 配置管理")
        config_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        control_layout.addWidget(config_label)
        
        self.config_button = self.create_button("🔧 打开配置", "配置RSS源和返利API")
        control_layout.addWidget(self.config_button)
        
        # 分隔线
        line3 = QFrame()
        line3.setFrameShape(QFrame.Shape.HLine)
        line3.setFrameShadow(QFrame.Shadow.Sunken)
        control_layout.addWidget(line3)
        
        # 测试功能按钮
        test_label = QLabel("🧪 测试功能")
        test_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        control_layout.addWidget(test_label)
        
        self.test_convert_button = self.create_button("🔗 测试转链", "测试返利链接转换功能")
        control_layout.addWidget(self.test_convert_button)
        
        # 分隔线
        line4 = QFrame()
        line4.setFrameShape(QFrame.Shape.HLine)
        line4.setFrameShadow(QFrame.Shadow.Sunken)
        control_layout.addWidget(line4)
        
        # 服务控制按钮
        service_label = QLabel("🎯 服务控制")
        service_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        control_layout.addWidget(service_label)
        
        self.start_button = self.create_button("▶️ 启动服务", "启动后台RSS推送服务")
        self.stop_button = self.create_button("⏹️ 停止服务", "停止后台服务")
        
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addStretch()

        # 右侧日志显示区域
        log_frame = QFrame()
        log_frame.setFrameShape(QFrame.Shape.StyledPanel)
        
        log_layout = QVBoxLayout(log_frame)
        log_layout.setContentsMargins(15, 15, 15, 15)
        
        log_title = QLabel("📋 系统日志")
        log_title.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        log_layout.addWidget(log_title)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        # 初始显示系统信息
        self.log_text.append("=== 智能RSS线报推送系统 v4.0 ===")
        self.log_text.append("支持淘宝、京东、拼多多返利转链")
        self.log_text.append("正在初始化日志监控...")
        self.log_text.append("=" * 50)
        log_layout.addWidget(self.log_text)
        
        # 添加到主布局
        main_layout.addWidget(control_panel)
        main_layout.addWidget(log_frame, 1)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("正在初始化...")

        self.apply_stylesheet()

        # 连接信号
        self.check_button.clicked.connect(self.check_requirements)
        self.install_button.clicked.connect(self.install_requirements)
        self.config_button.clicked.connect(self.open_config_dialog)
        self.test_convert_button.clicked.connect(self.open_test_convert_dialog)
        self.start_button.clicked.connect(self.start_rss_service)
        self.stop_button.clicked.connect(self.stop_rss_service)
        
        # 初始状态下禁用核心功能
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.install_button.hide() # 默认隐藏安装按钮
        
        # 服务状态
        self.service_running = False
        
    def setup_log_monitor(self):
        """设置日志监控"""
        try:
            # 确保logs目录存在
            os.makedirs("logs", exist_ok=True)
            
            # 如果日志文件存在，先加载现有内容
            if os.path.exists(self.log_file_path):
                self.load_existing_logs()
            
            # 启动日志监控线程
            self.log_monitor = LogMonitorThread(self.log_file_path)
            self.log_monitor.log_updated.connect(self.append_log)
            self.log_monitor.start()
            
            self.log_text.append("✅ 日志监控已启动")
        except Exception as e:
            self.log_text.append(f"❌ 日志监控启动失败: {str(e)}")
            
    def load_existing_logs(self):
        """加载现有的日志内容（最后100行）"""
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # 只显示最后100行
                recent_lines = lines[-100:] if len(lines) > 100 else lines
                
                if recent_lines:
                    self.log_text.append("\n=== 最近的日志记录 ===")
                    for line in recent_lines:
                        self.log_text.insertPlainText(line.rstrip() + '\n')
                
                # 设置日志监控的起始位置为文件末尾
                f.seek(0, 2)  # 移动到文件末尾
                if self.log_monitor:
                    self.log_monitor.last_position = f.tell()
        except Exception as e:
            self.log_text.append(f"❌ 加载历史日志失败: {str(e)}")
            
    def append_log(self, new_content):
        """追加新的日志内容"""
        if new_content.strip():
            # 移动光标到末尾
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.log_text.setTextCursor(cursor)
            
            # 插入新内容
            self.log_text.insertPlainText(new_content)
            
            # 自动滚动到底部
            scrollbar = self.log_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
            
    def closeEvent(self, event):
        """窗口关闭事件"""
        # 停止日志监控
        if self.log_monitor:
            self.log_monitor.stop()
            self.log_monitor.wait(2000)  # 等待最多2秒
            
        # 停止RSS服务
        if self.service_running:
            self.stop_rss_service()
            
        event.accept()

    def create_button(self, text, tooltip):
        button = QPushButton(text)
        button.setFont(QFont("Microsoft YaHei", 10))
        button.setIconSize(QSize(24, 24))
        button.setToolTip(tooltip)
        button.setMinimumHeight(40)
        return button

    def check_requirements(self):
        self.status_bar.showMessage("正在检查环境...")
        self.log_text.append("开始检查环境依赖...")
        self.check_thread = CheckRequirementsThread()
        self.check_thread.finished.connect(self.on_check_finished)
        self.check_thread.start()

    def on_check_finished(self, missing):
        if not missing:
            self.status_bar.showMessage("✅ 环境正常，可以启动服务。")
            self.log_text.append("✅ 所有依赖均已安装，环境正常！")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.install_button.hide()
            QMessageBox.information(self, "环境检查", "所有依赖均已安装，环境正常！")
        else:
            self.status_bar.showMessage(f"⚠️ 发现缺失的依赖: {', '.join(missing)}")
            self.log_text.append(f"⚠️ 发现缺失的依赖: {', '.join(missing)}")
            self.start_button.setEnabled(False)
            self.install_button.show()
            QMessageBox.warning(self, "环境检查", f"检测到以下依赖包缺失或版本不符，请点击'安装依赖'按钮进行安装：\n\n{', '.join(missing)}")

    def install_requirements(self):
        self.status_bar.showMessage("正在安装依赖，请稍候...")
        self.log_text.append("开始安装依赖包...")
        self.install_button.setEnabled(False)
        self.install_thread = InstallRequirementsThread()
        self.install_thread.finished.connect(self.on_install_finished)
        self.install_thread.start()

    def on_install_finished(self, success, message):
        if success:
            self.status_bar.showMessage("✅ 依赖安装成功！请重新检查环境。")
            self.log_text.append("✅ 依赖安装成功！")
            QMessageBox.information(self, "安装成功", "所有依赖已成功安装！\n\n请再次点击'检查环境'以确认。")
        else:
            self.status_bar.showMessage("❌ 依赖安装失败，请查看日志。")
            self.log_text.append(f"❌ 依赖安装失败: {message}")
            error_box = QMessageBox()
            error_box.setIcon(QMessageBox.Icon.Critical)
            error_box.setText("依赖安装失败！")
            error_box.setInformativeText("请检查您的网络连接和Python环境。详细错误信息如下：")
            error_box.setDetailedText(message)
            error_box.exec()
            
        self.install_button.setEnabled(True)
        
    def open_config_dialog(self):
        """打开配置对话框"""
        dialog = ConfigDialog(self)
        dialog.config_updated.connect(self.on_config_updated)
        dialog.exec()
        
    def on_config_updated(self):
        """配置更新后的回调"""
        self.log_text.append("✅ 配置已更新")
        self.status_bar.showMessage("配置已更新")
        
    def open_test_convert_dialog(self):
        """打开测试转链对话框"""
        dialog = TestConvertDialog(self)
        dialog.exec()
        
    def start_rss_service(self):
        """启动RSS监控服务"""
        try:
            # 导入服务控制模块
            import main
            
            # 在新线程中启动服务
            def start_service():
                main.start_scheduler()
                
            service_thread = threading.Thread(target=start_service, daemon=True)
            service_thread.start()
            
            self.service_running = True
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            
            self.log_text.append("🚀 RSS监控服务已启动")
            self.log_text.append("系统将自动监控RSS源并推送转链内容")
            self.log_text.append("支持淘宝、京东、拼多多返利转链")
            self.status_bar.showMessage("RSS监控服务运行中...")
            
        except Exception as e:
            self.log_text.append(f"❌ 启动服务失败: {str(e)}")
            QMessageBox.critical(self, "启动失败", f"无法启动RSS监控服务：\n{str(e)}")
            
    def stop_rss_service(self):
        """停止RSS监控服务"""
        try:
            # 导入服务控制模块
            import main
            
            main.stop_scheduler()
            
            self.service_running = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            
            self.log_text.append("⏹️ RSS监控服务已停止")
            self.status_bar.showMessage("RSS监控服务已停止")
            
        except Exception as e:
            self.log_text.append(f"❌ 停止服务失败: {str(e)}")
            QMessageBox.critical(self, "停止失败", f"无法停止RSS监控服务：\n{str(e)}")

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow { 
                background-color: #f5f5f5; 
            }
            QFrame { 
                background-color: #ffffff; 
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
            QLabel { 
                color: #333; 
                margin: 5px 0;
            }
            QPushButton {
                background-color: #0078d7; 
                color: white; 
                border-radius: 6px;
                padding: 8px 16px; 
                border: none;
                font-weight: bold;
            }
            QPushButton:hover { 
                background-color: #106ebe; 
            }
            QPushButton:pressed { 
                background-color: #005a9e; 
            }
            QPushButton:disabled { 
                background-color: #cccccc; 
                color: #666666;
            }
            QTextEdit {
                background-color: #fafafa;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
            }
            QStatusBar { 
                background-color: #0078d7; 
                color: white; 
                font-weight: bold;
            }
        """)

class TestConvertDialog(QDialog):
    """测试转链对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔗 测试返利转链功能")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("🧪 返利转链测试工具")
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 说明文字
        info_label = QLabel("输入商品链接，测试返利转链功能。支持淘宝、京东、拼多多等平台。")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("color: #666; margin: 10px 0;")
        layout.addWidget(info_label)
        
        # 输入区域
        input_group = QFrame()
        input_group.setFrameShape(QFrame.Shape.StyledPanel)
        input_layout = QVBoxLayout(input_group)
        
        input_label = QLabel("🔗 商品链接输入:")
        input_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        input_layout.addWidget(input_label)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("请输入商品链接，如: https://s.click.taobao.com/xxx")
        self.url_input.setMinimumHeight(35)
        input_layout.addWidget(self.url_input)
        
        # 预设链接按钮
        preset_layout = QHBoxLayout()
        
        self.preset_taobao_btn = QPushButton("📱 淘宝测试链接")
        self.preset_jd_btn = QPushButton("🛒 京东测试链接")
        self.preset_pdd_btn = QPushButton("🍑 拼多多测试链接")
        
        self.preset_taobao_btn.clicked.connect(lambda: self.set_preset_url("https://s.click.taobao.com/PvHy1Eq"))
        self.preset_jd_btn.clicked.connect(lambda: self.set_preset_url("https://u.jd.com/0rIPjug"))
        self.preset_pdd_btn.clicked.connect(lambda: self.set_preset_url("https://p.pinduoduo.com/lsYtFjyM?sc=EFAC"))
        
        preset_layout.addWidget(self.preset_taobao_btn)
        preset_layout.addWidget(self.preset_jd_btn)
        preset_layout.addWidget(self.preset_pdd_btn)
        
        input_layout.addLayout(preset_layout)
        layout.addWidget(input_group)
        
        # 转换按钮
        self.convert_btn = QPushButton("🚀 开始转链测试")
        self.convert_btn.setMinimumHeight(40)
        self.convert_btn.clicked.connect(self.test_convert)
        layout.addWidget(self.convert_btn)
        
        # 结果显示区域
        result_group = QFrame()
        result_group.setFrameShape(QFrame.Shape.StyledPanel)
        result_layout = QVBoxLayout(result_group)
        
        result_label = QLabel("📋 测试结果:")
        result_label.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
        result_layout.addWidget(result_label)
        
        self.result_text = QPlainTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFont(QFont("Consolas", 9))
        self.result_text.setPlaceholderText("转链测试结果将在这里显示...")
        result_layout.addWidget(self.result_text)
        
        layout.addWidget(result_group)
        
        # 关闭按钮
        close_btn = QPushButton("❌ 关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        self.apply_dialog_stylesheet()
        
    def set_preset_url(self, url):
        """设置预设URL"""
        self.url_input.setText(url)
        
    def load_config(self):
        """加载配置"""
        try:
            import json
            with open('config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        except Exception as e:
            self.result_text.appendPlainText(f"❌ 配置加载失败: {str(e)}")
            self.config = {}
            
    def test_convert(self):
        """执行转链测试"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "警告", "请输入要测试的商品链接")
            return
            
        self.result_text.clear()
        self.result_text.appendPlainText("🚀 开始转链测试...")
        self.result_text.appendPlainText(f"原始链接: {url}")
        self.result_text.appendPlainText("=" * 50)
        
        try:
            # 导入转链模块
            import sys
            import os
            sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
            
            from src.core.affiliate_converter import AffiliateConverter
            
            # 创建转换器 - 传递完整配置
            converter = AffiliateConverter(self.config)
            
            # 测试URL提取
            self.result_text.appendPlainText("🔍 URL识别测试:")
            extracted_urls = converter._extract_urls(f"测试商品: {url}")
            self.result_text.appendPlainText(f"  识别到的URL数量: {len(extracted_urls)}")
            for i, extracted_url in enumerate(extracted_urls):
                self.result_text.appendPlainText(f"  URL {i+1}: {extracted_url}")
            
            # 测试单链接转换
            self.result_text.appendPlainText(f"\n🔄 单链接转换测试:")
            converted_url = converter._convert_single_link(url)
            self.result_text.appendPlainText(f"  转换结果: {converted_url}")
            
            if converted_url != url:
                self.result_text.appendPlainText("  ✅ 转换成功！链接已发生变化")
            else:
                self.result_text.appendPlainText("  ⚠️ 转换未生效，链接未发生变化")
            
            # 测试批量转换
            self.result_text.appendPlainText(f"\n📝 批量转换测试:")
            test_text = f"推荐商品：{url} 快来抢购！"
            batch_result = converter.convert_links(test_text)
            self.result_text.appendPlainText(f"  原始文本: {test_text}")
            self.result_text.appendPlainText(f"  转换结果: {batch_result}")
            
            # 识别平台（使用现有的平台识别方法）
            self.result_text.appendPlainText(f"\n🏪 平台识别:")
            platform = converter._detect_platform(url)
            
            if platform == "taobao":
                self.result_text.appendPlainText(f"  平台: 淘宝/天猫")
            elif platform == "jd":
                self.result_text.appendPlainText(f"  平台: 京东")
            elif platform == "pdd":
                platform_name = "拼多多"
                # 只对拼多多使用现有的商品ID提取方法
                goods_id = converter._extract_pdd_goods_id(url)
                self.result_text.appendPlainText(f"  平台: {platform_name}")
                self.result_text.appendPlainText(f"  提取的商品ID: {goods_id if goods_id else '无法提取'}")
            else:
                self.result_text.appendPlainText(f"  平台: 未知平台")
            
            self.result_text.appendPlainText("\n" + "=" * 50)
            self.result_text.appendPlainText("🎉 测试完成！")
            
        except Exception as e:
            self.result_text.appendPlainText(f"\n❌ 测试过程中发生错误:")
            self.result_text.appendPlainText(f"错误信息: {str(e)}")
            import traceback
            self.result_text.appendPlainText(f"详细堆栈:\n{traceback.format_exc()}")
            
    def apply_dialog_stylesheet(self):
        """应用对话框样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QFrame {
                background-color: #ffffff;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
                padding: 10px;
            }
            QLabel {
                color: #333;
                margin: 5px 0;
            }
            QLineEdit {
                padding: 8px 12px;
                border: 2px solid #ddd;
                border-radius: 6px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #0078d7;
            }
            QPushButton {
                background-color: #0078d7;
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                border: none;
                font-weight: bold;
                margin: 2px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
            QPlainTextEdit {
                background-color: #fafafa;
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
            }
        """)

def main():
    app = QApplication(sys.argv)
    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()