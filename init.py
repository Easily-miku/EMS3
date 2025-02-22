import os
import sys
import json
import shutil
import platform
import subprocess
from pathlib import Path

def print_color(text, color):
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'end': '\033[0m'
    }
    print(f"{colors.get(color, '')}{text}{colors['end']}")

def check_python_version():
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print_color("错误: Python版本必须 >= 3.7", "red")
        sys.exit(1)
    print_color(f"Python版本检查通过: {sys.version.split()[0]}", "green")

def check_java():
    try:
        # 修复subprocess.run参数问题
        process = subprocess.Popen(['java', '-version'], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE,
                                text=True)
        _, stderr = process.communicate()
        
        if process.returncode == 0:
            java_version = stderr.split('\n')[0]
            print_color(f"Java检查通过: {java_version}", "green")
            return True
        else:
            print_color("警告: Java检测失败", "yellow")
            return False
    except FileNotFoundError:
        print_color("警告: 未检测到Java，请确保已安装Java", "yellow")
        return False
    except Exception as e:
        print_color(f"警告: Java检测出错 - {str(e)}", "yellow")
        return False

def create_directory_structure():
    directories = [
        'servers',
        'backups',
        'logs',
        'config',
        'static',
        'templates'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print_color(f"创建目录: {directory}", "blue")

def create_config():
    config = {
        "web_port": 5000,
        "security": {
            "secret_key": os.urandom(24).hex(),
            "admin_user": "admin",
            "admin_password": "admin",  # 默认密码
            "login_timeout": 3600
        },
        "java_paths": {
            "auto": "",
            "manual": []
        },
        "quick_commands": {
            "op": "/op {player}",
            "gamemode": "/gamemode {mode} {player}",
            "time": "/time set {time}",
            "weather": "/weather {type}"
        },
        "servers": {}
    }
    
    config_path = Path('config/config.json')
    if not config_path.exists():
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        print_color("创建配置文件: config.json", "blue")
        print_color("默认用户名: admin", "yellow")
        print_color("默认密码: admin", "yellow")
        print_color("请及时修改默认密码！", "red")

def check_requirements():
    if not Path('requirements.txt').exists():
        requirements = [
            "flask>=2.0.0",
            "flask-login>=0.5.0",
            "psutil>=5.8.0",
            "requests>=2.26.0",
            "apscheduler>=3.8.1",
            "werkzeug>=2.0.0",
            "python-dotenv>=0.19.0"
        ]
        with open('requirements.txt', 'w') as f:
            f.write('\n'.join(requirements))
        print_color("创建依赖文件: requirements.txt", "blue")

def main():
    print_color("\n=== EMS3 初始化程序 ===", "blue")
    print_color("开始初始化...\n", "blue")
    
    # 检查Python版本
    check_python_version()
    
    # 检查Java
    check_java()
    
    # 创建目录结构
    create_directory_structure()
    
    # 创建配置文件
    create_config()
    
    # 检查requirements.txt
    check_requirements()
    
    print_color("\n初始化完成！", "green")
    print_color("\n接下来的步骤：", "yellow")
    print_color("1. 安装依赖: pip install -r requirements.txt", "yellow")
    print_color("2. 启动面板: python app.py", "yellow")
    print_color("3. 访问面板: http://localhost:5000", "yellow")
    print_color("\n安全提示：", "red")
    print_color("* 请及时修改默认密码", "red")
    print_color("* 建议配置反向代理和SSL", "red")
    print_color("* 定期备份服务器数据", "red")

if __name__ == "__main__":
    main() 
