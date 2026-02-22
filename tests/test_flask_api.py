# tests/test_flask_api.py
import requests

def test_metrics_api():
    """测试Flask的/metrics接口是否正常返回"""
    try:
        resp = requests.get("http://127.0.0.1:5000/metrics")
        assert resp.status_code == 200
        print("Flask metrics接口正常！")
    except Exception as e:
        print(f"接口异常：{e}")

if __name__ == "__main__":
    test_metrics_api()