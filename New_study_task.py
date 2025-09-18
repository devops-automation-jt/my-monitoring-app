from flask import Flask, jsonify
import psutil
import random
from datetime import datetime
import platform

app = Flask(__name__)

# 模拟一些服务名称
SERVICES = [
    "nginx", "mysql", "redis", "elasticsearch",
    "kafka", "api-gateway", "auth-service"
]


def get_system_info():
    """获取基本系统信息"""
    return {
        "os": platform.system(),
        "os_version": platform.version(),
        "hostname": platform.node(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(logical=False),
        "cpu_count_logical": psutil.cpu_count(logical=True)
    }

def get_cpu_usage():
    """获取CPU使用情况"""
    return {
        "usage_percent": psutil.cpu_percent(interval=0.5),
        "per_core_usage": psutil.cpu_percent(percpu=True, interval=0.5),
        "load_average": psutil.getloadavg(),
        "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
    }


def get_memory_usage():
    """获取内存使用情况"""
    virtual = psutil.virtual_memory()
    swap = psutil.swap_memory()

    return {
        "virtual_memory": virtual._asdict(),
        "swap_memory": swap._asdict()
    }


def get_disk_usage():
    """获取磁盘使用情况"""
    disks = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disks.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "usage": usage._asdict()
            })
        except PermissionError:
            continue

    return {
        "disks": disks,
        "io_counters": psutil.disk_io_counters()._asdict()
    }


def get_network_stats():
    """获取网络统计信息"""
    net_io = psutil.net_io_counters()
    interfaces = {}

    for if_name, addrs in psutil.net_if_addrs().items():
        interfaces[if_name] = {
            "addresses": [addr._asdict() for addr in addrs]
        }

    return {
        "io_counters": net_io._asdict(),
        "interfaces": interfaces,
        "connections": len(psutil.net_connections())
    }


def get_service_status():
    """模拟服务状态检查"""
    statuses = []

    for service in SERVICES:
        # 随机模拟服务状态，但让大部分服务处于正常状态
        status = "running" if random.random() > 0.1 else "down"
        response_time = round(random.uniform(0.01, 2.5), 3)

        statuses.append({
            "service_name": service,
            "status": status,
            "response_time": response_time,
            "last_check": datetime.now().isoformat(),
            "uptime": round(random.uniform(100, 86400)) if status == "running" else 0
        })

    return statuses


def get_process_stats():
    """获取进程统计信息（前10个CPU使用率最高的进程）"""
    processes = []

    for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
        try:
            pinfo = proc.as_dict(attrs=['pid', 'name', 'username', 'cpu_percent', 'memory_percent'])
            processes.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass

    # 按CPU使用率排序并返回前10个
    processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
    return processes[:10]


# API路由
@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "monitoring-api"
    }), 200


@app.route('/api/system', methods=['GET'])
def system_info():
    """系统基本信息"""
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "data": get_system_info()
    }), 200


@app.route('/api/cpu', methods=['GET'])
def cpu_info():
    """CPU使用情况"""
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "data": get_cpu_usage()
    }), 200


@app.route('/api/memory', methods=['GET'])
def memory_info():
    """内存使用情况"""
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "data": get_memory_usage()
    }), 200


@app.route('/api/disk', methods=['GET'])
def disk_info():
    """磁盘使用情况"""
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "data": get_disk_usage()
    }), 200


@app.route('/api/network', methods=['GET'])
def network_info():
    """网络统计信息"""
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "data": get_network_stats()
    }), 200


@app.route('/api/services', methods=['GET'])
def service_info():
    """服务状态信息"""
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "data": get_service_status()
    }), 200


@app.route('/api/processes', methods=['GET'])
def process_info():
    """进程统计信息"""
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "data": get_process_stats()
    }), 200


@app.route('/api/all', methods=['GET'])
def all_info():
    """获取所有监控数据"""
    return jsonify({
        "timestamp": datetime.now().isoformat(),
        "data": {
            "system": get_system_info(),
            "cpu": get_cpu_usage(),
            "memory": get_memory_usage(),
            "disk": get_disk_usage(),
            "network": get_network_stats(),
            "services": get_service_status(),
            "processes": get_process_stats()
        }
    }), 200


if __name__ == '__main__':
    # 生产环境中应使用Gunicorn等WSGI服务器，此处仅为演示
    app.run(host='0.0.0.0', port=5000, debug=False)
