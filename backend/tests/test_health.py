"""SignalFlow 后端 - 测试骨架。

骨架阶段仅验证可启动性与健康检查；真实业务行为在后续切片补齐边界测试。
"""

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


def test_healthz() -> None:
    resp = client.get("/api/v1/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_root() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["service"] == "signalflow-backend"