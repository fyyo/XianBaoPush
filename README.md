# 智能RSS线报推送系统 XianBaoPush

一个智能RSS线报推送系统，能够自动抓取RSS源内容，进行智能转链处理，并推送到QQ群。系统支持多平台返利转链（淘宝、京东、拼多多）。

## ✨ 主要特性

### 🎯 智能返利转链
- **淘宝/天猫返利**: 集成大淘客API，自动转换淘宝商品链接
- **京东返利**: 集成京品库API，自动转换京东商品链接  
- **拼多多返利**: 集成多多进宝API，自动转换拼多多商品链接
- **智能链接识别**: 自动识别文本中的商品链接并进行转换
- **容错机制**: 转链失败时不影响系统运行，保持原始内容推送

### 📡 RSS订阅管理
- 支持多RSS源同时监控
- 可配置推送间隔和目标QQ群
- 智能文本清理和格式化
- 时间分界点机制，避免重复推送
- 统一状态管理

### 🖥️ 现代化GUI界面
- 基于PyQt6的现代化桌面应用
- 直观的配置管理界面
- 实时日志显示
- 环境检查和依赖自动安装

## 🚀 快速开始

### 方法一：使用EXE程序 (推荐)

这是最简单快捷的方式，无需安装Python环境。

1.  **下载程序**:
    前往 [GitHub Releases](https://github.com/fyyo/XianBaoPush/releases) 页面，下载最新的 `XianBaoPush.exe` 文件。

2.  **启动程序**:
    双击运行 `XianBaoPush.exe`。

3.  **进行配置**:
    程序启动后，会自动创建 `config.json` 文件。点击界面上的 **“打开配置”** 按钮，在图形化界面中填入您的API密钥、RSS源和QQ配置信息。

4.  **启动服务**:
    配置完成后，点击 **“启动服务”** 按钮，系统即开始运行。

### 方法二：通过源码运行

如果您希望进行二次开发或自定义，可以选择通过源码运行。

#### 环境要求
- Python 3.8+
- Windows 10/11

#### 安装步骤

1.  **克隆项目**:
    ```bash
    git clone https://github.com/fyyo/XianBaoPush.git
    cd XianBaoPush
    ```

2.  **安装依赖**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置系统**:
    启动程序后，点击 **“打开配置”** 按钮在图形化界面中完成配置。您也可以手动复制 `config.example.json` 为 `config.json` 并进行编辑。

4.  **启动应用**:
    ```bash
    # 启动GUI界面
    python main.py

    # 或在后台静默运行
    python run.pyw
    ```

## 📋 配置说明

### 配置方式

推荐通过程序的图形化界面进行配置。点击主界面的 **“打开配置”** 按钮，即可在弹出的窗口中方便地修改所有设置项。

所有配置将自动保存在程序目录下的 `config.json` 文件中。

### 返利API配置

#### 大淘客 (淘宝/天猫)
- 注册地址: https://www.dataoke.com/
- 获取App Key和App Secret
- 在配置文件中启用并填入密钥

#### 京品库 (京东)  
- 注册地址: https://www.jingpinku.com/
- 获取App Key、App Secret和Union ID
- 在配置文件中启用并填入密钥

#### 多多进宝 (拼多多)
- 注册地址: https://jinbao.pinduoduo.com/
- 获取Client ID、Client Secret和PID
- 在配置文件中启用并填入密钥

### QQ推送配置 (LLOneBot)

本系统通过 [LLOneBot](https://github.com/LLOneBot/LLOneBot) 实现QQ群消息推送。您必须先在您的QQ客户端（Windows版QQ桌面端）上正确安装和配置LLOneBot。

#### LLOneBot 安装与启动步骤

1.  **访问 LLOneBot 仓库**:
    前往 [LLOneBot GitHub Releases](https://github.com/LLOneBot/LLOneBot/releases) 页面，下载最新的 **`LLOneBot-vX.X.X.ffmpeg.zip** 可执行文件。

2.  **启动服务**:
    *   下载后，解压zip，QQ先不要启动，直接双击运行 `LLOneBot-vX.X.X.exe` 文件。
    *   解压后双击 llonebot.exe 会启动 QQ，登录后会在 llonebot.exe 所在目录生成一个 data 文件夹
    *   注意在登录的时候不能勾选多个账号，LLOneBot 不支持这种登录方式
    *   浏览器打开 http://localhost:3000 进行配置

4.  **配置本系统**:
    *   **`llonebot_api_url`**: 填入您在上一步中获取的LLOneBot的HTTP服务地址。如果在本机运行，通常是 `http://localhost:3000 `。
    *   **`group_id`**: 填入要推送消息的目标QQ群号。请确保您的机器人QQ号已经加入该群，并拥有发言权限。

### RSS订阅配置

在 `rss_sources` 列表中，您可以配置一个或多个RSS源。

- **`rss_url`**: 要监控的RSS源的URL。
- **`interval`**: 检查该RSS源更新的时间间隔（单位：分钟）。

### 示例配置
```json
{
  "rss_sources": [
    {
      "rss_url": "https://example.com/rss.xml",
      "interval": 5,
      "group_id": "YOUR_QQ_GROUP_ID",
      "llonebot_api_url": "http://127.0.0.1:3000"
    }
  ],
  "affiliate_config": {
    "dataoke": {
      "enabled": true,
      "app_key": "YOUR_DATAOKE_APP_KEY",
      "app_secret": "YOUR_DATAOKE_APP_SECRET"
    }
  }
}
```

## 🎮 使用方法

### GUI模式
1. 运行 `python main.py` 启动图形界面
2. 点击"检查环境"确保依赖正确安装
3. 点击"打开配置"进行API和RSS配置
4. 点击"启动服务"开始自动监控

### 命令行模式
运行 `python run.pyw` 可在后台静默运行

## 🔧 技术架构

### 核心模块
- **src/core/affiliate_converter.py**: 返利转链核心引擎
- **src/core/rss_fetcher.py**: RSS内容抓取器
- **src/core/qq_pusher.py**: QQ群消息推送器
- **src/core/config_manager.py**: 配置管理器

### GUI界面
- **src/gui/main_window.py**: 主窗口界面
- **src/gui/config_dialog.py**: 配置对话框

### 工具模块
- **src/utils/text_cleaner.py**: 文本清理工具

## 🛡️ 安全特性

- 配置信息本地存储，不上传到GitHub
- API调用签名验证
- 完善的错误处理和重试机制
- 详细的日志记录和监控
- 转链失败时的容错保护

## 📊 支持的链接类型

### 淘宝/天猫
- `item.taobao.com`
- `detail.tmall.com`
- `s.click.taobao.com`

### 京东
- `item.jd.com`
- `item.m.jd.com`
- `u.jd.com`

### 拼多多
- `mobile.yangkeduo.com`
- `p.pinduoduo.com`

## 🔄 更新日志

### v4.0 (当前版本)
- ✅ 完全重构为桌面GUI应用
- ✅ 智能返利转链功能
- ✅ 支持三大电商平台返利
- ✅ 修复时间处理和显示问题
- ✅ 优化文本清理机制
- ✅ 改进错误处理和容错机制
- ✅ 统一状态文件管理

## 🤝 贡献指南

欢迎提交Issue和Pull Request来改进项目！

### 开发环境搭建
1. Fork本项目
2. 克隆到本地
3. 安装依赖：`pip install -r requirements.txt`
4. 创建配置文件：`cp config.example.json config.json`
5. 进行开发和测试

### 提交规范
- 提交前请确保代码通过基本测试
- 提交信息请使用中文，格式清晰
- 大的功能改动请先创建Issue讨论

## 📄 许可证

本项目采用MIT许可证，详见[LICENSE](LICENSE)文件。

## 🆘 常见问题

### Q: 首次启动如何配置？
A: 复制 `config.example.json` 为 `config.json`，然后编辑填入您的API密钥和RSS源。

### Q: GUI界面无法显示？
A: 请确保已正确安装PyQt6依赖，运行 `pip install PyQt6`。

### Q: 返利转链不生效？
A: 请检查API密钥配置是否正确，确保账户有足够权限和余额。

### Q: QQ群推送失败？
A: 请按以下步骤排查：
1. **检查LLOneBot服务**: 确保LLOneBot已在您的QQ客户端上成功安装并正在运行。
2. **确认API地址**: 检查 `config.json` 中的 `llonebot_api_url` 是否与您LLOneBot设置的HTTP服务地址和端口完全一致。
3. **检查网络**: 确认本程序可以访问到LLOneBot的API地址（如在本机运行，通常是 `http://localhost:3000 `）。
4. **检查群号和机器人状态**: 确认 `group_id` 配置正确，并且机器人（QQ号）已经成功加入该群。
5. **查看日志**: 检查 `logs/rss_qq_app.log` 文件，查看是否有与QQ推送相关的详细错误信息。

### Q: 系统会重复推送相同线报吗？
A: 不会，系统使用时间分界点机制和状态文件管理，确保不重复推送。

### Q: 转链失败会影响系统运行吗？
A: 不会，系统具有完善的容错机制，转链失败时会保持原内容继续推送。

## 📞 技术支持

如果您在使用过程中遇到问题，可以：
1. 查看项目Wiki文档
2. 提交GitHub Issue
3. 查看系统日志文件 `logs/rss_qq_app.log`

---

**智能RSS线报推送系统 - 让线报推送更智能，让返利更简单！** 🎉

[![GitHub stars](https://img.shields.io/github/stars/fyyo/XianBaoPush.svg)](https://github.com/fyyo/XianBaoPush/stargazers)
[![GitHub issues](https://img.shields.io/github/issues/fyyo/XianBaoPush.svg)](https://github.com/fyyo/XianBaoPush/issues)
[![GitHub license](https://img.shields.io/github/license/fyyo/XianBaoPush.svg)](https://github.com/fyyo/XianBaoPush/blob/main/LICENSE)