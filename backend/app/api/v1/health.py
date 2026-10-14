"""SignalFlow 后端 - 健康检查接口。"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
def healthz() -> dict[str, str]:
    """服务存活探针（容器编排/负载均衡使用）。"""
    return {"status": "ok", "service": "signalflow-backend"}