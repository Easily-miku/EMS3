# EMS3 - 简单高效的Minecraft服务器管理面板

EMS3（Easy Minecraft Server Management System 3）是一个用Python编写的轻量级Minecraft服务器管理面板。它提供了直观的Web界面，让您可以轻松管理多个Minecraft服务器。

## 特性

- 🚀 轻量级且高效
- 💻 美观的Web界面
- 🔄 实时状态监控
- 📁 文件管理系统
- 🎮 服务器控制台
- ⚡ 快捷命令系统
- 🌙 暗黑模式支持
- 🔧 多Java版本管理
- 📊 资源使用监控
- 🔌 插件和模组支持

## 系统要求

- Python 3.7+
- Java（用于运行Minecraft服务器）
- 现代浏览器（Chrome、Firefox、Edge等）

## 快速安装

### Linux系统（推荐）

使用一键安装脚本（支持Ubuntu/Debian/CentOS）：

```bash
wget -O install.sh https://raw.githubusercontent.com/yourusername/EMS3/main/install.sh
chmod +x install.sh
./install.sh
```

安装脚本会自动：
- 检查并安装所需依赖（Python、Java、Git等）
- 下载并初始化EMS3
- 创建系统服务
- 启动EMS3服务

### Windows系统

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/EMS3.git
cd EMS3
```

2. 运行初始化脚本：
```bash
python init.py
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 启动面板：
```bash
python app.py
```

5. 访问面板：
打开浏览器访问 `http://localhost:5000`

## 配置说明

### 配置文件

配置文件位于 `config/config.json`，包含以下主要设置：

- `web_port`: Web面板端口号
- `java_paths`: Java路径配置
- `quick_commands`: 快捷命令配置
- `servers`: 服务器配置

### Java配置

支持多个Java版本，可以在面板设置中添加：
- 自动检测系统默认Java
- 手动添加Java路径
- 为每个服务器单独配置Java版本

### 快捷命令

预设的快捷命令包括：
- op：设置管理员
- gamemode：更改游戏模式
- time：设置时间
- weather：设置天气

可以在面板中添加自定义快捷命令。

## 使用说明

### 创建服务器

1. 点击右侧工具栏的"创建服务器"
2. 填写服务器名称和端口
3. 选择Java版本和内存设置
4. 点击创建

### 服务器管理

- **概览**：查看服务器状态、CPU和内存使用情况
- **文件管理**：管理服务器文件、编辑配置
- **控制台**：查看日志、执行命令
- **设置**：修改服务器配置

### 文件管理

- 支持在线编辑配置文件
- 上传/下载文件
- 创建/删除文件和文件夹

### 控制台功能

- 实时日志显示
- 命令执行
- 命令历史记录
- 快捷命令支持

## 安全建议

1. 修改默认端口
2. 设置防火墙规则
3. 使用反向代理（如Nginx）
4. 定期备份服务器文件

## 常见问题

1. **无法启动服务器**
   - 检查Java路径配置
   - 确认端口未被占用
   - 查看日志获取详细错误信息

2. **CPU使用率显示异常**
   - 已优化多核CPU显示
   - 显示为单核平均使用率

3. **内存使用显示**
   - 显示实际物理内存使用
   - 单位为MB

## 更新日志

### v3.0.0
- 全新的Web界面
- 多Java版本支持
- 实时资源监控
- 文件管理系统优化
- 暗黑模式支持

## 贡献指南

欢迎提交Pull Request和Issue。在提交之前，请：

1. 确保代码符合PEP 8规范
2. 添加必要的注释
3. 更新相关文档

## 许可证

本项目采用MIT许可证。详见 [LICENSE](LICENSE) 文件。

## 联系方式

- 项目主页：[GitHub](https://github.com/yourusername/EMS3)
- 问题反馈：[Issues](https://github.com/yourusername/EMS3/issues)

## 致谢

感谢所有为本项目做出贡献的开发者。
