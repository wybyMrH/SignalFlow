"""SignalFlow 后端 - 客户访谈服务。

访谈生命周期：scheduled（已预约）→ recorded（已完成记录）→ extracted（AI 已提炼）→ linked（已联动）。
跨 Domain 编排：访谈 AI 提炼结论中 lead_candidate=True 时，
自动调用 BusinessService 生成商务线索并回填 linked_lead_id（同一事务）。
AI 提炼本身的调用在阶段 3 通过 llm/gateway.py 抽象接口接入。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import NotFoundError, ValidationError
from app.models.interview import InterviewRecord
from app.repositories.interview import InterviewRecordRepository
from app.services.base import ServiceBase
from app.services.business import BusinessService
from sqlalchemy.orm import Session

# 合法访谈状态迁移
INTERVIEW_STATUS_FLOW: dict[str, set[str]] = {
    "scheduled": {"recorded", "cancelled"},
    "recorded": {"extracted", "cancelled"},
    "extracted": {"linked"},
    "linked": set(),
    "cancelled": set(),
}


class InterviewService(ServiceBase):
    """客户访谈业务服务（含线索生成编排）。"""

    def __init__(
        self,
        session: Session,
        *,
        repo: InterviewRecordRepository | None = None,
        business_service: BusinessService | None = None,
    ) -> None:
        super().__init__(session)
        self._repo = repo or InterviewRecordRepository(session)
        self._business = business_service or BusinessService(session)

    # ──────────────────────────────────────────────
    # 基础管理
    # ──────────────────────────────────────────────

    def create(self, data: dict[str, Any]) -> InterviewRecord:
        """创建访谈记录（初始状态 scheduled）。"""
        record = InterviewRecord(
            id=str(uuid.uuid4()),
            company_name=str(data.get("company_name", "")),
            company_type=data.get("company_type"),
            industry=data.get("industry"),
            contact_name=data.get("contact_name"),
            contact_role=data.get("contact_role"),
            interview_date=data.get("interview_date"),
            duration_min=int(data.get("duration_min", 0)),
            source=data.get("source"),
            status="scheduled",
            summary=data.get("summary"),
            key_points=data.get("key_points") or [],
            linked_feedback_ids=data.get("linked_feedback_ids") or [],
            recorder=data.get("recorder"),
        )
        if not record.company_name:
            raise ValidationError(detail="访谈公司名称不能为空")
        self._repo.create(record)
        self._commit()
        return record

    def get(self, interview_id: str) -> InterviewRecord:
        """按主键读取访谈，不存在时抛 NotFoundError。"""
        record = self._repo.get_by_id(interview_id)
        if record is None:
            raise NotFoundError(resource="客户访谈")
        return record

    def list(self) -> list[InterviewRecord]:
        """返回全部访谈记录（按访谈日期倒序）。"""
        return sorted(
            self._repo.list_all(),  # type: ignore[arg-type]
            key=lambda r: r.interview_date or r.created_at,
            reverse=True,
        )

    def change_status(self, interview_id: str, new_status: str) -> InterviewRecord:
        """按状态机流转访谈状态。"""
        record = self.get(interview_id)
        allowed = INTERVIEW_STATUS_FLOW.get(record.status, set())
        if new_status not in allowed:
            raise ValidationError(
                detail=f"非法状态流转：{record.status} → {new_status}",
                errors=[
                    {
                        "field": "status",
                        "message": f"{record.status} 只能流转到 {sorted(allowed)}",
                    }
                ],
            )
        record.status = new_status
        self._commit()
        return record

    # ──────────────────────────────────────────────
    # AI 提炼 + 线索联动（跨 Domain 编排）
    # ──────────────────────────────────────────────

    def run_extraction(self, interview_id: str, extraction: dict[str, Any]) -> InterviewRecord:
        """保存 AI 提炼结论到访谈记录（幂等，可安全重试）。

        提炼成功后：
        1. 状态流转 recorded → extracted；
        2. 若 extraction.lead_candidate=True 且尚未关联线索，
           则生成商务线索并回填 linked_lead_id，状态流转 extracted → linked；
        3. 已处于 extracted/linked 的访谈再次提炼不报错：
           - extracted 时若发现 lead_candidate=True 且尚未关联线索，补齐线索联动；
           - linked 时保持 linked，不重复生成线索（BusinessService 幂等兜底）。
        scheduled / cancelled 状态不允许提炼，抛 ValidationError。
        """
        record = self.get(interview_id)
        if record.status not in {"recorded", "extracted", "linked"}:
            raise ValidationError(
                detail=f"当前状态 {record.status} 不支持 AI 提炼，需先完成访谈记录"
            )

        extraction["extracted_at"] = datetime.now(timezone.utc).isoformat()
        record.extraction = extraction
        if record.status == "recorded":
            record.status = "extracted"

        if (
            record.status != "linked"
            and extraction.get("lead_candidate")
            and not record.linked_lead_id
        ):
            lead = self._business.create_lead_from_interview(record, extraction)
            record.linked_lead_id = lead.id
            record.status = "linked"
        self._commit()
        return record

    def link_to_feedback(self, interview_id: str, feedback_id: str) -> InterviewRecord:
        """关联反馈记录到访谈（联动证据链）。"""
        record = self.get(interview_id)
        linked = list(record.linked_feedback_ids or [])
        if feedback_id not in linked:
            linked.append(feedback_id)
        record.linked_feedback_ids = linked
        self._commit()
        return record

    def summary(self) -> dict[str, Any]:
        """访谈统计：总数 / 各状态数量 / 线索候选数 / 已生成线索数。"""
        records = self.list()
        return {
            "total": len(records),
            "scheduled": sum(1 for r in records if r.status == "scheduled"),
            "recorded": sum(1 for r in records if r.status == "recorded"),
            "extracted": sum(1 for r in records if r.status in {"extracted", "linked"}),
            "pending_extraction": sum(1 for r in records if r.status == "recorded"),
            "lead_candidates": sum(
                1 for r in records if (r.extraction or {}).get("lead_candidate")
            ),
            "generated_leads": sum(1 for r in records if r.linked_lead_id),
            "matched_needs_count": len(
                {
                    need
                    for r in records
                    for need in (r.extraction or {}).get("matched_needs", [])
                }
            ),
            "total_duration_min": sum(r.duration_min for r in records),
        }