# EMS3 - 简单高效的Minecraft服务器管理面板

EMS3（Easy Minecraft Server Management System 3）是一个用Python编写的轻量级Minecraft服务器管理面板。它提供了直观的Web界面，让您可以轻松管理多个Minecraft服务器。

🌐 [在线演示](https://easily-miku.github.io/EMS3/index.html)

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
- ⏰ 定时任务系统
- 💾 自动备份功能

## 系统要求

- Python 3.7+
- Java（用于运行Minecraft服务器）
- 现代浏览器（Chrome、Firefox、Edge等）

## 快速安装

### Linux系统（推荐）

使用一键安装脚本（支持Ubuntu/Debian/CentOS）：

```bash
wget -O install.sh https://raw.githubusercontent.com/Easily-miku/EMS3/main/install.sh
chmod +x install.sh
./install.sh
```

安装完成后，可以使用以下命令管理EMS3：

```bash
# 启动服务
sudo emcsl 1

# 停止服务
sudo emcsl 2

# 重启服务
sudo emcsl 3

# 查看状态
sudo emcsl 4

# 查看日志
sudo emcsl 5

# 查看系统资源
sudo emcsl 6

# 查看帮助信息
emcsl --help
```

### Windows系统

1. 克隆仓库：
```bash
git clone https://github.com/Easily-miku/EMS3.git
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

## 功能特性

### 服务器管理
- 创建和管理多个服务器实例
- 实时监控服务器状态
- CPU和内存使用监控
- 在线玩家列表

### 文件管理
- 在线文件编辑器
- 文件上传/下载
- 目录浏览和管理
- 权限管理

### 控制台功能
- 实时日志显示
- 命令执行和历史记录
- 快捷命令支持
- 自定义命令模板

### 定时任务
- Cron表达式支持
- 定时执行命令
- 定时重启服务器
- 任务管理界面

### 备份系统
- 手动/自动备份
- 备份文件管理
- 一键恢复功能
- 定时备份计划

### 系统监控
- CPU使用率监控
- 内存使用监控
- 磁盘空间监控
- 系统负载监控

## 命令行工具

Linux系统提供`emcsl`命令行工具：

```bash
使用方法: emcsl <命令编号>

可用命令:
1  - 启动EMS3服务
2  - 停止EMS3服务
3  - 重启EMS3服务
4  - 查看EMS3服务状态
5  - 查看EMS3日志
6  - 查看系统资源使用情况
7  - 检查Java版本
8  - 检查Python版本
9  - 更新EMS3
0  - 显示帮助信息
```

## 安全建议

1. 修改默认端口
2. 设置防火墙规则
3. 使用反向代理（如Nginx）
4. 定期备份服务器文件
5. 启用HTTPS
6. 设置强密码

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

### v3.1.0
- 全新的Web界面
- 定时任务
- 玩家数量显示
- 自动备份功能

- 
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

本项目采用GNU3.0许可证。详见 [LICENSE](LICENSE) 文件。

## 相关链接

- 🌐 [在线演示](https://easily-miku.github.io/EMS3/index.html)
- 📦 [项目主页](https://github.com/Easily-miku/EMS3)
- 🐛 [问题反馈](https://github.com/Easily-miku/EMS3/issues)

## 致谢

感谢所有为本项目做出贡献的开发者。
