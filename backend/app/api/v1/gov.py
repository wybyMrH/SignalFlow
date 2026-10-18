"""SignalFlow 后端 - 政务适配接口。

提供政务总览（诉求分级 / 热点主题 / 舆情预警 / 政策告知），对齐前端 GovOverview 契约。
"""

from app.core.database import get_db
from app.services.gov import GovService
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

router = APIRouter()


def _service(db: Session = Depends(get_db)) -> GovService:
    return GovService(db)


@router.get("/overview")
def get_gov_overview(service=Depends(_service)) -> dict:
    """政务适配总览。"""
    return service.overview()