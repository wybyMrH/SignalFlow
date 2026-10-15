"""SignalFlow 后端 - 跨 Domain 编排与其余 Service 单元测试。

覆盖编排链路（Interview→BusinessLead、Feedback→Insight、Gov→Insight、
Roadmap→Insight、Workflow/Agent 互相校验）及 Automation/Resource 规则引擎。
全部使用内存 mock，不依赖数据库。
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.models.agent import Agent, Skill
from app.models.automation import ClassificationResult, DedupGroup, PriorityAdjustment
from app.models.business import BusinessLead
from app.models.feedback import Feedback
from app.models.gov import GovAlertItem
from app.models.insight import InsightTopic
from app.models.interview import InterviewRecord
from app.models.roadmap import RoadmapItem, TaskItem
from app.models.setting import Setting
from app.models.workflow import Workflow, WorkflowRun
from app.services.agents import AgentService
from app.services.automation import AutomationService
from app.services.base import ReplyGenerator
from app.services.business import INTENT_TO_SCORE, BusinessService
from app.services.gov import GOV_ALERT_PRIORITY_THRESHOLD, GovService
from app.services.insight import InsightService
from app.services.interview import InterviewService
from app.services.resources import ResourceService
from app.services.roadmap import RoadmapService
from app.services.workflows import VALID_NODE_TYPES, WorkflowService
from tests.mocks import FakeSession, MemoryRepo


# ──────────────────────────────────────────────
# 构造辅助
# ──────────────────────────────────────────────

def make_feedback(
    *,
    content: str = "大厅排队等待时间太长",
    author: str = "客户A",
    source: str = "hotline",
) -> Feedback:
    return Feedback(
        id=uuid.uuid4(),
        tenant_id="default",
        source=source,
        content=content,
        author=author,
        status="new",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def make_topic(title: str = "窗口服务效率", priority: int = 80) -> InsightTopic:
    return InsightTopic(
        id=str(uuid.uuid4()),
        title=title,
        priority_score=priority,
        strength=priority,
        feedback_count=4,
        customer_count=2,
        trend="up",
    )


def make_interview(
    *,
    status: str = "recorded",
    summary: str = "客户提到窗口排队时间长",
    linked_lead_id: str | None = None,
) -> InterviewRecord:
    return InterviewRecord(
        id=str(uuid.uuid4()),
        company_name="中科软联",
        company_type="金融科技",
        industry="软件服务",
        contact_name="张经理",
        contact_role="IT 总监",
        interview_date=datetime.now(timezone.utc),
        duration_min=45,
        source="sales_call",
        status=status,
        summary=summary,
        key_points=["排队时间长", "希望整合工单系统"],
        linked_feedback_ids=["fb-1"],
        linked_lead_id=linked_lead_id,
        recorder="李顾问",
    )


def make_agent(*, enabled: bool = True, reliability: int = 50) -> Agent:
    return Agent(
        id=str(uuid.uuid4()),
        name="分类助手",
        category="prebuilt",
        enabled=enabled,
        tools=[{"key": "search_kb", "name": "知识库检索"}],
        run_count=0,
        reliability=reliability,
        preset=True,
    )


# ──────────────────────────────────────────────
# Interview → BusinessLead 联动（跨 Domain 编排）
# ──────────────────────────────────────────────

class TestInterviewBusinessOrchestration:
    def test_run_extraction_generates_lead_and_links(self) -> None:
        session = FakeSession()
        interview_repo = MemoryRepo([make_interview()])
        lead_repo = MemoryRepo()
        business = BusinessService(session, repo=lead_repo)  # type: ignore[arg-type]
        service = InterviewService(session, repo=interview_repo, business_service=business)  # type: ignore[arg-type]

        extraction = {
            "lead_candidate": True,
            "matched_needs": ["排队叫号优化", "工单系统集成"],
            "cooperation_intent": "high",
            "lead_reason": "有明确立项计划",
        }
        record = service.run_extraction(interview_repo.list_all()[0].id, extraction)

        assert record.status == "linked"
        assert record.linked_lead_id is not None
        leads = lead_repo.list_all()
        assert len(leads) == 1
        lead = leads[0]
        assert isinstance(lead, BusinessLead)
        assert lead.stage == "identified"
        assert lead.company_name == "中科软联"
        # high 意向 → (85, 85) 基础；2 个匹配需求 → value=min(90, 50)+0=50
        assert lead.value_score == 50
        assert lead.confidence == INTENT_TO_SCORE["high"][1]
        assert lead.matched_product == "排队叫号优化"

    def test_run_extraction_is_idempotent(self) -> None:
        session = FakeSession()
        existing_lead = BusinessLead(
            id=str(uuid.uuid4()),
            feedback_id="fb-1",
            content="旧线索",
            company_name="中科软联",
            stage="identified",
        )
        interview_repo = MemoryRepo(
            [make_interview(status="linked", linked_lead_id=existing_lead.id)]
        )
        lead_repo = MemoryRepo([existing_lead])
        business = BusinessService(session, repo=lead_repo)  # type: ignore[arg-type]
        service = InterviewService(session, repo=interview_repo, business_service=business)  # type: ignore[arg-type]

        extraction = {"lead_candidate": True, "matched_needs": ["排队叫号优化"]}
        record = service.run_extraction(interview_repo.list_all()[0].id, extraction)

        assert record.linked_lead_id == existing_lead.id
        assert len(lead_repo.list_all()) == 1  # 不重复生成

    def test_run_extraction_without_candidate_stays_extracted(self) -> None:
        session = FakeSession()
        interview_repo = MemoryRepo([make_interview()])
        lead_repo = MemoryRepo()
        business = BusinessService(session, repo=lead_repo)  # type: ignore[arg-type]
        service = InterviewService(session, repo=interview_repo, business_service=business)  # type: ignore[arg-type]

        record = service.run_extraction(
            interview_repo.list_all()[0].id, {"lead_candidate": False, "matched_needs": []}
        )

        assert record.status == "extracted"
        assert lead_repo.list_all() == []

    def test_run_extraction_rejects_wrong_status(self) -> None:
        session = FakeSession()
        interview_repo = MemoryRepo([make_interview(status="scheduled")])
        business = BusinessService(session)  # type: ignore[arg-type]
        service = InterviewService(session, repo=interview_repo, business_service=business)  # type: ignore[arg-type]

        with pytest.raises(ValidationError):
            service.run_extraction(interview_repo.list_all()[0].id, {"lead_candidate": False})

    def test_create_interview_requires_company_name(self) -> None:
        session = FakeSession()
        service = InterviewService(session, repo=MemoryRepo())  # type: ignore[arg-type]
        with pytest.raises(ValidationError):
            service.create({"company_name": ""})

    def test_interview_status_machine(self) -> None:
        session = FakeSession()
        interview_repo = MemoryRepo([make_interview(status="recorded")])
        service = InterviewService(session, repo=interview_repo)  # type: ignore[arg-type]
        record = service.change_status(interview_repo.list_all()[0].id, "extracted")
        assert record.status == "extracted"
        with pytest.raises(ValidationError):
            service.change_status(interview_repo.list_all()[0].id, "scheduled")


class TestBusinessService:
    def test_compute_match_score_rules(self) -> None:
        # 4 个匹配需求 → min(90, 100) + 0 = 90（封顶后保持 90）
        value, confidence = BusinessService.compute_match_score(
            matched_needs=4, cooperation="high"
        )
        assert value == 90
        assert confidence == 85
        # low 意向 + 少量反馈佐证
        value2, confidence2 = BusinessService.compute_match_score(
            matched_needs=1, feedback_count=6, cooperation="low"
        )
        assert value2 == 35  # 25 + 10（反馈佐证封顶）
        assert confidence2 == 35  # 30 + 5

    def test_update_stage_validation(self) -> None:
        session = FakeSession()
        lead = BusinessLead(
            id=str(uuid.uuid4()),
            feedback_id="fb-1",
            content="线索",
            company_name="公司",
            stage="identified",
        )
        service = BusinessService(session, repo=MemoryRepo([lead]))  # type: ignore[arg-type]
        assert service.update_stage(lead.id, "qualified").stage == "qualified"
        with pytest.raises(ValidationError):
            service.update_stage(lead.id, "qualified")  # qualified → qualified 非法

    def test_summary(self) -> None:
        session = FakeSession()
        now = datetime.now(timezone.utc)
        leads = [
            BusinessLead(id=str(uuid.uuid4()), feedback_id="1", content="a", company_name="A", industry="软件", stage="identified", created_at=now),
            BusinessLead(id=str(uuid.uuid4()), feedback_id="2", content="b", company_name="B", industry="制造", stage="pushed", created_at=now),
        ]
        service = BusinessService(session, repo=MemoryRepo(leads))  # type: ignore[arg-type]
        summary = service.summary()
        assert summary["total_leads"] == 2
        assert summary["pushed_leads"] == 1
        assert summary["industry_count"] == 2


# ──────────────────────────────────────────────
# Feedback → Insight 聚合
# ──────────────────────────────────────────────

class TestFeedbackInsightAggregation:
    def test_aggregate_creates_topic(self) -> None:
        session = FakeSession()
        topic_repo = MemoryRepo()
        service = InsightService(session, repo=topic_repo)  # type: ignore[arg-type]
        feedbacks = [
            make_feedback(content="排队太久", author="甲"),
            make_feedback(content="叫号等待长", author="甲"),
            make_feedback(content="窗口太少", author="乙"),
        ]

        topic = service.aggregate_feedback("窗口服务效率", feedbacks, sentiment="negative")

        assert topic.title == "窗口服务效率"
        assert topic.feedback_count == 3
        assert topic.customer_count == 2
        # strength = 3*20 + 2*5 = 70；negative 加成 15 → 85
        assert topic.strength == 70
        assert topic.priority_score == 85
        assert topic.trend == "up"
        assert len(topic.evidence) == 3
        assert topic.score_card["level"] == "critical"
        assert session.commits == 1

    def test_aggregate_updates_existing_topic_by_title(self) -> None:
        session = FakeSession()
        existing = make_topic(title="窗口服务效率", priority=10)
        topic_repo = MemoryRepo([existing])
        service = InsightService(session, repo=topic_repo)  # type: ignore[arg-type]

        topic = service.aggregate_feedback("窗口服务效率", [make_feedback()])

        assert len(topic_repo.list_all()) == 1
        assert topic.feedback_count == 1
        assert topic.priority_score != 10

    def test_aggregate_empty_feedbacks_raises(self) -> None:
        session = FakeSession()
        service = InsightService(session, repo=MemoryRepo())  # type: ignore[arg-type]
        with pytest.raises(ValidationError):
            service.aggregate_feedback("空主题", [])

    def test_priority_levels(self) -> None:
        session = FakeSession()
        service = InsightService(session, repo=MemoryRepo())  # type: ignore[arg-type]
        assert service._level_of(85) == "critical"
        assert service._level_of(60) == "high"
        assert service._level_of(50) == "medium"
        assert service._level_of(10) == "low"

    def test_compute_trend(self) -> None:
        assert InsightService.compute_trend(5, 3) == "up"
        assert InsightService.compute_trend(2, 5) == "down"
        assert InsightService.compute_trend(4, 4) == "flat"
        assert InsightService.compute_trend(0, 0) == "flat"
        assert InsightService.compute_trend(3, None) == "up"


# ──────────────────────────────────────────────
# Gov → Insight 预警
# ──────────────────────────────────────────────

class TestGovInsightAlerts:
    def test_classify_complaint_levels(self) -> None:
        assert GovService.classify_complaint("发生安全事故") == "red"
        assert GovService.classify_complaint("媒体曝光维权") == "orange"
        assert GovService.classify_complaint("排队等待太久") == "yellow"
        assert GovService.classify_complaint("普通咨询") == "blue"

    def test_evaluate_insight_alerts_creates_orange(self) -> None:
        session = FakeSession()
        alert_repo = MemoryRepo()
        insight = InsightService(session, repo=MemoryRepo([make_topic(priority=80)]))  # type: ignore[arg-type]
        service = GovService(session, alert_repo=alert_repo, insight_service=insight)  # type: ignore[arg-type]

        alerts = service.evaluate_insight_alerts()

        assert len(alerts) == 1
        assert alerts[0].level == "orange"
        assert alerts[0].trigger == "insight_priority"
        assert alerts[0].evidence_count == 4
        assert len(alert_repo.list_all()) == 1

    def test_evaluate_skips_below_threshold_and_duplicates(self) -> None:
        session = FakeSession()
        alert_repo = MemoryRepo(
            [
                GovAlertItem(
                    id=str(uuid.uuid4()),
                    level="orange",
                    title="窗口服务效率",
                    created_at=datetime.now(timezone.utc),
                )
            ]
        )
        insight = InsightService(
            session,
            repo=MemoryRepo(
                [
                    make_topic(title="窗口服务效率", priority=90),  # 已存在同标题预警
                    make_topic(title="低频主题", priority=30),  # 低于阈值
                ]
            ),
        )  # type: ignore[arg-type]
        service = GovService(session, alert_repo=alert_repo, insight_service=insight)  # type: ignore[arg-type]

        assert service.evaluate_insight_alerts() == []
        assert len(alert_repo.list_all()) == 1


# ──────────────────────────────────────────────
# Roadmap → Insight 优先级
# ──────────────────────────────────────────────

class TestRoadmapInsight:
    def test_compute_recommended_priority(self) -> None:
        topic = make_topic(priority=75)
        assert RoadmapService.compute_recommended_priority(topic) == 75
        assert RoadmapService.compute_recommended_priority(None, fallback=10) == 10
        low = make_topic(priority=120)
        assert RoadmapService.compute_recommended_priority(low) == 100

    def test_add_task_from_topic_inherits_priority(self) -> None:
        session = FakeSession()
        topic = make_topic(priority=70)
        item = RoadmapItem(
            id=str(uuid.uuid4()),
            title="优化窗口服务",
            topic_id=topic.id,
            status="planning",
            task_count=0,
            progress=0,
        )
        roadmap = RoadmapService(
            session,
            repo=MemoryRepo([item]),  # type: ignore[arg-type]
            task_repo=MemoryRepo(),  # type: ignore[arg-type]
            insight_repo=MemoryRepo([topic]),  # type: ignore[arg-type]
        )

        task = roadmap.add_task_from_topic(item.id, "上线动态开窗")

        assert task.priority == 70
        assert isinstance(task, TaskItem)
        assert roadmap.get_item(item.id).task_count == 1

    def test_add_task_from_topic_without_topic_uses_zero(self) -> None:
        session = FakeSession()
        item = RoadmapItem(
            id=str(uuid.uuid4()),
            title="普通项目",
            topic_id=None,
            status="planning",
            task_count=0,
            progress=0,
        )
        roadmap = RoadmapService(
            session,
            repo=MemoryRepo([item]),  # type: ignore[arg-type]
            task_repo=MemoryRepo(),  # type: ignore[arg-type]
            insight_repo=MemoryRepo(),  # type: ignore[arg-type]
        )
        task = roadmap.add_task_from_topic(item.id, "基础任务")
        assert task.priority == 0

    def test_recompute_progress(self) -> None:
        session = FakeSession()
        item = RoadmapItem(
            id=str(uuid.uuid4()),
            title="项目",
            status="active",
            progress=0,
            task_count=3,
        )
        tasks = [
            TaskItem(id=str(uuid.uuid4()), roadmap_id=item.id, title="t1", status="done", priority=0),
            TaskItem(id=str(uuid.uuid4()), roadmap_id=item.id, title="t2", status="done", priority=0),
            TaskItem(id=str(uuid.uuid4()), roadmap_id=item.id, title="t3", status="todo", priority=0),
        ]
        roadmap = RoadmapService(
            session,
            repo=MemoryRepo([item]),  # type: ignore[arg-type]
            task_repo=MemoryRepo(tasks),  # type: ignore[arg-type]
            insight_repo=MemoryRepo(),  # type: ignore[arg-type]
        )
        updated = roadmap.recompute_progress(item.id)
        assert updated.progress == 67  # round(2/3*100)

    def test_roadmap_status_machine(self) -> None:
        session = FakeSession()
        item = RoadmapItem(id=str(uuid.uuid4()), title="项目", status="planning", task_count=0, progress=0)
        roadmap = RoadmapService(session, repo=MemoryRepo([item]))  # type: ignore[arg-type]
        assert roadmap.update_item_status(item.id, "active").status == "active"
        with pytest.raises(ValidationError):
            roadmap.update_item_status(item.id, "planning")


# ──────────────────────────────────────────────
# Workflow / Agent 互相校验
# ──────────────────────────────────────────────

class TestWorkflowService:
    def test_validate_nodes_ok(self) -> None:
        errors = WorkflowService.validate_nodes(
            [
                {"id": "c1", "type": "ClassifyNode"},
                {"id": "d1", "type": "DedupNode"},
            ],
            [{"source": "c1", "target": "d1"}],
            agent_bindings={"c1": "agent-1"},
        )
        assert errors == []

    def test_validate_nodes_duplicate_and_invalid_type(self) -> None:
        errors = WorkflowService.validate_nodes(
            [{"id": "c1", "type": "ClassifyNode"}, {"id": "c1", "type": "UnknownNode"}],
            [],
        )
        assert any("重复" in e for e in errors)
        assert any("type 非法" in e for e in errors)

    def test_validate_nodes_bad_edge_and_binding(self) -> None:
        errors = WorkflowService.validate_nodes(
            [{"id": "c1", "type": "ClassifyNode"}],
            [{"source": "missing", "target": "c1"}],
            agent_bindings={"ghost": "agent-1"},
        )
        assert any("不存在的源节点" in e for e in errors)
        assert any("Agent 绑定节点不存在" in e for e in errors)

    def test_create_rejects_invalid_graph(self) -> None:
        session = FakeSession()
        service = WorkflowService(session, repo=MemoryRepo())  # type: ignore[arg-type]
        with pytest.raises(ValidationError):
            service.create({"name": "坏图", "nodes": [{"id": "x", "type": "BadType"}]})

    def test_start_run_requires_enabled(self) -> None:
        session = FakeSession()
        workflow = Workflow(id=str(uuid.uuid4()), name="禁用流", enabled=False)
        service = WorkflowService(
            session,
            repo=MemoryRepo([workflow]),  # type: ignore[arg-type]
            run_repo=MemoryRepo(),  # type: ignore[arg-type]
        )
        with pytest.raises(ValidationError):
            service.start_run(workflow.id)


class TestAgentService:
    def test_record_run_reliability_bounds(self) -> None:
        session = FakeSession()
        agent = make_agent(reliability=99)
        service = AgentService(session, repo=MemoryRepo([agent]))  # type: ignore[arg-type]
        service.record_run(agent.id, success=True)
        assert agent.reliability == 100  # 封顶
        service.record_run(agent.id, success=False)
        service.record_run(agent.id, success=False)
        assert agent.reliability == 96
        assert agent.run_count == 3

    def test_has_tool_supports_dict_and_string(self) -> None:
        session = FakeSession()
        agent = make_agent()
        agent.tools = [{"key": "search_kb"}, "web_search"]
        service = AgentService(session, repo=MemoryRepo([agent]))  # type: ignore[arg-type]
        assert service.has_tool(agent.id, "search_kb") is True
        assert service.has_tool(agent.id, "web_search") is True
        assert service.has_tool(agent.id, "missing") is False

    def test_bind_workflow_idempotent_and_validates(self) -> None:
        session = FakeSession()
        agent = make_agent()
        workflow = Workflow(id=str(uuid.uuid4()), name="流", enabled=True)
        agent_service = AgentService(session, repo=MemoryRepo([agent]))  # type: ignore[arg-type]
        workflow_service = WorkflowService(session, repo=MemoryRepo([workflow]))  # type: ignore[arg-type]
        agent_service._workflows = workflow_service

        agent_service.bind_workflow(agent.id, workflow.id)
        assert agent.bound_workflow_ids == [workflow.id]
        agent_service.bind_workflow(agent.id, workflow.id)
        assert len(agent.bound_workflow_ids) == 1  # 幂等

    def test_bind_workflow_validates_existence(self) -> None:
        session = FakeSession()
        agent = make_agent()
        agent_service = AgentService(session, repo=MemoryRepo([agent]))  # type: ignore[arg-type]
        workflow_service = WorkflowService(session, repo=MemoryRepo())  # type: ignore[arg-type]
        agent_service._workflows = workflow_service
        with pytest.raises(NotFoundError):
            agent_service.bind_workflow(agent.id, "missing-wf")

    def test_toggle_skill(self) -> None:
        session = FakeSession()
        skill = Skill(id=str(uuid.uuid4()), name="知识库", enabled=True)
        service = AgentService(session, skill_repo=MemoryRepo([skill]))  # type: ignore[arg-type]
        assert service.toggle_skill(skill.id).enabled is False


# ──────────────────────────────────────────────
# Automation 规则引擎
# ──────────────────────────────────────────────

class TestAutomationService:
    def test_classify_hits_keyword(self) -> None:
        session = FakeSession()
        classification_repo = MemoryRepo()
        service = AutomationService(session, classification_repo=classification_repo)  # type: ignore[arg-type]

        result = service.classify(make_feedback(content="大厅排队太久了"))

        assert isinstance(result, ClassificationResult)
        assert result.suggested_topic == "窗口服务效率"
        assert result.confidence > 0.6
        assert result.needs_review is False
        assert len(classification_repo.list_all()) == 1

    def test_classify_no_match_requires_review(self) -> None:
        session = FakeSession()
        service = AutomationService(session, classification_repo=MemoryRepo())  # type: ignore[arg-type]
        result = service.classify(make_feedback(content="完全无关的普通咨询"))
        assert result.suggested_topic == "待人工分类"
        assert result.needs_review is True
        assert result.confidence == 0.0

    def test_suggest_dedup_group(self) -> None:
        session = FakeSession()
        dedup_repo = MemoryRepo()
        service = AutomationService(session, dedup_repo=dedup_repo)  # type: ignore[arg-type]
        target = make_feedback(content="大厅排队等待太久了")
        candidates = [make_feedback(content="大厅排队等待时间太长影响体验")]

        group = service.suggest_dedup(target, candidates)

        assert isinstance(group, DedupGroup)
        assert group.repeat_count == 2
        assert group.status == "pending"
        assert len(dedup_repo.list_all()) == 1

    def test_suggest_dedup_none_when_low_similarity(self) -> None:
        session = FakeSession()
        service = AutomationService(session, dedup_repo=MemoryRepo())  # type: ignore[arg-type]
        target = make_feedback(content="排队")
        candidates = [make_feedback(content="材料复印复复杂杂处理")]
        assert service.suggest_dedup(target, candidates) is None

    def test_auto_reply_uses_injected_generator(self) -> None:
        session = FakeSession()

        class FakeGenerator(ReplyGenerator):
            def generate_reply(self, content: str) -> str:
                return f"re: {content}"

        service = AutomationService(session, reply_generator=FakeGenerator())
        assert service.auto_reply(make_feedback(content="排队")) == "re: 排队"

        service_without = AutomationService(session)
        assert service_without.auto_reply(make_feedback(content="排队")) is None

    def test_record_priority_adjustment_validation(self) -> None:
        session = FakeSession()
        service = AutomationService(session, adjustment_repo=MemoryRepo())  # type: ignore[arg-type]
        with pytest.raises(ValidationError):
            service.record_priority_adjustment(feedback_id="f1", old_priority=10, new_priority=101)
        adjustment = service.record_priority_adjustment(
            feedback_id="f1", old_priority=50, new_priority=80, reason="舆情升级"
        )
        assert isinstance(adjustment, PriorityAdjustment)
        assert adjustment.reason == "舆情升级"


# ──────────────────────────────────────────────
# Resource 监控
# ──────────────────────────────────────────────

class TestResourceService:
    def make_server(self, *, cpu: float = 50.0, mem: float = 50.0, disk: float = 50.0, status: str = "healthy"):
        from app.models.resource import ServerState

        return ServerState(
            id=str(uuid.uuid4()),
            name="app-server-1",
            role="backend",
            cpu=cpu,
            mem=mem,
            disk=disk,
            status=status,
        )

    def make_endpoint(self, *, error_rate: float = 0.0, response_ms: int = 100, status: str = "healthy"):
        from app.models.resource import ApiEndpointState

        return ApiEndpointState(
            id=str(uuid.uuid4()),
            method="GET",
            path="/api/v1/healthz",
            status=status,
            response_ms=response_ms,
            error_rate=error_rate,
        )

    def test_overall_health(self) -> None:
        session = FakeSession()
        from app.models.resource import DatabaseState

        db = DatabaseState(id=str(uuid.uuid4()), name="pg", status="error")
        service = ResourceService(
            session,
            server_repo=MemoryRepo([self.make_server()]),  # type: ignore[arg-type]
            db_repo=MemoryRepo([db]),  # type: ignore[arg-type]
            endpoint_repo=MemoryRepo([self.make_endpoint()]),  # type: ignore[arg-type]
        )
        health = service.overall_health()
        assert health["overall"] == "error"
        assert health["total"] == 3
        assert health["healthy"] == 2

    def test_evaluate_alerts_thresholds(self) -> None:
        session = FakeSession()
        alert_repo = MemoryRepo()
        service = ResourceService(
            session,
            server_repo=MemoryRepo([self.make_server(cpu=95.0)]),  # type: ignore[arg-type]
            db_repo=MemoryRepo(),  # type: ignore[arg-type]
            endpoint_repo=MemoryRepo([self.make_endpoint(error_rate=0.3)]),  # type: ignore[arg-type]
            alert_repo=alert_repo,  # type: ignore[arg-type]
        )
        alerts = service.evaluate_alerts()
        levels = [a.level for a in alerts]
        assert "warning" in levels
        assert len(alerts) == 2  # CPU 超阈值 + API 错误率超阈值
        assert len(alert_repo.list_all()) == 2
        assert session.commits == 1