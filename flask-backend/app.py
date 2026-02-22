import subprocess
import re
import json
import chardet
from flask import Flask, Response
from prometheus_client import Gauge, generate_latest


app = Flask(__name__)


# 定义Gauge指标
disk_gauge = Gauge('host_disk_usage', '主机磁盘使用率', ['hostname'])
mem_gauge = Gauge('host_memory_usage', '主机内存使用率', ['hostname'])
cpu_gauge = Gauge('host_cpu_usage', '主机CPU使用率', ['hostname'])
load_gauge = Gauge('host_load_1min', '主机1分钟负载', ['hostname'])


def run_ansible_task():
    """执行ansible任务，返回原始字节流"""
    try:
        result = subprocess.run(
            [
                '/home/admin/monitor_project/ci_cd_env/bin/ansible-playbook',
                '-i', 'inventory/hosts.ini',
                'api_return.yml'
            ],
            capture_output=True,
            cwd='/home/admin/monitor_project',
            timeout=30
        )
        return True, result.stdout, result.stderr
    except Exception as e:
        return False, b'', str(e).encode('utf-8')


#返回原始JSON数据
def get_raw_monitor_data():
    """返回原始的Python列表/字典（不是Response），供Prometheus解析"""
    success, stdout_bytes, stderr_bytes = run_ansible_task()
    if not success:
        return []

    # 编码识别和解码
    stdout_encoding = chardet.detect(stdout_bytes)['encoding'] or 'utf-8'
    stdout_str = stdout_bytes.decode(stdout_encoding, errors='ignore')

    # 提取JSON字符串
    json_match = re.search(r'msg": "(\[.*?])"', stdout_str)
    if not json_match:
        return []

    # 解析JSON字符串为Python列表
    try:
        pure_json = json_match.group(1)
        pure_json_clean = pure_json.replace('\\', '')
        result=json.loads(pure_json_clean)
        return result# 返回Python列表（可遍历）
    except json.JSONDecodeError:
        return []

#修饰为Response（供flask服务封装）
def get_monitor_data():
    """返回Flask Response（供/monitor-data接口）"""
    raw_data = get_raw_monitor_data()
    if raw_data:
        return Response(json.dumps(raw_data), mimetype='application/json; charset=utf-8')
    else:
        success, stdout_bytes, stderr_bytes = run_ansible_task()
        stdout_encoding = chardet.detect(stdout_bytes)['encoding'] or 'utf-8'
        stdout_str = stdout_bytes.decode(stdout_encoding, errors='ignore')
        stderr_encoding = chardet.detect(stderr_bytes)['encoding'] or 'utf-8'
        stderr_str = stderr_bytes.decode(stderr_encoding, errors='ignore')
        response = f"=== 收集失败 ===\nstdout: {stdout_str}\nstderr: {stderr_str}"
        return Response(response, mimetype='text/plain; charset=utf-8')


#数据Prometheus化（供Prometheus解析）
def data_prmetheus():
    # 获取原始Python列表
    mock_host_metrics = get_raw_monitor_data()
    if not mock_host_metrics:
        return "暂无监控数据"

    # 遍历数据赋值给指标
    for host in mock_host_metrics:
        hostname = host.get("hostname")
        if not hostname:
            continue  # 主机名为空则跳过
        # 提取数值并转浮点数，加异常处理
        try:
            disk_usage = float(host.get("disk_usage", 0))
            mem_usage = float(host.get("memory_usage", 0))
            cpu_usage = float(host.get("cpu_usage", 0))
            load_1min = float(host.get("load_1min", 0))
        except ValueError:
            continue  # 数值转换失败则跳过

        # 赋值给指标
        disk_gauge.labels(hostname=hostname).set(disk_usage)
        mem_gauge.labels(hostname=hostname).set(mem_usage)
        cpu_gauge.labels(hostname=hostname).set(cpu_usage)
        load_gauge.labels(hostname=hostname).set(load_1min)

    # 生成Prometheus格式文本
    prom_text = generate_latest().decode("utf-8")
    return prom_text


#新增Prometheus采集的核心接口
@app.route('/metrics')
def prometheus_metrics():
    prom_data = data_prmetheus()
    return Response(prom_data, mimetype='text/plain; charset=utf-8')


@app.route('/')
def index():
    return '成功部署到云服务器\n\n访问 /monitor-data 查看监控数据\n访问 /metrics 查看Prometheus格式数据'


@app.route('/monitor-data')
def print_monitor_data():
    return get_monitor_data()


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=False,
        threaded=False
    )