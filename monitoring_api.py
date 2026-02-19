import subprocess
import re
import chardet  # 自动识别编码（只需要装一次）
from flask import Flask, Response

app = Flask(__name__)


def run_ansible_task():
    """执行ansible任务，不强制编码，只拿原始字节流"""
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
            # 完全不指定编码，保留原始字节流（管它是GBK还是UTF-8）
        )
        return True, result.stdout, result.stderr
    except Exception as e:
        return False, b'', str(e).encode('utf-8')


@app.route('/')
def index():
    return '成功部署到云服务器\n\n访问 /monitor-data 查看监控数据'


@app.route('/monitor-data')
def get_monitor_data():
    success, stdout_bytes, stderr_bytes = run_ansible_task()

    # 核心优化：自动识别编码（不管是GBK还是UTF-8，都能正确解码）
    # 1. 识别stdout编码
    stdout_encoding = chardet.detect(stdout_bytes)['encoding'] or 'utf-8'
    # 2. 解码（无法解码的字符忽略，不影响核心数据）
    stdout_str = stdout_bytes.decode(stdout_encoding, errors='ignore')

    #  stderr同理（错误信息也可能是GBK）
    stderr_encoding = chardet.detect(stderr_bytes)['encoding'] or 'utf-8'
    stderr_str = stderr_bytes.decode(stderr_encoding, errors='ignore')

    # 提取纯净JSON（和之前一样）
    json_match = re.search(r'msg": "(\[.*?\])"', stdout_str)
    if json_match and success:
        pure_json = json_match.group(1)
        return Response(pure_json, mimetype='application/json; charset=utf-8')
    else:
        response = f"=== 收集失败 ===\nstdout: {stdout_str}\nstderr: {stderr_str}"
        return Response(response, mimetype='text/plain; charset=utf-8')


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8080,
        debug=False,
        threaded=True
    )