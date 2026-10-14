"""SignalFlow 后端 - 洞察接口。

骨架阶段：返回空洞察列表，展示"分析结果读取面"的契约；
真实洞察由 LangGraph 工作流产出后由服务层回填。
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("")
def list_insights() -> dict:
    """洞察看板数据（主题/痛点/趋势/预警）——骨架占位。"""
    return {"items": [], "total": 0, "skeleton": True}