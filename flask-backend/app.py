import subprocess
import re
import json
import chardet
from flask import Flask, Response
from prometheus_client import Gauge, generate_latest
import os
# 1. 导入日志库
import logging

# ===================== 日志配置（核心） =====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
# 获取日志对象
logger = logging.getLogger(__name__)

# ============================================================

app = Flask(__name__)

# 定义Gauge指标
disk_gauge = Gauge('host_disk_usage', '主机磁盘使用率', ['hostname'])
mem_gauge = Gauge('host_memory_usage', '主机内存使用率', ['hostname'])
cpu_gauge = Gauge('host_cpu_usage', '主机CPU使用率', ['hostname'])
load_gauge = Gauge('host_load_1min', '主机1分钟负载', ['hostname'])


def run_ansible_task():
    """执行ansible任务，返回原始字节流"""
    try:
        logger.info("开始执行 Ansible 剧本：multiple_date.yml")
        result = subprocess.run(
            [
                '/usr/local/bin/ansible-playbook',
                '-i', 'inventory/hosts.ini',
                'multiple_date.yml'
            ],
            capture_output=True,
            cwd='/app/ansible',
            timeout=30
        )
        logger.info(f"Ansible 执行完成，返回码: {result.returncode}")
        return True, result.stdout, result.stderr
    except Exception as e:
        logger.error(f"Ansible 执行异常: {str(e)}", exc_info=True)
        return False, b'', str(e).encode('utf-8')


def get_raw_monitor_data():
    """返回原始的Python列表/字典（不是Response），供Prometheus解析"""
    success, stdout_bytes, stderr_bytes = run_ansible_task()
    if not success:
        logger.error("Ansible 任务执行失败")
        return []

    # 编码识别和解码
    stdout_encoding = chardet.detect(stdout_bytes)['encoding'] or 'utf-8'
    stdout_str = stdout_bytes.decode(stdout_encoding, errors='ignore')
    logger.debug(f"Ansible 原始输出: {stdout_str[:500]}...")  # 只打印前500字符，避免日志过长

    # 提取JSON字符串
    json_match = re.search(r'msg": "(\[.*?])"', stdout_str)
    if not json_match:
        logger.warning("未从 Ansible 输出中匹配到 JSON 数据")
        return []

    # 解析JSON字符串为Python列表
    try:
        pure_json = json_match.group(1)
        pure_json_clean = pure_json.replace('\\', '')
        result = json.loads(pure_json_clean)
        logger.info(f"成功解析监控数据，主机数量: {len(result)}")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析失败: {str(e)}")
        return []


def get_monitor_data():
    """返回Flask Response（供/monitor-data接口）"""
    raw_data = get_raw_monitor_data()
    if raw_data:
        logger.info("接口 /monitor-data 返回正常监控数据")
        return Response(json.dumps(raw_data), mimetype='application/json; charset=utf-8')
    else:
        logger.error("接口 /monitor-data 数据收集失败")
        success, stdout_bytes, stderr_bytes = run_ansible_task()
        stdout_encoding = chardet.detect(stdout_bytes)['encoding'] or 'utf-8'
        stdout_str = stdout_bytes.decode(stdout_encoding, errors='ignore')
        stderr_encoding = chardet.detect(stderr_bytes)['encoding'] or 'utf-8'
        stderr_str = stderr_bytes.decode(stderr_encoding, errors='ignore')
        response = f"=== 收集失败 ===\nstdout: {stdout_str}\nstderr: {stderr_str}"
        return Response(response, mimetype='text/plain; charset=utf-8')


def data_prmetheus():
    # 获取原始Python列表
    mock_host_metrics = get_raw_monitor_data()
    if not mock_host_metrics:
        logger.warning("Prometheus 无监控数据可更新")
        return "暂无监控数据"

    # 遍历数据赋值给指标
    success_count = 0
    for host in mock_host_metrics:
        hostname = host.get("hostname")
        if not hostname:
            logger.warning("发现空主机名，跳过")
            continue
        # 提取数值并转浮点数，加异常处理
        try:
            disk_usage = float(host.get("disk_usage", 0))
            mem_usage = float(host.get("memory_usage", 0))
            cpu_usage = float(host.get("cpu_usage", 0))
            load_1min = float(host.get("load_1min", 0))
        except ValueError:
            logger.warning(f"主机 {hostname} 数据格式错误，跳过")
            continue

        # 赋值给指标
        disk_gauge.labels(hostname=hostname).set(disk_usage)
        mem_gauge.labels(hostname=hostname).set(mem_usage)
        cpu_gauge.labels(hostname=hostname).set(cpu_usage)
        load_gauge.labels(hostname=hostname).set(load_1min)
        success_count += 1

    logger.info(f"Prometheus 指标更新完成，成功更新主机数: {success_count}")
    # 生成Prometheus格式文本
    prom_text = generate_latest().decode("utf-8")
    return prom_text


@app.route('/metrics')
def prometheus_metrics():
    logger.info("收到 Prometheus 指标采集请求")
    prom_data = data_prmetheus()
    return Response(prom_data, mimetype='text/plain; charset=utf-8')


@app.route('/')
def index():
    logger.info("访问首页 /")
    return '成功部署到云服务器\n\n访问 /monitor-data 查看监控数据\n访问 /metrics 查看Prometheus格式数据'


@app.route('/monitor-data')
def print_monitor_data():
    return get_monitor_data()


if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info(f"Flask 服务启动，端口: {os.getenv('APP_PORT', 8080)}")
    logger.info("=" * 50)
    app.run(
        host='0.0.0.0',
        port=int(os.getenv("APP_PORT", 8080)),
        debug=False,
        threaded=False
    )