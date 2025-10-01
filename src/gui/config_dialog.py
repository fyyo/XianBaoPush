
# src/gui/config_dialog.py - 配置对话框
import sys
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, 
                             QWidget, QLabel, QLineEdit, QPushButton, QTableWidget, 
                             QTableWidgetItem, QMessageBox, QGroupBox, QCheckBox,
                             QFormLayout, QHeaderView, QSpacerItem, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from ..core.config_manager import (load_config, save_config, load_rss_configs, 
                                   save_rss_configs, load_affiliate_config, 
                                   save_affiliate_config, get_default_affiliate_config)

class ConfigDialog(QDialog):
    """配置对话框"""
    
    config_updated = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("智能RSS线报推送系统 - 配置管理")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
        self.load_all_configs()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        
        # RSS配置标签页
        self.rss_tab = QWidget()
        self.setup_rss_tab()
        self.tab_widget.addTab(self.rss_tab, "📡 RSS订阅配置")
        
        # 返利配置标签页
        self.affiliate_tab = QWidget()
        self.setup_affiliate_tab()
        self.tab_widget.addTab(self.affiliate_tab, "💰 返利转链配置")
        
        layout.addWidget(self.tab_widget)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
    def setup_rss_tab(self):
        """设置RSS配置标签页"""
        layout = QVBoxLayout(self.rss_tab)
        
        # 添加RSS配置区域
        add_group = QGroupBox("添加新的RSS订阅")
        add_layout = QFormLayout(add_group)
        
        self.rss_url_input = QLineEdit()
        self.rss_url_input.setPlaceholderText("请输入RSS源地址")
        add_layout.addRow("RSS地址:", self.rss_url_input)
        
        self.interval_input = QLineEdit("60")
        self.interval_input.setPlaceholderText("推送间隔（秒）")
        add_layout.addRow("推送间隔:", self.interval_input)
        
        self.group_id_input = QLineEdit()
        self.group_id_input.setPlaceholderText("请输入QQ群号")
        add_layout.addRow("QQ群号:", self.group_id_input)
        
        self.api_url_input = QLineEdit("http://localhost:3000")
        self.api_url_input.setPlaceholderText("LLOneBot API地址")
        add_layout.addRow("API地址:", self.api_url_input)
        
        self.add_button = QPushButton("添加订阅")
        self.add_button.clicked.connect(self.add_rss_config)
        add_layout.addRow(self.add_button)
        
        layout.addWidget(add_group)
        
        # RSS配置列表
        list_group = QGroupBox("当前RSS订阅列表")
        list_layout = QVBoxLayout(list_group)
        
        self.rss_table = QTableWidget()
        self.rss_table.setColumnCount(5)
        self.rss_table.setHorizontalHeaderLabels(["RSS地址", "推送间隔", "QQ群号", "API地址", "操作"])
        
        # 设置表格列宽
        header = self.rss_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        self.rss_table.setColumnWidth(1, 80)
        self.rss_table.setColumnWidth(2, 100)
        self.rss_table.setColumnWidth(3, 150)
        self.rss_table.setColumnWidth(4, 80)
        
        list_layout.addWidget(self.rss_table)
        layout.addWidget(list_group)
        
    def setup_affiliate_tab(self):
        """设置返利配置标签页"""
        layout = QVBoxLayout(self.affiliate_tab)
        
        # 大淘客配置
        dataoke_group = QGroupBox("大淘客配置（淘宝返利）")
        dataoke_layout = QFormLayout(dataoke_group)
        
        self.dataoke_enabled = QCheckBox("启用大淘客转链")
        dataoke_layout.addRow(self.dataoke_enabled)
        
        self.dataoke_app_key = QLineEdit()
        self.dataoke_app_key.setPlaceholderText("请输入大淘客App Key")
        dataoke_layout.addRow("App Key:", self.dataoke_app_key)
        
        self.dataoke_app_secret = QLineEdit()
        self.dataoke_app_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self.dataoke_app_secret.setPlaceholderText("请输入大淘客App Secret")
        dataoke_layout.addRow("App Secret:", self.dataoke_app_secret)
        
        layout.addWidget(dataoke_group)
        
        # 京品库配置
        jingpinku_group = QGroupBox("京品库配置（京东返利）")
        jingpinku_layout = QFormLayout(jingpinku_group)
        
        self.jingpinku_enabled = QCheckBox("启用京品库转链")
        jingpinku_layout.addRow(self.jingpinku_enabled)
        
        self.jingpinku_appid = QLineEdit()
        self.jingpinku_appid.setPlaceholderText("请输入京品库App ID")
        jingpinku_layout.addRow("App ID:", self.jingpinku_appid)

        self.jingpinku_appkey = QLineEdit()
        self.jingpinku_appkey.setEchoMode(QLineEdit.EchoMode.Password)
        self.jingpinku_appkey.setPlaceholderText("请输入京品库App Key")
        jingpinku_layout.addRow("App Key:", self.jingpinku_appkey)

        self.jingpinku_union_id = QLineEdit()
        self.jingpinku_union_id.setPlaceholderText("请输入联盟ID")
        jingpinku_layout.addRow("Union ID:", self.jingpinku_union_id)
        
        layout.addWidget(jingpinku_group)
        
        # 拼多多配置
        pdd_group = QGroupBox("多多进宝配置（拼多多返利）")
        pdd_layout = QFormLayout(pdd_group)
        
        self.pdd_enabled = QCheckBox("启用多多进宝转链")
        pdd_layout.addRow(self.pdd_enabled)
        
        self.pdd_client_id = QLineEdit()
        self.pdd_client_id.setPlaceholderText("请输入拼多多Client ID")
        pdd_layout.addRow("Client ID:", self.pdd_client_id)
        
        self.pdd_client_secret = QLineEdit()
        self.pdd_client_secret.setEchoMode(QLineEdit.EchoMode.Password)
        self.pdd_client_secret.setPlaceholderText("请输入拼多多Client Secret")
        pdd_layout.addRow("Client Secret:", self.pdd_client_secret)
        
        self.pdd_pid = QLineEdit()
        self.pdd_pid.setPlaceholderText("请输入推广位ID")
        pdd_layout.addRow("PID:", self.pdd_pid)
        
        layout.addWidget(pdd_group)
        
        # 批量设置配置
        batch_group = QGroupBox("批量转链设置")
        batch_layout = QFormLayout(batch_group)
        
        self.convert_enabled = QCheckBox("启用批量转链功能")
        batch_layout.addRow(self.convert_enabled)
        
        self.max_convert_input = QLineEdit("5")
        self.max_convert_input.setPlaceholderText("每批最多转链数量")
        batch_layout.addRow("每批转链数量:", self.max_convert_input)
        
        layout.addWidget(batch_group)
        
        # 保存按钮
        button_layout = QHBoxLayout()
        self.save_affiliate_button = QPushButton("保存返利配置")
        self.save_affiliate_button.clicked.connect(self.save_affiliate_config)
        button_layout.addWidget(self.save_affiliate_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # 添加弹簧
        layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
    def load_all_configs(self):
        """加载所有配置"""
        self.load_rss_configs()
        self.load_affiliate_configs()
        
    def load_rss_configs(self):
        """加载RSS配置"""
        configs = load_rss_configs()
        self.rss_table.setRowCount(len(configs))
        
        for row, config in enumerate(configs):
            self.rss_table.setItem(row, 0, QTableWidgetItem(config.get('rss_url', '')))
            self.rss_table.setItem(row, 1, QTableWidgetItem(str(config.get('interval', ''))))
            self.rss_table.setItem(row, 2, QTableWidgetItem(config.get('group_id', '')))
            self.rss_table.setItem(row, 3, QTableWidgetItem(config.get('llonebot_api_url', '')))
            
            # 删除按钮
            delete_button = QPushButton("删除")
            delete_button.clicked.connect(lambda checked, r=row: self.delete_rss_config(r))
            self.rss_table.setCellWidget(row, 4, delete_button)
            
    def load_affiliate_configs(self):
        """加载返利配置"""
        config = load_affiliate_config()
        if not config:
            config = get_default_affiliate_config()
            
        # 大淘客配置
        dataoke_config = config.get('dataoke', {})
        self.dataoke_enabled.setChecked(dataoke_config.get('enabled', False))
        self.dataoke_app_key.setText(dataoke_config.get('app_key', ''))
        self.dataoke_app_secret.setText(dataoke_config.get('app_secret', ''))
        
        # 京品库配置
        jingpinku_config = config.get('jingpinku', {})
        self.jingpinku_enabled.setChecked(jingpinku_config.get('enabled', False))
        self.jingpinku_appid.setText(jingpinku_config.get('appid', ''))
        self.jingpinku_appkey.setText(jingpinku_config.get('appkey', ''))
        self.jingpinku_union_id.setText(jingpinku_config.get('union_id', ''))
        
        # 拼多多配置
        pdd_config = config.get('pdd', {})
        self.pdd_enabled.setChecked(pdd_config.get('enabled', False))
        self.pdd_client_id.setText(pdd_config.get('client_id', ''))
        self.pdd_client_secret.setText(pdd_config.get('client_secret', ''))
        self.pdd_pid.setText(pdd_config.get('pid', ''))
        
        # 批量设置配置
        batch_config = config.get('batch_settings', {})
        self.convert_enabled.setChecked(batch_config.get('convert_enabled', True))
        self.max_convert_input.setText(str(batch_config.get('max_convert_per_batch', 5)))
        
    def add_rss_config(self):
        """添加RSS配置"""
        rss_url = self.rss_url_input.text().strip()
        interval = self.interval_input.text().strip()
        group_id = self.group_id_input.text().strip()
        api_url = self.api_url_input.text().strip()
        
        if not all([rss_url, interval, group_id, api_url]):
            QMessageBox.warning(self, "警告", "请填写所有必需字段！")
            return
            
        try:
            interval = int(interval)
            if interval <= 0:
                raise ValueError("间隔必须大于0")
        except ValueError:
            QMessageBox.warning(self, "警告", "推送间隔必须是正整数！")
            return
            
        # 保存配置
        configs = load_rss_configs()
        new_config = {
            'rss_url': rss_url,
            'interval': interval,
            'group_id': group_id,
            'llonebot_api_url': api_url
        }
        
        # 检查是否已存在
        existing_config = next((c for c in configs if c["rss_url"] == rss_url), None)
        if existing_config:
            existing_config.update(new_config)
        else:
            configs.append(new_config)
            
        save_rss_configs(configs)
        
        # 清空输入框
        self.rss_url_input.clear()
        self.interval_input.setText("60")
        self.group_id_input.clear()
        self.api_url_input.setText("http://localhost:3000")
        
        # 重新加载表格
        self.load_rss_configs()
        self.config_updated.emit()
        
        QMessageBox.information(self, "成功", "RSS配置保存成功！")
        
    def delete_rss_config(self, row):
        """删除RSS配置"""
        if row >= self.rss_table.rowCount():
            return
            
        rss_url_item = self.rss_table.item(row, 0)
        if not rss_url_item:
            return
            
        rss_url = rss_url_item.text()
        
        reply = QMessageBox.question(self, "确认删除",
                                   f"确定要删除订阅源：\n{rss_url}\n吗？",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            configs = load_rss_configs()
            configs = [c for c in configs if c["rss_url"] != rss_url]
            save_rss_configs(configs)
            
            self.load_rss_configs()
            self.config_updated.emit()
            
            QMessageBox.information(self, "成功", "订阅源删除成功！")
        
    def save_affiliate_config(self):
        """保存返利配置"""
        try:
            max_convert = int(self.max_convert_input.text().strip())
            if max_convert <= 0:
                raise ValueError("转链数量必须大于0")
        except ValueError:
            QMessageBox.warning(self, "警告", "每批转链数量必须是正整数！")
            return
            
        config = {
            'dataoke': {
                'enabled': self.dataoke_enabled.isChecked(),
                'app_key': self.dataoke_app_key.text().strip(),
                'app_secret': self.dataoke_app_secret.text().strip()
            },
            'jingpinku': {
                'enabled': self.jingpinku_enabled.isChecked(),
                'appid': self.jingpinku_appid.text().strip(),
                'appkey': self.jingpinku_appkey.text().strip(),
                'union_id': self.jingpinku_union_id.text().strip()
            },
            'pdd': {
                'enabled': self.pdd_enabled.isChecked(),
                'client_id': self.pdd_client_id.text().strip(),
                'client_secret': self.pdd_client_secret.text().strip(),
                'pid': self.pdd_pid.text().strip()
            },
            'batch_settings': {
                'convert_enabled': self.convert_enabled.isChecked(),
                'max_convert_per_batch': max_convert
            }
        }
        
        save_affiliate_config(config)
        self.config_updated.emit()
        QMessageBox.information(self, "成功", "返利配置保存成功！")