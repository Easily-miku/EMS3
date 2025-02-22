from flask import Flask, render_template, jsonify, request, send_from_directory, redirect, url_for, session
import os
import json
import subprocess
import psutil
import time
import requests
from datetime import datetime, timedelta
import uuid
import shutil
import threading
from queue import Queue
import base64
import hashlib
import functools
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
import zipfile
from shutil import which

app = Flask(__name__)

# 全局变量
minecraft_processes = {}
config = None
download_status = {}
download_queue = Queue()
command_history = {}
scheduler = BackgroundScheduler()

# 定时任务存储
scheduled_tasks = {}

# OpenFrp API 基础URL
OPENFRP_BASE_URL = "https://api.openfrp.net"

# OpenFrp 运行状态
frpc_process = None

# 添加日志翻译字典
LOG_TRANSLATIONS = {
    "Done": "完成",
    "Starting minecraft server": "正在启动Minecraft服务器",
    "Loading properties": "加载配置文件",
    "Default game type": "默认游戏模式",
    "Preparing level": "准备世界中",
    "Starting Minecraft server on": "在以下地址启动Minecraft服务器",
    "Preparing spawn area": "准备出生点区域",
    "Time elapsed": "耗时",
    "For help": "获取帮助请输入",
    "Stopping server": "正在停止服务器",
    "Server stopped": "服务器已停止",
    "joined the game": "加入了游戏",
    "left the game": "离开了游戏",
    "Unknown command": "未知命令",
    "Invalid command syntax": "命令语法无效"
}

class OpenFrpAPI:
    def __init__(self, token, authorization):
        self.token = token
        self.authorization = authorization
        self.headers = {"Authorization": authorization}
    
    def get_user_info(self):
        """获取用户信息"""
        try:
            response = requests.post(
                f"{OPENFRP_BASE_URL}/frp/api/getUserInfo",
                headers=self.headers
            )
            data = response.json()
            if data["flag"]:
                return {"success": True, "data": data["data"]}
            return {"success": False, "message": data.get("msg", "获取用户信息失败")}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_node_list(self):
        """获取节点列表"""
        try:
            response = requests.post(
                f"{OPENFRP_BASE_URL}/frp/api/getNodeList",
                headers=self.headers
            )
            data = response.json()
            if data["flag"]:
                return {"success": True, "data": data["data"]}
            return {"success": False, "message": data.get("msg", "获取节点列表失败")}
        except Exception as e:
            return {"success": False, "message": str(e)}

    def get_proxies(self):
        """获取用户隧道列表"""
        try:
            response = requests.post(
                f"{OPENFRP_BASE_URL}/frp/api/getUserProxies",
                headers=self.headers
            )
            data = response.json()
            if data["flag"]:
                return {"success": True, "data": data["data"]["list"]}
            return {"success": False, "message": data.get("msg", "获取隧道列表失败")}
        except Exception as e:
            return {"success": False, "message": str(e)}

def find_java_in_path():
    """在系统PATH中查找默认的Java"""
    try:
        # 检查默认的java命令
        process = subprocess.Popen(['java', '-version'], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE,
                                text=True)
        _, stderr = process.communicate()
        version = stderr.split('\n')[0]
        return {
            'path': 'java',
            'version': version,
            'is_default': True
        }
    except:
        return None

def load_config():
    """加载或创建配置文件"""
    default_config = {
        "web_port": 5000,
        "security": {
            "secret_key": os.urandom(24).hex(),
            "admin_user": "admin",
            "admin_password": hashlib.sha256("admin".encode()).hexdigest(),
            "login_timeout": 3600
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

    config_path = 'config/config.json'
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            # 确保所有必需的配置项都存在
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            # 特别确保 security 部分存在
            if 'security' not in config:
                config['security'] = default_config['security']
            # 保存更新后的配置
            os.makedirs('config', exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            return config
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}")
            return default_config
    else:
        # 创建新的配置文件
        os.makedirs('config', exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
        return default_config

def save_config():
    os.makedirs('config', exist_ok=True)
    with open('config/config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# 下载线程函数
def download_thread():
    while True:
        task = download_queue.get()
        if task is None:
            break
            
        server_id, name, mc_version, core_version = task
        download_status[server_id] = {
            "status": "downloading",
            "progress": 0,
            "message": "正在获取下载信息..."
        }
        
        try:
            # 获取下载信息
            response = requests.get(f"{MIRROR_API_BASE}/{name}/{mc_version}/{core_version}")
            if not response.ok:
                raise Exception("获取下载信息失败")
            
            download_info = response.json()
            if not download_info.get("success"):
                raise Exception(download_info.get("message", "获取下载信息失败"))
            
            # 下载文件
            download_url = download_info["data"]["download_url"]
            response = requests.get(download_url, stream=True)
            if not response.ok:
                raise Exception("下载文件失败")
            
            # 获取文件大小
            total_size = int(response.headers.get('content-length', 0))
            
            server = config["servers"][server_id]
            file_path = os.path.join(server["server_path"], download_info["data"]["filename"])
            
            # 创建临时文件
            temp_path = file_path + ".tmp"
            downloaded_size = 0
            
            with open(temp_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        if total_size:
                            progress = (downloaded_size / total_size) * 100
                            download_status[server_id]["progress"] = progress
                            download_status[server_id]["message"] = f"下载中... {progress:.1f}%"
            
            # 下载完成，移动文件
            os.replace(temp_path, file_path)
            
            # 更新服务器配置
            config["servers"][server_id]["server_jar"] = download_info["data"]["filename"]
            config["servers"][server_id]["type"] = name
            save_config()
            
            download_status[server_id] = {
                "status": "completed",
                "progress": 100,
                "message": "下载完成"
            }
            
        except Exception as e:
            download_status[server_id] = {
                "status": "error",
                "progress": 0,
                "message": str(e)
            }
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
        download_queue.task_done()

# 启动下载线程
download_thread = threading.Thread(target=download_thread)
download_thread.daemon = True
download_thread.start()

# 登录装饰器
def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            if request.is_json:
                return jsonify({"status": "error", "message": "请先登录"}), 401
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if (username == config['security']['admin_user'] and 
            hashlib.sha256(password.encode()).hexdigest() == config['security']['admin_password']):
            session['logged_in'] = True
            session.permanent = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="用户名或密码错误")
    
    return render_template('login.html')

# 主页路由
@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/api/servers')
@login_required
def get_servers():
    servers_data = {}
    for server_id, server in config["servers"].items():
        players = get_online_players(server_id)
        servers_data[server_id] = {
            **server,
            "online_players": len(players),
            "players": players
        }
    return jsonify({"servers": servers_data})

@app.route('/api/servers', methods=['POST'])
@login_required
def create_server():
    data = request.json
    server_id = str(uuid.uuid4())
    server_path = os.path.join('servers', server_id)
    
    config["servers"][server_id] = {
        "name": data["name"],
        "server_path": server_path,
        "server_jar": data.get("server_jar", "server.jar"),
        "java_path": data.get("java_path", "java"),
        "java_args": data.get("java_args", "-Xmx1024M -Xms1024M"),
        "server_port": data.get("server_port", 25565),
        "type": data.get("type", "vanilla")
    }
    
    os.makedirs(server_path, exist_ok=True)
    save_config()
    return jsonify({"status": "success", "server_id": server_id})

@app.route('/api/servers/<server_id>', methods=['DELETE'])
@login_required
def delete_server(server_id):
    if server_id in minecraft_processes:
        return jsonify({"status": "error", "message": "请先停止服务器"})
    
    server = config["servers"].get(server_id)
    if server:
        shutil.rmtree(server["server_path"], ignore_errors=True)
        del config["servers"][server_id]
        save_config()
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "服务器不存在"})

@app.route('/api/start/<server_id>', methods=['POST'])
@login_required
def start_server(server_id):
    if server_id not in config["servers"]:
        return jsonify({"status": "error", "message": "服务器不存在"})
    
    if server_id in minecraft_processes and minecraft_processes[server_id].poll() is None:
        return jsonify({"status": "error", "message": "服务器已在运行"})
    
    server = config["servers"][server_id]
    # 使用绝对路径
    server_path = os.path.abspath(server['server_path'])
    jar_path = os.path.abspath(os.path.join(server_path, server['server_jar']))
    
    # 检查服务器核心文件是否存在
    if not os.path.exists(jar_path):
        return jsonify({
            "status": "error", 
            "message": f"服务器核心文件不存在: {jar_path}\n请先下载服务器核心文件"
        })
    
    try:
        # 创建日志目录
        logs_dir = os.path.join(server_path, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # 构建命令列表
        java_args = server['java_args'].split()
        cmd = [server['java_path']] + java_args + ['-jar', jar_path, 'nogui']
        
        # 启动进程并重定向输出到日志文件
        log_file = os.path.join(logs_dir, 'latest.log')
        with open(log_file, 'w', encoding='utf-8') as f:
            # 使用CREATE_NO_WINDOW标志来隐藏控制台窗口（仅在Windows上有效）
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            minecraft_processes[server_id] = subprocess.Popen(
                cmd,
                cwd=server_path,
                stdout=f,
                stderr=f,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,  # 行缓冲，确保日志及时写入
                startupinfo=startupinfo
            )
        
        # 立即返回成功响应，不等待进程启动
        return jsonify({"status": "success", "message": "服务器正在启动中"})
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"启动失败: {str(e)}"})

@app.route('/api/stop/<server_id>', methods=['POST'])
@login_required
def stop_server(server_id):
    if server_id not in minecraft_processes:
        return jsonify({"status": "error", "message": "服务器未运行"})
    
    process = minecraft_processes[server_id]
    if process.poll() is None:
        process.terminate()
        time.sleep(2)
        if process.poll() is None:
            process.kill()
        del minecraft_processes[server_id]
        return jsonify({"status": "success", "message": "服务器已停止"})
    return jsonify({"status": "error", "message": "服务器未运行"})

@app.route('/api/status/<server_id>')
@login_required
def get_status(server_id):
    if server_id in minecraft_processes:
        process = minecraft_processes[server_id]
        if process.poll() is None:
            try:
                proc = psutil.Process(process.pid)
                # 获取CPU使用率前先调用一次
                proc.cpu_percent()
                # 等待一小段时间后再次获取，这样可以得到准确的CPU使用率
                time.sleep(0.1)
                # 获取CPU核心数
                cpu_count = psutil.cpu_count()
                # 计算单个进程的平均CPU使用率
                cpu_percent = proc.cpu_percent() / cpu_count if cpu_count else 0
                # 获取内存使用情况（MB）
                memory_mb = proc.memory_info().rss / 1024 / 1024
                return jsonify({
                    "status": "running",
                    "pid": process.pid,
                    "cpu_percent": cpu_percent,
                    "memory_mb": round(memory_mb, 2)
                })
            except:
                del minecraft_processes[server_id]
    return jsonify({"status": "stopped"})

def translate_log(log_line):
    """翻译日志内容"""
    for eng, chn in LOG_TRANSLATIONS.items():
        if eng in log_line:
            log_line = log_line.replace(eng, chn)
    return log_line

@app.route('/api/logs/<server_id>')
@login_required
def get_logs(server_id):
    if server_id not in config["servers"]:
        return jsonify({"status": "error", "message": "服务器不存在"})
    
    server = config["servers"][server_id]
    log_file = os.path.join(server['server_path'], 'logs', 'latest.log')
    
    try:
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                # 读取最后100行日志
                logs = []
                for line in f:
                    line = line.strip()
                    if line:  # 忽略空行
                        logs.append(line)
                        if len(logs) > 100:
                            logs.pop(0)
                # 翻译日志
                translated_logs = [translate_log(log) for log in logs]
            return jsonify({"logs": translated_logs})
        else:
            # 如果日志文件不存在，检查服务器是否在运行
            if server_id in minecraft_processes:
                process = minecraft_processes[server_id]
                if process.poll() is not None:
                    # 服务器已停止但进程仍在列表中
                    del minecraft_processes[server_id]
                    return jsonify({
                        "status": "error",
                        "message": "服务器已停止运行"
                    })
            return jsonify({"logs": []})
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"读取日志失败: {str(e)}"
        })

# 文件管理相关API
@app.route('/api/files/<server_id>')
@login_required
def list_files(server_id):
    if server_id not in config["servers"]:
        return jsonify({"status": "error", "message": "服务器不存在"})
    
    server = config["servers"][server_id]
    path = request.args.get('path', '')
    full_path = os.path.join(server['server_path'], path)
    
    try:
        files = []
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            files.append({
                "name": item,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                "modified": datetime.fromtimestamp(os.path.getmtime(item_path)).isoformat()
            })
        return jsonify({"files": files})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/files/<server_id>/content', methods=['GET'])
@login_required
def get_file_content(server_id):
    if server_id not in config["servers"]:
        return jsonify({"status": "error", "message": "服务器不存在"})
    
    server = config["servers"][server_id]
    path = request.args.get('path', '')
    full_path = os.path.join(server['server_path'], path)
    
    try:
        if not os.path.isfile(full_path):
            return jsonify({"status": "error", "message": "文件不存在"})
        
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({"content": content})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/files/<server_id>/content', methods=['POST'])
@login_required
def save_file_content(server_id):
    if server_id not in config["servers"]:
        return jsonify({"status": "error", "message": "服务器不存在"})
    
    server = config["servers"][server_id]
    path = request.json.get('path', '')
    content = request.json.get('content', '')
    full_path = os.path.join(server['server_path'], path)
    
    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/files/<server_id>/upload', methods=['POST'])
@login_required
def upload_file(server_id):
    if server_id not in config["servers"]:
        return jsonify({"status": "error", "message": "服务器不存在"})
    
    server = config["servers"][server_id]
    path = request.form.get('path', '')
    file = request.files.get('file')
    
    if not file:
        return jsonify({"status": "error", "message": "没有文件"})
    
    try:
        full_path = os.path.join(server['server_path'], path, file.filename)
        file.save(full_path)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/files/<server_id>/delete', methods=['POST'])
@login_required
def delete_file(server_id):
    if server_id not in config["servers"]:
        return jsonify({"status": "error", "message": "服务器不存在"})
    
    server = config["servers"][server_id]
    path = request.json.get('path', '')
    full_path = os.path.join(server['server_path'], path)
    
    try:
        if os.path.isdir(full_path):
            shutil.rmtree(full_path)
        else:
            os.remove(full_path)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# 下载核心相关API
MIRROR_API_BASE = "https://download.fastmirror.net/api/v3"

@app.route('/api/cores')
@login_required
def get_cores():
    try:
        response = requests.get(MIRROR_API_BASE)
        if response.ok:
            data = response.json()
            if data.get("success"):
                cores = []
                for core in data["data"]:
                    # 添加一些有用的信息
                    cores.append({
                        "name": core["name"],
                        "tag": core["tag"],
                        "homepage": core["homepage"],
                        "recommend": core["recommend"]
                    })
                return jsonify({"status": "success", "cores": cores})
        return jsonify({"status": "error", "message": "获取核心列表失败"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/cores/<name>')
@login_required
def get_core_versions(name):
    try:
        response = requests.get(f"{MIRROR_API_BASE}/{name}")
        if response.ok:
            data = response.json()
            if data.get("success"):
                return jsonify({
                    "status": "success", 
                    "versions": data["data"]["mc_versions"]
                })
        return jsonify({"status": "error", "message": "获取版本列表失败"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/cores/<name>/<mc_version>')
@login_required
def get_core_builds(name, mc_version):
    try:
        response = requests.get(f"{MIRROR_API_BASE}/{name}/{mc_version}")
        if response.ok:
            data = response.json()
            if data.get("success"):
                return jsonify({
                    "status": "success", 
                    "builds": data["data"]["builds"]
                })
        return jsonify({"status": "error", "message": "获取构建版本失败"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/download/<server_id>', methods=['POST'])
@login_required
def download_core(server_id):
    if server_id not in config["servers"]:
        return jsonify({"status": "error", "message": "服务器不存在"})
    
    if server_id in download_status and download_status[server_id]["status"] == "downloading":
        return jsonify({"status": "error", "message": "已有下载任务在进行中"})
    
    data = request.json
    name = data.get("name")
    mc_version = data.get("mc_version")
    core_version = data.get("core_version")
    
    if not all([name, mc_version, core_version]):
        return jsonify({"status": "error", "message": "参数不完整"})
    
    try:
        # 先获取下载信息
        metadata_response = requests.get(f"{MIRROR_API_BASE}/{name}/{mc_version}/{core_version}")
        if not metadata_response.ok:
            return jsonify({"status": "error", "message": "获取下载信息失败"})
        
        metadata = metadata_response.json()
        if not metadata.get("success"):
            return jsonify({"status": "error", "message": metadata.get("message", "获取下载信息失败")})
        
        # 将下载信息添加到任务队列
        download_queue.put((server_id, name, mc_version, core_version))
        return jsonify({
            "status": "success", 
            "message": "已添加到下载队列",
            "filename": metadata["data"]["filename"]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/api/download/<server_id>/status')
@login_required
def get_download_status(server_id):
    if server_id not in download_status:
        return jsonify({
            "status": "none",
            "progress": 0,
            "message": "无下载任务"
        })
    return jsonify(download_status[server_id])

# 添加公告API
@app.route('/api/announcements')
@login_required
def get_announcements():
    announcements = [
        {
            "id": 1,
            "title": "欢迎使用 EMS3 管理面板",
            "content": "EMS3 是一个轻量级、专业的 Minecraft 服务器管理面板。使用前请仔细阅读使用说明。",
            "type": "info",
            "date": "2024-03-19"
        },
        {
            "id": 2,
            "title": "使用说明",
            "content": """
1. 首次使用请先在右侧工具栏创建新服务器
2. 创建服务器后需要下载服务器核心才能启动
3. 可以在文件管理中编辑服务器配置文件
4. 如遇问题请查看日志或联系管理员
            """.strip(),
            "type": "warning",
            "date": "2024-03-19"
        }
    ]
    return jsonify({"announcements": announcements})

# Java路径管理API
@app.route('/api/java/detect', methods=['POST'])
@login_required
def detect_java():
    """检测系统默认的Java"""
    try:
        java_info = find_java_in_path()
        if java_info:
            return jsonify({
                "status": "success",
                "java_info": java_info
            })
        return jsonify({
            "status": "error",
            "message": "未找到系统默认的Java"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/java/paths', methods=['GET'])
@login_required
def get_java_paths():
    """获取所有Java路径"""
    try:
        # 获取系统默认Java
        auto_java = find_java_in_path()
        
        # 获取手动添加的Java
        manual_paths = []
        for java_info in config.get("java_paths", {}).get("manual", []):
            if isinstance(java_info, str):
                # 处理旧格式的数据
                path = java_info
                try:
                    if os.path.isfile(path):
                        result = subprocess.run([path, '-version'], capture_output=True, text=True, stderr=subprocess.PIPE)
                        version = result.stderr.split('\n')[0]
                        manual_paths.append({
                            'path': path,
                            'version': version,
                            'manual': True
                        })
                except:
                    continue
            else:
                # 新格式的数据，保留原有版本信息
                manual_paths.append(java_info)
        
        return jsonify({
            "status": "success",
            "auto_paths": auto_java,
            "manual_paths": manual_paths
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/java/paths', methods=['POST'])
@login_required
def add_java_path():
    """添加自定义Java路径"""
    data = request.json
    path = data.get('path', '').strip()
    
    if not path:
        return jsonify({
            "status": "error",
            "message": "请提供Java路径"
        })
    
    # 处理路径中的引号和反斜杠
    path = path.strip('"\'').replace('/', '\\')
    
    # 如果是默认java
    if path.lower() == 'java':
        java_info = find_java_in_path()
        if not java_info:
            return jsonify({
                "status": "error",
                "message": "系统中未找到默认的Java"
            })
        return jsonify({
            "status": "success",
            "version": java_info['version']
        })
    
    # 检查路径是否已存在
    for java_info in config['java_paths']['manual']:
        if isinstance(java_info, dict) and java_info['path'].lower() == path.lower():
            return jsonify({
                "status": "error",
                "message": "该Java路径已经添加过了"
            })
        elif isinstance(java_info, str) and java_info.lower() == path.lower():
            return jsonify({
                "status": "error",
                "message": "该Java路径已经添加过了"
            })
    
    # 验证自定义路径
    if not os.path.isfile(path):
        return jsonify({
            "status": "error",
            "message": f"指定的路径无效: {path}\n请确保该路径指向一个有效的Java可执行文件。"
        })
    
    try:
        # 验证Java路径
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
        process = subprocess.Popen([path, '-version'], 
                                stdout=subprocess.PIPE, 
                                stderr=subprocess.PIPE,
                                text=True,
                                startupinfo=startupinfo)
        _, stderr = process.communicate()
        version = stderr.split('\n')[0]
        
        # 创建Java信息对象
        java_info = {
            'path': path,
            'version': version,
            'manual': True,
            'added_time': datetime.now().isoformat()
        }
        
        # 确保配置文件中有java_paths结构
        if 'java_paths' not in config:
            config['java_paths'] = {'auto': '', 'manual': []}
        if 'manual' not in config['java_paths']:
            config['java_paths']['manual'] = []
            
        # 检查是否已存在
        exists = False
        for i, existing in enumerate(config['java_paths']['manual']):
            if isinstance(existing, dict) and existing['path'] == path:
                config['java_paths']['manual'][i] = java_info
                exists = True
                break
            elif isinstance(existing, str) and existing == path:
                config['java_paths']['manual'][i] = java_info
                exists = True
                break
                
        if not exists:
            config['java_paths']['manual'].append(java_info)
        
        save_config()
        
        return jsonify({
            "status": "success",
            "version": version,
            "java_info": java_info
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"无效的Java路径: {str(e)}"
        })

@app.route('/api/java/paths/<path:path>', methods=['DELETE'])
@login_required
def remove_java_path(path):
    """删除手动添加的Java路径"""
    try:
        path = base64.b64decode(path).decode('utf-8')
        manual_paths = config['java_paths']['manual']
        
        # 检查是否有服务器正在使用这个Java路径
        for server_id, server in config['servers'].items():
            if server['java_path'] == path:
                return jsonify({
                    "status": "error",
                    "message": f"无法删除，该Java路径正在被服务器 {server['name']} 使用"
                })
        
        # 查找并删除匹配的路径
        for i, java_info in enumerate(manual_paths):
            if (isinstance(java_info, dict) and java_info['path'] == path) or \
               (isinstance(java_info, str) and java_info == path):
                del manual_paths[i]
                save_config()
                return jsonify({"status": "success"})
                
        return jsonify({
            "status": "error",
            "message": "路径不存在"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

# 命令执行API
@app.route('/api/servers/<server_id>/command', methods=['POST'])
@login_required
def execute_command(server_id):
    if server_id not in minecraft_processes:
        return jsonify({"status": "error", "message": "服务器未运行"})
    
    data = request.json
    command = data.get('command')
    if not command:
        return jsonify({"status": "error", "message": "请提供命令"})
    
    process = minecraft_processes[server_id]
    if process.poll() is None:
        try:
            process.stdin.write(command + '\n')
            process.stdin.flush()
            
            # 记录命令历史
            if server_id not in command_history:
                command_history[server_id] = []
            command_history[server_id].append({
                "command": command,
                "timestamp": datetime.now().isoformat()
            })
            if len(command_history[server_id]) > 50:  # 限制历史记录数量
                command_history[server_id].pop(0)
            
            return jsonify({"status": "success"})
        except Exception as e:
            return jsonify({"status": "error", "message": f"执行命令失败: {str(e)}"})
    return jsonify({"status": "error", "message": "服务器未运行"})

@app.route('/api/servers/<server_id>/command/history')
@login_required
def get_command_history(server_id):
    return jsonify({
        "history": command_history.get(server_id, [])
    })

# 快捷指令管理API
@app.route('/api/quick-commands')
@login_required
def get_quick_commands():
    return jsonify({"commands": config["quick_commands"]})

@app.route('/api/quick-commands', methods=['POST'])
@login_required
def add_quick_command():
    data = request.json
    name = data.get('name')
    command = data.get('command')
    description = data.get('description')
    
    if not all([name, command]):
        return jsonify({"status": "error", "message": "请提供完整信息"})
    
    config["quick_commands"][name] = {
        "command": command,
        "description": description or ""
    }
    save_config()
    return jsonify({"status": "success"})

@app.route('/api/quick-commands/<name>', methods=['DELETE'])
@login_required
def delete_quick_command(name):
    if name in config["quick_commands"]:
        del config["quick_commands"][name]
        save_config()
        return jsonify({"status": "success"})
    return jsonify({"status": "error", "message": "指令不存在"})

@app.route('/api/servers/<server_id>/settings', methods=['POST'])
@login_required
def update_server_settings(server_id):
    if server_id not in config["servers"]:
        return jsonify({"status": "error", "message": "服务器不存在"})
    
    data = request.json
    server = config["servers"][server_id]
    
    # 验证Java路径
    java_path = data.get("java_path")
    if java_path != "java":  # 如果不是使用默认的java
        if not os.path.isfile(java_path):
            return jsonify({
                "status": "error",
                "message": "无效的Java路径"
            })
        try:
            process = subprocess.Popen([java_path, '-version'], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE,
                                    text=True)
            process.communicate()
            if process.returncode != 0:
                return jsonify({
                    "status": "error",
                    "message": "Java路径验证失败"
                })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Java路径验证失败: {str(e)}"
            })
    
    # 更新服务器设置
    server["name"] = data.get("name", server["name"])
    server["server_port"] = data.get("server_port", server["server_port"])
    server["java_path"] = java_path
    server["java_args"] = data.get("java_args", server["java_args"])
    
    save_config()
    return jsonify({"status": "success"})

# 定时任务相关函数
def execute_scheduled_command(server_id, command):
    """执行预定的命令"""
    if server_id in minecraft_processes:
        process = minecraft_processes[server_id]
        if process.poll() is None:
            try:
                process.stdin.write(command + '\n')
                process.stdin.flush()
                print(f"定时任务执行成功: 服务器 {server_id} - 命令 {command}")
            except Exception as e:
                print(f"定时任务执行失败: {str(e)}")

def execute_scheduled_backup(server_id, keep_backups=5):
    """执行定时备份"""
    try:
        # 创建备份
        backup_info, error = create_backup(server_id)
        if error:
            print(f"定时备份失败: {error}")
            return
            
        # 如果设置了保留数量，清理旧备份
        if keep_backups > 0:
            server = config["servers"][server_id]
            backup_dir = os.path.join(server['server_path'], 'backups')
            if os.path.exists(backup_dir):
                # 获取所有备份文件并按时间排序
                backups = []
                for file in os.listdir(backup_dir):
                    if file.startswith('backup_') and file.endswith('.zip'):
                        file_path = os.path.join(backup_dir, file)
                        backups.append((file_path, os.path.getmtime(file_path)))
                
                # 按时间从新到旧排序
                backups.sort(key=lambda x: x[1], reverse=True)
                
                # 删除多余的备份
                for backup_path, _ in backups[keep_backups:]:
                    try:
                        os.remove(backup_path)
                        print(f"删除旧备份: {backup_path}")
                    except Exception as e:
                        print(f"删除旧备份失败: {str(e)}")
        
        print(f"定时备份成功: {backup_info['name']}")
    except Exception as e:
        print(f"定时备份执行失败: {str(e)}")

def restart_server(server_id):
    """重启服务器"""
    try:
        # 先停止服务器
        if server_id in minecraft_processes:
            process = minecraft_processes[server_id]
            if process.poll() is None:
                process.terminate()
                time.sleep(5)
                if process.poll() is None:
                    process.kill()
                del minecraft_processes[server_id]
        
        # 等待几秒后重启
        time.sleep(5)
        
        # 重启服务器
        server = config["servers"][server_id]
        server_path = os.path.abspath(server['server_path'])
        jar_path = os.path.abspath(os.path.join(server_path, server['server_jar']))
        
        if not os.path.exists(jar_path):
            print(f"重启失败: 服务器核心文件不存在 {jar_path}")
            return
            
        logs_dir = os.path.join(server_path, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        java_args = server['java_args'].split()
        cmd = [server['java_path']] + java_args + ['-jar', jar_path, 'nogui']
        
        log_file = os.path.join(logs_dir, 'latest.log')
        with open(log_file, 'w', encoding='utf-8') as f:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE
            
            minecraft_processes[server_id] = subprocess.Popen(
                cmd,
                cwd=server_path,
                stdout=f,
                stderr=f,
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
                startupinfo=startupinfo
            )
        print(f"服务器 {server_id} 重启成功")
    except Exception as e:
        print(f"重启失败: {str(e)}")

# 定时任务API
@app.route('/api/tasks', methods=['GET'])
@login_required
def get_tasks():
    """获取所有定时任务"""
    tasks = []
    for job in scheduler.get_jobs():
        task_id = job.id
        task = scheduled_tasks.get(task_id, {})
        tasks.append({
            'id': task_id,
            'name': task.get('name', '未命名任务'),
            'type': task.get('type', '未知类型'),
            'server_id': task.get('server_id', ''),
            'command': task.get('command', ''),
            'schedule_type': task.get('schedule_type', ''),
            'schedule_value': task.get('schedule_value', ''),
            'next_run_time': job.next_run_time.strftime('%Y-%m-%d %H:%M:%S') if job.next_run_time else None
        })
    return jsonify({'tasks': tasks})

@app.route('/api/tasks', methods=['POST'])
@login_required
def create_task():
    """创建定时任务"""
    data = request.json
    task_type = data.get('type')  # 'command', 'restart', 或 'backup'
    server_id = data.get('server_id')
    name = data.get('name', '未命名任务')
    schedule_type = data.get('schedule_type')  # 'cron', 'interval', 或 'date'
    schedule_value = data.get('schedule_value')
    
    if not all([task_type, server_id, schedule_type, schedule_value]):
        return jsonify({
            'status': 'error',
            'message': '缺少必要参数'
        })
    
    try:
        # 创建触发器
        if schedule_type == 'cron':
            trigger = CronTrigger.from_crontab(schedule_value)
        elif schedule_type == 'interval':
            trigger = IntervalTrigger(seconds=int(schedule_value))
        elif schedule_type == 'date':
            trigger = DateTrigger(run_date=datetime.fromisoformat(schedule_value))
        else:
            return jsonify({
                'status': 'error',
                'message': '不支持的调度类型'
            })
        
        # 创建任务
        task_id = str(uuid.uuid4())
        if task_type == 'command':
            command = data.get('command')
            if not command:
                return jsonify({
                    'status': 'error',
                    'message': '命令不能为空'
                })
            job = scheduler.add_job(
                execute_scheduled_command,
                trigger=trigger,
                args=[server_id, command],
                id=task_id
            )
        elif task_type == 'backup':
            keep_backups = int(data.get('keep_backups', 5))
            job = scheduler.add_job(
                execute_scheduled_backup,
                trigger=trigger,
                args=[server_id, keep_backups],
                id=task_id
            )
        else:  # restart
            job = scheduler.add_job(
                restart_server,
                trigger=trigger,
                args=[server_id],
                id=task_id
            )
        
        # 保存任务信息
        scheduled_tasks[task_id] = {
            'name': name,
            'type': task_type,
            'server_id': server_id,
            'command': data.get('command'),
            'keep_backups': data.get('keep_backups', 5),
            'schedule_type': schedule_type,
            'schedule_value': schedule_value
        }
        
        return jsonify({
            'status': 'success',
            'task_id': task_id
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/tasks/<task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    """删除定时任务"""
    try:
        scheduler.remove_job(task_id)
        if task_id in scheduled_tasks:
            del scheduled_tasks[task_id]
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/tasks/<task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    """更新定时任务"""
    if task_id not in scheduled_tasks:
        return jsonify({
            'status': 'error',
            'message': '任务不存在'
        })
    
    data = request.json
    name = data.get('name')
    schedule_type = data.get('schedule_type')
    schedule_value = data.get('schedule_value')
    
    try:
        # 更新触发器
        if schedule_type and schedule_value:
            if schedule_type == 'cron':
                trigger = CronTrigger.from_crontab(schedule_value)
            elif schedule_type == 'interval':
                trigger = IntervalTrigger(seconds=int(schedule_value))
            elif schedule_type == 'date':
                trigger = DateTrigger(run_date=datetime.fromisoformat(schedule_value))
            else:
                return jsonify({
                    'status': 'error',
                    'message': '不支持的调度类型'
                })
            
            # 重新调度任务
            scheduler.reschedule_job(
                task_id,
                trigger=trigger
            )
            
            # 更新任务信息
            scheduled_tasks[task_id].update({
                'schedule_type': schedule_type,
                'schedule_value': schedule_value
            })
        
        # 更新名称
        if name:
            scheduled_tasks[task_id]['name'] = name
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/logout', methods=['POST'])
@login_required
def api_logout():
    """退出登录"""
    session.clear()
    return jsonify({
        'status': 'success',
        'message': '已成功退出登录'
    })

@app.route('/api/system/stats')
@login_required
def get_system_stats():
    """获取系统资源使用情况"""
    try:
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用率
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_used = memory.used / (1024 * 1024 * 1024)  # 转换为GB
        memory_total = memory.total / (1024 * 1024 * 1024)  # 转换为GB
        
        return jsonify({
            'status': 'success',
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'memory_used': round(memory_used, 2),
            'memory_total': round(memory_total, 2)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

def get_online_players(server_id):
    """获取服务器在线玩家"""
    if server_id not in minecraft_processes:
        return []
    
    process = minecraft_processes[server_id]
    if process.poll() is not None:
        return []
    
    try:
        # 发送list命令
        process.stdin.write('list\n')
        process.stdin.flush()
        
        # 读取日志文件获取最新的玩家列表
        server = config["servers"][server_id]
        log_file = os.path.join(server['server_path'], 'logs', 'latest.log')
        if not os.path.exists(log_file):
            return []
        
        # 读取最后几行日志
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[-10:]  # 读取最后10行
            
        # 查找包含玩家列表的行
        for line in reversed(lines):
            if 'There are' in line and 'players online' in line:
                # 解析玩家列表
                if ':' in line:
                    players_str = line.split(':')[-1].strip()
                    if players_str:
                        return [p.strip() for p in players_str.split(',')]
                break
        return []
    except Exception as e:
        print(f"获取在线玩家失败: {str(e)}")
        return []

@app.route('/api/servers/<server_id>/players')
@login_required
def get_server_players(server_id):
    """获取服务器在线玩家API"""
    if server_id not in config["servers"]:
        return jsonify({"status": "error", "message": "服务器不存在"})
    
    players = get_online_players(server_id)
    return jsonify({
        "status": "success",
        "players": players,
        "count": len(players)
    })

def create_backup(server_id):
    """创建服务器备份"""
    if server_id not in config["servers"]:
        return None, "服务器不存在"
    
    try:
        server = config["servers"][server_id]
        server_path = server['server_path']
        backup_dir = os.path.join(server_path, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"backup_{timestamp}.zip"
        backup_path = os.path.join(backup_dir, backup_name)
        
        # 创建ZIP文件
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # 遍历服务器目录
            for root, dirs, files in os.walk(server_path):
                # 排除backups目录和logs目录
                if 'backups' in dirs:
                    dirs.remove('backups')
                if 'logs' in dirs:
                    dirs.remove('logs')
                
                for file in files:
                    file_path = os.path.join(root, file)
                    # 计算相对路径
                    arc_path = os.path.relpath(file_path, server_path)
                    zipf.write(file_path, arc_path)
        
        # 获取备份文件大小
        backup_size = os.path.getsize(backup_path) / (1024 * 1024)  # 转换为MB
        
        return {
            'name': backup_name,
            'path': backup_path,
            'size': round(backup_size, 2),
            'time': timestamp
        }, None
    except Exception as e:
        return None, str(e)

@app.route('/api/servers/<server_id>/backup', methods=['POST'])
@login_required
def backup_server(server_id):
    """创建服务器备份API"""
    if server_id not in config["servers"]:
        return jsonify({"status": "error", "message": "服务器不存在"})
    
    backup_info, error = create_backup(server_id)
    if error:
        return jsonify({
            "status": "error",
            "message": f"创建备份失败: {error}"
        })
    
    return jsonify({
        "status": "success",
        "message": "备份创建成功",
        "backup": backup_info
    })

@app.route('/api/servers/<server_id>/backups')
@login_required
def list_backups(server_id):
    """获取服务器备份列表"""
    if server_id not in config["servers"]:
        return jsonify({"status": "error", "message": "服务器不存在"})
    
    try:
        server = config["servers"][server_id]
        backup_dir = os.path.join(server['server_path'], 'backups')
        if not os.path.exists(backup_dir):
            return jsonify({"backups": []})
        
        backups = []
        for file in os.listdir(backup_dir):
            if file.startswith('backup_') and file.endswith('.zip'):
                file_path = os.path.join(backup_dir, file)
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # 转换为MB
                file_time = file[7:-4]  # 从文件名提取时间戳
                
                backups.append({
                    'name': file,
                    'path': file_path,
                    'size': round(file_size, 2),
                    'time': file_time
                })
        
        # 按时间倒序排序
        backups.sort(key=lambda x: x['time'], reverse=True)
        return jsonify({"backups": backups})
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"获取备份列表失败: {str(e)}"
        })

@app.route('/api/servers/<server_id>/backups/<backup_name>')
@login_required
def download_backup(server_id, backup_name):
    """下载备份文件"""
    if server_id not in config["servers"]:
        return jsonify({"status": "error", "message": "服务器不存在"})
    
    try:
        server = config["servers"][server_id]
        backup_dir = os.path.join(server['server_path'], 'backups')
        backup_path = os.path.join(backup_dir, backup_name)
        
        if not os.path.exists(backup_path):
            return jsonify({"status": "error", "message": "备份文件不存在"})
        
        return send_from_directory(
            backup_dir,
            backup_name,
            as_attachment=True
        )
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"下载备份失败: {str(e)}"
        })

@app.route('/api/servers/<server_id>/backups/<backup_name>', methods=['DELETE'])
@login_required
def delete_backup(server_id, backup_name):
    """删除备份文件"""
    if server_id not in config["servers"]:
        return jsonify({"status": "error", "message": "服务器不存在"})
    
    try:
        server = config["servers"][server_id]
        backup_dir = os.path.join(server['server_path'], 'backups')
        backup_path = os.path.join(backup_dir, backup_name)
        
        if not os.path.exists(backup_path):
            return jsonify({"status": "error", "message": "备份文件不存在"})
        
        os.remove(backup_path)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"删除备份失败: {str(e)}"
        })

@app.route('/api/files/<server_id>/create_folder', methods=['POST'])
@login_required
def create_folder(server_id):
    """创建文件夹"""
    if server_id not in config["servers"]:
        return jsonify({"status": "error", "message": "服务器不存在"})
    
    server = config["servers"][server_id]
    path = request.json.get('path', '')
    full_path = os.path.join(server['server_path'], path)
    
    try:
        os.makedirs(full_path, exist_ok=True)
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"创建文件夹失败: {str(e)}"
        })

# OpenFrp API 相关路由
@app.route('/api/openfrp/user_info', methods=['GET'])
def get_user_info():
    """获取用户信息接口"""
    token = request.args.get('token')
    authorization = request.args.get('authorization')
    if not token or not authorization:
        return jsonify({"success": False, "message": "缺少token或authorization参数"})
    
    api = OpenFrpAPI(token, authorization)
    result = api.get_user_info()
    return jsonify(result)

@app.route('/api/openfrp/nodes', methods=['GET'])
def get_nodes():
    """获取节点列表接口"""
    token = request.args.get('token')
    authorization = request.args.get('authorization')
    if not token or not authorization:
        return jsonify({"success": False, "message": "缺少token或authorization参数"})
    
    api = OpenFrpAPI(token, authorization)
    result = api.get_node_list()
    return jsonify(result)

@app.route('/api/openfrp/proxies', methods=['GET'])
def get_proxies():
    """获取隧道列表接口"""
    token = request.args.get('token')
    authorization = request.args.get('authorization')
    if not token or not authorization:
        return jsonify({"success": False, "message": "缺少token或authorization参数"})
    
    api = OpenFrpAPI(token, authorization)
    result = api.get_proxies()
    return jsonify(result)

@app.route('/api/openfrp/start', methods=['POST'])
def start_proxy():
    """启动指定隧道"""
    token = request.json.get('token')
    proxy_id = request.json.get('proxy_id')
    
    if not token or not proxy_id:
        return jsonify({"success": False, "message": "缺少token或proxy_id参数"})
    
    success, message = run_frpc_background(token, proxy_id)
    return jsonify({"success": success, "message": message})

@app.route('/api/openfrp/stop', methods=['POST'])
def stop_proxy():
    """停止当前运行的隧道"""
    success = stop_frpc()
    return jsonify({
        "success": success,
        "message": "隧道已停止" if success else "没有正在运行的隧道"
    })

def stop_frpc():
    """停止frpc进程"""
    global frpc_process
    if frpc_process:
        try:
            frpc_process.terminate()
            time.sleep(2)
            if frpc_process.poll() is None:
                frpc_process.kill()
            frpc_process = None
            return True
        except Exception as e:
            print(f"停止frpc失败: {e}")
            return False
    return False

def run_frpc_background(token, proxy_id):
    """后台运行frpc"""
    global frpc_process
    try:
        # 先停止现有的frpc进程
        stop_frpc()
        
        # 根据操作系统确定frpc命令
        if os.name == 'nt':  # Windows系统
            frpc_path = "frpc/frpc.exe"
            if not os.path.exists(frpc_path):
                return False, "no_frpc_windows"  # Windows下未找到frpc.exe
        else:  # Linux/Unix系统
            # 检查PATH中是否存在frpc
            frpc_path = which('frpc')
            if not frpc_path:
                return False, "no_frpc_linux"  # Linux下未找到frpc
            
        # 构建启动命令
        cmd = [
            frpc_path,
            "-u", token,
            "-p", str(proxy_id)
        ]
        
        # 在后台运行frpc
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            
        frpc_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=startupinfo
        )
        
        # 等待一段时间检查进程是否正常运行
        time.sleep(2)
        if frpc_process.poll() is None:
            return True, "frpc启动成功"
        else:
            error = frpc_process.stderr.read().decode()
            return False, f"frpc启动失败: {error}"
    except Exception as e:
        return False, f"启动frpc失败: {str(e)}"

@app.route('/frp')
def frp():
    return render_template('frp.html')

if __name__ == '__main__':
    config = load_config()
    app.secret_key = config['security']['secret_key']
    app.permanent_session_lifetime = timedelta(seconds=config['security']['login_timeout'])
    
    # 启动调度器
    scheduler.start()
    
    app.run(host='0.0.0.0', port=config["web_port"], debug=True) 
