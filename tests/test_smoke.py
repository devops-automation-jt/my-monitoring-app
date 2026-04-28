# tests/test_smoke.py
# DevOps 冒烟测试：仅校验Flask服务能正常启动，无业务测试
def test_flask_startup():
    try:
        from app import app
        assert app is not None
        print(" Flask服务启动成功，无语法/依赖错误")
    except Exception as e:
        raise AssertionError(f" Flask服务启动失败：{str(e)}")