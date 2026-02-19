from flask import Flask, jsonify
import subprocess
import json
import re
from datetime import datetime
import time
import threading

app = Flask(__name__)
# 历史监控数据缓存（最多保留10条，按时间倒序）
monitoring_history = []
MAX_HISTORY = 10  # 最大历史记录数
COLLECT_INTERVAL = 600  # 自动采集间隔：10分钟（600秒），可修改


def run_monitoring_playbook():
    """执行监控playbook并提取数据（简化解析逻辑）"""
    try:
        result = subprocess.run(
            ['ansible-playbook', '-i', 'inventory/hosts.ini', 'api_return.yml'],
            capture_output=True,
            cwd='/home/admin/monitor-project',
            timeout=30
        )

        if result.returncode != 0:
            print(f"Playbook执行失败: {result.stderr.decode('utf-8', errors='ignore')}")
            return None

        # 简化解析：正则直接提取msg中的JSON
        output = result.stdout.decode('utf-8', errors='ignore')
        match = re.search(r'"msg"\s*:\s*"(\[.*?\])"', output, re.DOTALL)
        if not match:
            print("未找到msg字段中的JSON数据")
            return None

        json_str = match.group(1).replace('\\"', '"').replace('\\n', '')
        return json.loads(json_str)

    except Exception as e:
        print(f"执行/解析异常: {str(e)}")
        return None


def auto_collect_data():
    """定时自动采集数据（后台运行）"""
    while True:
        print(f"\n[{datetime.now().isoformat()}] 开始自动采集监控数据...")
        new_data = run_monitoring_playbook()

        if new_data:
            # 封装采集记录（含时间戳）
            current_record = {
                "timestamp": datetime.now().isoformat(),
                "data": new_data,
                "data_count": len(new_data)
            }
            # 存入历史缓存（最新数据放最前，超量则删除最早的）
            monitoring_history.insert(0, current_record)
            if len(monitoring_history) > MAX_HISTORY:
                monitoring_history.pop()
            print(f"采集成功！当前历史记录数：{len(monitoring_history)}")
        else:
            print("采集失败，跳过此次记录")

        # 等待下一个采集周期
        time.sleep(COLLECT_INTERVAL)


@app.route('/ceshi')
def get_metrics():
    """接口：返回所有自动采集的历史监控数据"""
    response = {
        "status": "success" if monitoring_history else "no_data",
        "history_count": len(monitoring_history),
        "max_history": MAX_HISTORY,
        "collect_interval": COLLECT_INTERVAL / 60,  # 显示为分钟
        "history_data": monitoring_history,  # 多个历史采集记录
        "query_time": datetime.now().isoformat()
    }
    return jsonify(response)


if __name__ == '__main__':
    # 启动后台定时采集线程（不阻塞Flask服务）
    collect_thread = threading.Thread(target=auto_collect_data, daemon=True)
    collect_thread.start()
    print(f"定时采集线程已启动，每{COLLECT_INTERVAL / 60}分钟采集一次")

    # 启动Flask服务
    app.run(debug=True, host='0.0.0.0', port=5001)