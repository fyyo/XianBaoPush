# src/core/config_manager.py - 统一配置管理器
import json
import os

CONFIG_FILE = 'config.json'

def load_config():
    """加载完整配置"""
    if not os.path.exists(CONFIG_FILE):
        # 创建默认配置
        default_config = {
            "rss_sources": [],
            "affiliate_config": get_default_affiliate_config()
        }
        save_config(default_config)
        return default_config
        
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # 确保配置结构完整
        if 'rss_sources' not in config:
            config['rss_sources'] = []
        if 'affiliate_config' not in config:
            config['affiliate_config'] = get_default_affiliate_config()
            
        return config
    except (FileNotFoundError, json.JSONDecodeError):
        # 如果文件损坏，返回默认配置
        default_config = {
            "rss_sources": [],
            "affiliate_config": get_default_affiliate_config()
        }
        save_config(default_config)
        return default_config

def save_config(config):
    """保存完整配置"""
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存配置失败: {e}")

def load_rss_configs():
    """加载RSS配置列表（兼容旧接口）"""
    config = load_config()
    return config.get('rss_sources', [])

def save_rss_configs(rss_configs):
    """保存RSS配置列表（兼容旧接口）"""
    config = load_config()
    config['rss_sources'] = rss_configs
    save_config(config)

def load_affiliate_config():
    """加载返利配置（兼容旧接口）"""
    config = load_config()
    return config.get('affiliate_config', get_default_affiliate_config())

def save_affiliate_config(affiliate_config):
    """保存返利配置（兼容旧接口）"""
    config = load_config()
    config['affiliate_config'] = affiliate_config
    save_config(config)

def get_default_affiliate_config():
    """获取默认返利配置"""
    return {
        'dataoke': {
            'enabled': False,
            'app_key': '',
            'app_secret': ''
        },
        'jingpinku': {
            'enabled': False,
            'app_key': '',
            'app_secret': '',
            'union_id': ''
        },
        'pdd': {
            'enabled': False,
            'client_id': '',
            'client_secret': '',
            'pid': ''
        },
        'batch_settings': {
            'convert_enabled': True,
            'max_convert_per_batch': 5
        }
    }
