"""SignalFlow 后端 - AI 自动化规则服务。

规则引擎：自动分类、去重建议、优先级调整记录、自动审批。
AI 相关能力（分类/去重/回复生成）通过注入的 ReplyGenerator 协议调用，
本层不直接 import litellm/langgraph。
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.exceptions import NotFoundError, ValidationError
from app.models.automation import (
    AutomationRule,
    ClassificationResult,
    DedupGroup,
    PriorityAdjustment,
)
from app.models.feedback import Feedback
from app.repositories.automation import (
    AutomationRuleRepository,
    ClassificationResultRepository,
    DedupGroupRepository,
    PriorityAdjustmentRepository,
)
from app.services.base import ReplyGenerator, ServiceBase
from sqlalchemy.orm import Session

# 关键词 → 主题映射（规则引擎的轻量实现，后续可替换为 Embedding 聚类）
# 注意：仅用于规则匹配测试与演示，真实分类由 LangGraph ClassifyNode 承担。
TOPIC_KEYWORDS: list[tuple[str, str]] = [
    ("排队", "窗口服务效率"),
    ("等候", "窗口服务效率"),
    ("叫号", "窗口服务效率"),
    ("材料", "材料提交与复用"),
    ("复印", "材料提交与复用"),
    ("重复", "重复提交"),
    ("预约", "预约与爽约管理"),
    ("爽约", "预约与爽约管理"),
    ("政策", "政策咨询"),
    ("医保", "医保与社保"),
    ("社保", "医保与社保"),
    ("态度", "服务态度"),
    ("闪退", "APP 稳定性"),
    ("app", "APP 稳定性"),
]

# 低置信度阈值：低于该值进入人工复核队列
REVIEW_CONFIDENCE_THRESHOLD = 0.6


class AutomationService(ServiceBase):
    """AI 自动化规则引擎服务。"""

    def __init__(
        self,
        session: Session,
        *,
        rule_repo: AutomationRuleRepository | None = None,
        classification_repo: ClassificationResultRepository | None = None,
        dedup_repo: DedupGroupRepository | None = None,
        adjustment_repo: PriorityAdjustmentRepository | None = None,
        reply_generator: ReplyGenerator | None = None,
    ) -> None:
        super().__init__(session)
        self._rules = rule_repo or AutomationRuleRepository(session)
        self._classifications = classification_repo or ClassificationResultRepository(session)
        self._dedup = dedup_repo or DedupGroupRepository(session)
        self._adjustments = adjustment_repo or PriorityAdjustmentRepository(session)
        self._reply_generator = reply_generator

    # ──────────────────────────────────────────────
    # 规则管理
    # ──────────────────────────────────────────────

    def list_rules(self) -> list[AutomationRule]:
        """返回全部自动化规则。"""
        return list(self._rules.list_all())  # type: ignore[arg-type]

    def toggle_rule(self, rule_id: str) -> AutomationRule:
        """切换规则启用状态。"""
        rule = self._rules.get_by_id(rule_id)
        if rule is None:
            raise NotFoundError(resource="自动化规则")
        rule.enabled = not rule.enabled
        self._commit()
        return rule

    # ──────────────────────────────────────────────
    # 自动分类
    # ──────────────────────────────────────────────

    def classify(self, feedback: Feedback) -> ClassificationResult:
        """基于关键词规则为反馈分配主题。

        规则：匹配到多个关键词时取置信度最高的主题；
        无匹配时标记 needs_review=True（人工复核队列）。
        """
        content = (feedback.content or "").lower()
        matches: list[tuple[str, float]] = []
        for keyword, topic in TOPIC_KEYWORDS:
            if keyword.lower() in content:
                confidence = min(0.99, 0.55 + content.count(keyword.lower()) * 0.1)
                matches.append((topic, round(confidence, 2)))
        if not matches:
            result = ClassificationResult(
                id=str(uuid.uuid4()),
                feedback_id=str(feedback.id),
                suggested_topic="待人工分类",
                confidence=0.0,
                alternatives=[],
                needs_review=True,
                processed_at=datetime.now(timezone.utc),
            )
        else:
            matches.sort(key=lambda m: m[1], reverse=True)
            suggested, confidence = matches[0]
            alternatives = [{"topic": t, "confidence": c} for t, c in matches[1:3]]
            result = ClassificationResult(
                id=str(uuid.uuid4()),
                feedback_id=str(feedback.id),
                suggested_topic=suggested,
                confidence=confidence,
                alternatives=alternatives,
                needs_review=confidence < REVIEW_CONFIDENCE_THRESHOLD,
                processed_at=datetime.now(timezone.utc),
            )
        self._classifications.create(result)
        self._commit()
        return result

    # ──────────────────────────────────────────────
    # 去重建议
    # ──────────────────────────────────────────────

    def suggest_dedup(self, feedback: Feedback, candidates: list[Feedback]) -> DedupGroup | None:
        """判断反馈是否与候选集重复。

        相似度采用简单词元交集（分词用正则），大于阈值 0.6 建议合并；
        相似度不足或候选为空时返回 None（不生成去重组）。
        """
        if not candidates:
            return None
        target_tokens = self._tokenize(feedback.content)
        if not target_tokens:
            return None
        best: tuple[Feedback, float] | None = None
        for candidate in candidates:
            candidate_tokens = self._tokenize(candidate.content)
            if not candidate_tokens:
                continue
            overlap = len(target_tokens & candidate_tokens)
            similarity = overlap / min(len(target_tokens), len(candidate_tokens))
            if best is None or similarity > best[1]:
                best = (candidate, similarity)
        if best is None or best[1] < 0.6:
            return None

        group = DedupGroup(
            id=str(uuid.uuid4()),
            representative_id=str(best[0].id),
            members=[
                {
                    "feedback_id": str(best[0].id),
                    "content": best[0].content[:120],
                    "similarity": round(best[1], 2),
                }
            ],
            status="pending",
            repeat_count=2,
        )
        self._dedup.create(group)
        self._commit()
        return group

    @staticmethod
    def _tokenize(content: str | None) -> set[str]:
        """极简中文分词：按字 bigram 构造词元集合。"""
        text = re.sub(r"\s+", "", content or "")
        if len(text) < 2:
            return {text} if text else set()
        return {text[i : i + 2] for i in range(len(text) - 1)}

    # ──────────────────────────────────────────────
    # 优先级调整记录
    # ──────────────────────────────────────────────

    def record_priority_adjustment(
        self,
        *,
        feedback_id: str,
        old_priority: int,
        new_priority: int,
        reason: str | None = None,
        triggered_by: str | None = None,
    ) -> PriorityAdjustment:
        """记录一次优先级调整（审计留痕）。"""
        if new_priority < 0 or new_priority > 100:
            raise ValidationError(detail="优先级必须在 0-100 之间")
        adjustment = PriorityAdjustment(
            id=str(uuid.uuid4()),
            feedback_id=feedback_id,
            old_priority=old_priority,
            new_priority=new_priority,
            reason=reason,
            triggered_by=triggered_by,
            adjusted_at=datetime.now(timezone.utc),
        )
        self._adjustments.create(adjustment)
        self._commit()
        return adjustment

    # ──────────────────────────────────────────────
    # 自动审批 / 回复
    # ──────────────────────────────────────────────

    def auto_reply(self, feedback: Feedback) -> str | None:
        """基于反馈内容生成 AI 回复草稿。

        依赖注入的 ReplyGenerator（阶段 3 为 llm/gateway.py 的 LLMGateway 适配）；
        未注入生成器时返回 None（跳过自动回复）。
        """
        if self._reply_generator is None:
            return None
        return self._reply_generator.generate_reply(feedback.content)