#!/bin/bash

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 打印带颜色的信息
print_info() {
    echo -e "${GREEN}[信息]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[警告]${NC} $1"
}

print_error() {
    echo -e "${RED}[错误]${NC} $1"
}

# 检查系统类型
check_system() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
    else
        print_error "无法确定操作系统类型"
        exit 1
    fi
}

# 检查并安装依赖
install_dependencies() {
    print_info "检查并安装必要的依赖..."
    
    case $OS in
        "Ubuntu" | "Debian GNU/Linux")
            sudo apt-get update
            sudo apt-get install -y python3 python3-pip openjdk-17-jdk git curl wget
            ;;
        "CentOS Linux" | "Red Hat Enterprise Linux")
            sudo yum -y update
            sudo yum -y install python3 python3-pip java-17-openjdk-devel git curl wget
            ;;
        *)
            print_error "不支持的操作系统: $OS"
            exit 1
            ;;
    esac
}

# 检查Python版本
check_python() {
    print_info "检查Python版本..."
    if ! command -v python3 &> /dev/null; then
        print_error "Python3未安装"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if (( $(echo "$PYTHON_VERSION < 3.7" | bc -l) )); then
        print_error "Python版本必须大于等于3.7，当前版本: $PYTHON_VERSION"
        exit 1
    fi
    print_info "Python版本检查通过: $PYTHON_VERSION"
}

# 检查Java版本
check_java() {
    print_info "检查Java版本..."
    if ! command -v java &> /dev/null; then
        print_error "Java未安装"
        exit 1
    fi
    
    JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2)
    print_info "Java版本检查通过: $JAVA_VERSION"
}

# 下载EMS3
download_ems3() {
    print_info "下载EMS3..."
    if [ -d "EMS3" ]; then
        print_warning "EMS3目录已存在，正在更新..."
        cd EMS3
        git pull
    else
        git clone https://github.com/yourusername/EMS3.git
        cd EMS3
    fi
}

# 初始化EMS3
init_ems3() {
    print_info "初始化EMS3..."
    python3 init.py
    
    if [ $? -ne 0 ]; then
        print_error "初始化失败"
        exit 1
    fi
}

# 安装Python依赖
install_requirements() {
    print_info "安装Python依赖..."
    python3 -m pip install -r requirements.txt
    
    if [ $? -ne 0 ]; then
        print_error "依赖安装失败"
        exit 1
    fi
}

# 创建启动脚本
create_service() {
    print_info "创建系统服务..."
    
    sudo tee /etc/systemd/system/ems3.service > /dev/null << EOL
[Unit]
Description=EMS3 Minecraft Server Manager
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=/usr/bin/python3 app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOL

    sudo systemctl daemon-reload
    sudo systemctl enable ems3
    sudo systemctl start ems3
    
    print_info "EMS3服务已创建并启动"
}

# 获取用户输入的用户名和密码
get_credentials() {
    print_info "设置管理员账号"
    echo -n "请输入管理员用户名 (默认: admin): "
    read admin_user
    admin_user=${admin_user:-admin}
    
    echo -n "请输入管理员密码 (默认: admin): "
    read -s admin_pass
    echo
    admin_pass=${admin_pass:-admin}
    
    echo -n "请再次输入密码: "
    read -s admin_pass2
    echo
    
    if [ "$admin_pass" != "$admin_pass2" ]; then
        print_error "两次输入的密码不一致"
        get_credentials
    fi
}

# 主函数
main() {
    echo "================================================="
    echo "          EMS3 自动安装脚本"
    echo "================================================="
    
    # 检查是否以root运行
    if [ "$EUID" = 0 ]; then 
        print_error "请不要以root用户运行此脚本"
        exit 1
    fi
    
    # 检查系统
    check_system
    
    # 安装依赖
    install_dependencies
    
    # 检查Python和Java
    check_python
    check_java
    
    # 获取管理员凭据
    get_credentials
    
    # 下载和初始化EMS3
    download_ems3
    
    # 使用设置的用户名和密码初始化
    print_info "使用设置的凭据初始化EMS3..."
    python3 init.py --username "$admin_user" --password "$admin_pass"
    
    install_requirements
    
    # 创建系统服务
    create_service
    
    echo "================================================="
    print_info "安装完成！"
    print_info "EMS3已经安装并启动成功"
    print_info "您可以通过以下命令管理服务："
    echo "启动: sudo systemctl start ems3"
    echo "停止: sudo systemctl stop ems3"
    echo "重启: sudo systemctl restart ems3"
    echo "状态: sudo systemctl status ems3"
    print_info "请访问 http://$(hostname -I | cut -d' ' -f1):5000 使用EMS3"
    print_info "登录用户名: $admin_user"
    echo "================================================="
}

# 执行主函数
main