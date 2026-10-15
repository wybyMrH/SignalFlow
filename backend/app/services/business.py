"""SignalFlow 后端 - 商务线索服务。

线索生命周期：identified（识别）→ qualified（确认）→ pushed（推送销售/CSM）。
线索来源：客户访谈 AI 提炼（InterviewService 编排调用）与反馈语义匹配。
匹配评分规则集中在 compute_match_* 纯函数，便于单元测试。
"""

from __future__ import annotations

import uuid
from typing import Any

from app.core.exceptions import NotFoundError, ValidationError
from app.models.business import BusinessLead
from app.models.interview import InterviewRecord
from app.repositories.business import BusinessLeadRepository
from app.services.base import ServiceBase
from sqlalchemy.orm import Session

# 合法线索阶段迁移
LEAD_STAGE_FLOW: dict[str, set[str]] = {
    "identified": {"qualified", "pushed", "lost"},
    "qualified": {"pushed", "lost"},
    "pushed": {"lost"},
    "lost": set(),
}

# 合作意向 → (客户价值, 置信度) 映射（可配置化前的规则默认值）
INTENT_TO_SCORE: dict[str, tuple[int, int]] = {
    "high": (85, 85),
    "medium": (60, 60),
    "low": (30, 30),
}


class BusinessService(ServiceBase):
    """商务线索业务服务。"""

    def __init__(
        self,
        session: Session,
        *,
        repo: BusinessLeadRepository | None = None,
    ) -> None:
        super().__init__(session)
        self._repo = repo or BusinessLeadRepository(session)

    # ──────────────────────────────────────────────
    # 匹配评分（纯函数）
    # ──────────────────────────────────────────────

    @staticmethod
    def compute_match_score(
        *,
        matched_needs: int,
        feedback_count: int = 0,
        cooperation: str = "medium",
    ) -> tuple[int, int]:
        """计算线索的价值分数与置信度。

        规则：
        - 价值：以匹配需求数为锚（每项 +25，最高 90）；
          反馈佐证每 1 条 +2，封顶 +10。
        - 置信度：以合作意向为基础（high 85 / medium 60 / low 30）；
          反馈佐证每 5 条 +5，封顶 +15。
        - 两者各自封顶，最高 100。
        """
        value = min(90, matched_needs * 25) + min(10, feedback_count * 2)
        base = INTENT_TO_SCORE.get(cooperation, (60, 60))[1]
        confidence = min(100, base + min(15, feedback_count // 5 * 5))
        return value, confidence

    @staticmethod
    def _stage_valid(current: str, target: str) -> bool:
        return target in LEAD_STAGE_FLOW.get(current, set())

    # ──────────────────────────────────────────────
    # 线索创建（跨 Domain：访谈 → 线索）
    # ──────────────────────────────────────────────

    def create_lead_from_interview(
        self,
        record: InterviewRecord,
        extraction: dict[str, Any],
    ) -> BusinessLead:
        """从访谈提炼结论生成商务线索。

        - 若该访谈已关联线索，则直接返回已有线索（幂等，避免重复生成）。
        - 仅当 lead_candidate=True 时创建；否则抛 ValidationError。
        """
        if record.linked_lead_id:
            existing = self._repo.get_by_id(record.linked_lead_id)
            if existing is not None:
                return existing
        if not extraction.get("lead_candidate"):
            raise ValidationError(detail="该访谈未识别出商务线索候选，无需生成")

        matched_needs = extraction.get("matched_needs") or []
        value_score, confidence = self.compute_match_score(
            matched_needs=len(matched_needs),
            cooperation=str(extraction.get("cooperation_intent", "medium")),
        )

        lead = self._repo.create(
            BusinessLead(
                id=str(uuid.uuid4()),
                feedback_id=str(getattr(record, "linked_feedback_ids", [])[0])
                if getattr(record, "linked_feedback_ids", [])
                else "",
                content=record.summary or "",
                company_name=record.company_name,
                industry=record.industry or "",
                company_type=record.company_type or "",
                size_band="",
                matched_product=matched_needs[0] if matched_needs else "综合解决方案",
                match_reason=str(extraction.get("lead_reason", "")),
                value_score=value_score,
                confidence=confidence,
                stage="identified",
            )
        )
        self._commit()
        return lead

    # ──────────────────────────────────────────────
    # 线索生命周期
    # ──────────────────────────────────────────────

    def get(self, lead_id: str) -> BusinessLead:
        """按主键读取线索，不存在时抛 NotFoundError。"""
        lead = self._repo.get_by_id(lead_id)
        if lead is None:
            raise NotFoundError(resource="商务线索")
        return lead

    def list(self) -> list[BusinessLead]:
        """返回全部线索（按创建时间倒序）。"""
        return sorted(
            self._repo.list_all(),  # type: ignore[arg-type]
            key=lambda lead: lead.created_at,
            reverse=True,
        )

    def update_stage(self, lead_id: str, new_stage: str) -> BusinessLead:
        """按生命周期校验并流转线索阶段。"""
        lead = self.get(lead_id)
        if not self._stage_valid(lead.stage, new_stage):
            raise ValidationError(
                detail=f"非法阶段流转：{lead.stage} → {new_stage}",
                errors=[
                    {
                        "field": "stage",
                        "message": f"{lead.stage} 只能流转到 {sorted(LEAD_STAGE_FLOW.get(lead.stage, set()))}",
                    }
                ],
            )
        lead.stage = new_stage
        self._commit()
        return lead

    def summary(self) -> dict[str, Any]:
        """线索总览统计：总数 / 已确认 / 已推送 / 行业数。"""
        leads = self.list()
        industries = {lead.industry for lead in leads if lead.industry}
        return {
            "total_leads": len(leads),
            "qualified_leads": sum(1 for lead in leads if lead.stage == "qualified"),
            "pushed_leads": sum(1 for lead in leads if lead.stage == "pushed"),
            "industry_count": len(industries),
        }