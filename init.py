import os
import json
import shutil
import hashlib
import secrets

def generate_secret_key():
    """生成随机密钥"""
    return secrets.token_hex(32)

def hash_password(password):
    """使用SHA-256哈希密码"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_directories():
    """初始化必要的目录"""
    directories = ['config', 'servers', 'templates']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ 创建目录: {directory}")

def init_config(username=None, password=None):
    """初始化配置文件"""
    config_path = 'config/config.json'
    if not os.path.exists(config_path):
        # 如果没有提供用户名和密码，使用默认值
        if not username:
            username = "admin"
        if not password:
            password = "admin"

        default_config = {
            "web_port": 5000,
            "security": {
                "secret_key": generate_secret_key(),
                "admin_user": username,
                "admin_password": hash_password(password),
                "login_timeout": 3600,  # 登录超时时间（秒）
                "max_login_attempts": 5,  # 最大登录尝试次数
                "lockout_time": 300,  # 锁定时间（秒）
                "secure_paths": ["/admin", "/api"]  # 需要登录才能访问的路径
            },
            "java_paths": {
                "auto": "",
                "manual": []
            },
            "quick_commands": {
                "op": {
                    "command": "op {player}",
                    "description": "将玩家设为管理员"
                },
                "gamemode": {
                    "command": "gamemode {mode} {player}",
                    "description": "更改玩家游戏模式"
                },
                "time": {
                    "command": "time set {time}",
                    "description": "设置时间"
                },
                "weather": {
                    "command": "weather {type}",
                    "description": "设置天气"
                }
            },
            "servers": {}
        }
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        print(f"✓ 创建配置文件: {config_path}")
        print(f"✓ 初始用户名: {username}")
        print(f"✓ 初始密码: {password}")
    else:
        print(f"! 配置文件已存在: {config_path}")

def init_requirements():
    """初始化requirements.txt文件"""
    requirements = [
        'flask',
        'psutil',
        'requests',
        'flask-login',
        'flask-session'
    ]
    
    with open('requirements.txt', 'w') as f:
        f.write('\n'.join(requirements))
    print("✓ 创建requirements.txt")

def main(username=None, password=None):
    """主初始化函数"""
    print("开始初始化EMS3面板...")
    print("-" * 50)
    
    # 创建目录
    init_directories()
    
    # 初始化配置
    init_config(username, password)
    
    # 创建requirements.txt
    init_requirements()
    
    print("-" * 50)
    print("初始化完成！")
    print("\n后续步骤:")
    print("1. 运行 'pip install -r requirements.txt' 安装依赖")
    print("2. 运行 'python app.py' 启动面板")
    print("3. 访问 http://localhost:5000 使用面板")
    print("\n安全提示:")
    print("* 请及时修改默认密码")
    print("* 配置文件位于 config/config.json")
    print("* 可以在配置文件中修改登录超时时间和其他安全设置")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='初始化EMS3面板')
    parser.add_argument('--username', help='设置管理员用户名')
    parser.add_argument('--password', help='设置管理员密码')
    args = parser.parse_args()
    
    main(args.username, args.password) 