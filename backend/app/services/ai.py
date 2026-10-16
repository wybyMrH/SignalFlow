"""SignalFlow 后端 - AI 工作流服务。

骨架阶段：提供 mock 实现，覆盖前端所有 AI 交互场景。
真实 LLM 接入时，仅需替换 _generate 内部实现，接口契约不变。
"""

import random
import time
import uuid
from datetime import datetime, timedelta
from typing import Any

from app.core.logging import get_logger
from app.schemas.ai import AIAutomationRule, AIChatMessage, AIWorkflowStatus

logger = get_logger(__name__)


class AIService:
    """AI 工作流服务（mock 阶段）。"""

    def __init__(self) -> None:
        self._msg_counter = 0

    def _next_msg_id(self) -> str:
        self._msg_counter += 1
        return f"msg-{self._msg_counter:03d}"

    # ───── 工作流状态 ─────

    def get_workflows(self) -> list[AIWorkflowStatus]:
        """返回当前运行中的 AI 工作流列表（mock 数据）。"""
        now = datetime.utcnow()
        return [
            AIWorkflowStatus(
                id="wf-001",
                name="工单智能分类",
                status="running",
                progress=67,
                started_at=now - timedelta(minutes=12),
                eta="约 3 分钟",
                detail="正在对今日 12 条新工单进行主题聚类与优先级评估",
            ),
            AIWorkflowStatus(
                id="wf-002",
                name="舆情情感监测",
                status="running",
                progress=45,
                started_at=now - timedelta(minutes=25),
                eta="约 8 分钟",
                detail="分析近 7 天热线与门户反馈情感倾向",
            ),
            AIWorkflowStatus(
                id="wf-003",
                name="重复问题自动汇总",
                status="completed",
                progress=100,
                started_at=now - timedelta(minutes=60),
                detail="已识别 3 组高频重复提问，生成统一话术建议",
            ),
            AIWorkflowStatus(
                id="wf-004",
                name="政策知识库同步",
                status="queued",
                progress=0,
                started_at=now,
                detail="等待夜间批量更新窗口（02:00）",
            ),
            AIWorkflowStatus(
                id="wf-005",
                name="高优先级自动升级",
                status="running",
                progress=82,
                started_at=now - timedelta(minutes=5),
                eta="约 1 分钟",
                detail="检测到 1 条 P5 级投诉，正在推送值班负责人",
            ),
        ]

    # ───── 自动化规则 ─────

    def get_automation_rules(self) -> list[AIAutomationRule]:
        """返回政企场景预设自动化规则。"""
        return [
            AIAutomationRule(
                id="rule-001",
                name="自动分类新工单",
                description="根据内容关键词与历史聚类模型，自动为新提交工单分配主题标签与优先级",
                enabled=True,
                scenario="工单接入",
                icon="tags",
                tone="primary",
                stats="今日已自动分类 12 条",
            ),
            AIAutomationRule(
                id="rule-002",
                name="重复问题自动回复",
                description="对匹配到知识库高频问答模板的工单，自动生成统一规范回复并进入待审批队列",
                enabled=True,
                scenario="回复生成",
                icon="message",
                tone="success",
                stats="今日已命中 5 条",
            ),
            AIAutomationRule(
                id="rule-003",
                name="高优先级自动升级",
                description="P4+ 工单或情感极负面反馈，自动推送至值班负责人并生成督办任务",
                enabled=True,
                scenario="风险预警",
                icon="alert",
                tone="warning",
                stats="今日已升级 2 条",
            ),
            AIAutomationRule(
                id="rule-004",
                name="情感负面实时预警",
                description="监测热线/门户/评价渠道，连续出现负面情感反馈时触发预警通知",
                enabled=False,
                scenario="舆情监测",
                icon="sentiment",
                tone="danger",
                stats="上次触发：昨天 14:32",
            ),
            AIAutomationRule(
                id="rule-005",
                name="材料清单智能校验",
                description="根据办理事项自动匹配所需材料清单，发现重复提交时提示历史材料复用",
                enabled=True,
                scenario="办事辅助",
                icon="checklist",
                tone="info",
                stats="本月减少重复提交 38 次",
            ),
            AIAutomationRule(
                id="rule-006",
                name="预约爽约自动提醒",
                description="预约前 1 小时通过短信/APP 推送提醒，爽约后自动释放号源",
                enabled=False,
                scenario="预约管理",
                icon="clock",
                tone="info",
                stats="待启用",
            ),
        ]

    # ───── 对话与回复生成 ─────

    def chat(self, query: str, _history: list[AIChatMessage]) -> AIChatMessage:
        """AI 对话：基于关键词匹配返回 mock 回复。"""
        q = query.lower()
        reply = self._build_reply(q)
        return AIChatMessage(
            id=self._next_msg_id(),
            role="assistant",
            content=reply,
            timestamp=datetime.utcnow(),
            workflow_refs=["wf-001", "wf-002"],
            sources=["知识库 v2026.10", "工单数据库", "政策文件库"],
        )

    def welcome(self) -> AIChatMessage:
        """AI 欢迎语。"""
        return AIChatMessage(
            id=self._next_msg_id(),
            role="assistant",
            content=(
                "您好，我是 SignalFlow 智能助手。\n"
                "我可以帮您查询工单统计、查看 AI 工作流状态、检索政策知识库，或根据历史数据给出整改建议。\n"
                "试试问我「今天工单情况如何」或「最近有什么高频问题」。"
            ),
            timestamp=datetime.utcnow(),
        )

    def generate_reply(self, content: str) -> str:
        """基于反馈内容生成 AI 回复草稿（模拟知识库检索）。"""
        lower = content.lower()
        if "排队" in lower or "等候" in lower or "叫号" in lower:
            return (
                "您好，关于大厅排队等候问题，我们已记录并反馈至运营管理组。\n\n"
                "当前已采取以下措施：\n"
                "1. 高峰期（9:00-11:00, 14:00-16:00）已增开 2 个综合窗口\n"
                "2. 叫号系统已升级，新增微信实时排队提醒功能\n"
                "3. 针对老年群体，保留人工取号通道并提供优先服务\n\n"
                "预计下周五前完成动态开窗系统的联调测试，届时将根据实时客流自动调整开放窗口数量。\n"
                "如需进一步协助，请拨打服务热线 12345 或到 2 号窗口咨询。"
            )
        if "材料" in lower or "重复" in lower or "复印" in lower:
            return (
                "您好，关于材料重复提交的问题，我们正在推进「一网通办」材料共享机制。\n\n"
                "目前可采取以下方式减少重复提交：\n"
                "1. 通过「政务通」APP 完成实名认证后，系统自动调取电子证照\n"
                "2. 同类型业务在 30 天内可使用历史材料，无需重复提交\n"
                "3. 房屋租赁备案、社保转移等高频事项已接入材料复用接口\n\n"
                "如需查询您的历史材料清单或申请电子证照调用，可到 5 号窗口办理，或致电 12345 按 3 号键转接材料审核专席。"
            )
        if "预约" in lower or "爽约" in lower or "取消" in lower:
            return (
                "您好，关于预约系统相关问题，我们已核实并处理。\n\n"
                "说明如下：\n"
                "1. 预约成功后系统将在办理前 1 小时发送短信提醒\n"
                "2. 如因故无法到场，请提前 2 小时在 APP 或网站取消预约\n"
                "3. 连续 3 次爽约将暂停预约权限 7 天，现场取号不受影响\n\n"
                "如需重新预约或查询预约记录，请登录「政务服务网」→「我的预约」，或拨打 12345 按 2 号键。"
            )
        if "政策" in lower or "咨询" in lower or "答复" in lower:
            return (
                "您好，关于政策咨询问题，已转接至政策解读专员处理。\n\n"
                "根据您的问题类型，相关政策如下：\n"
                "• 社保转移：需在原参保地开具《参保缴费凭证》，至现参保地申请转入\n"
                "• 生育津贴：连续缴费满 12 个月且生育时参保状态正常即可申领\n"
                "• 异地就医备案：可通过「国家医保服务平台」APP 在线办理\n\n"
                "如需获取完整政策文件或申请一对一政策解读，请拨打 12345 按 5 号键，或到 3 号窗口「政策咨询专席」办理。"
            )
        return (
            "您好，感谢您的反馈。我们已收到您的诉求并安排专人跟进处理。\n\n"
            "通常处理时效：\n"
            "• 一般咨询类：1-2 个工作日\n"
            "• 业务办理类：3-5 个工作日\n"
            "• 投诉建议类：5-7 个工作日\n\n"
            "您可通过以下方式查询进度：\n"
            "1. 「政务服务网」→「我的工单」输入编号查询\n"
            "2. 拨打 12345 按 1 号键查询工单状态\n"
            "3. 关注微信公众号「XX政务」，绑定后实时接收进度推送\n\n"
            "再次感谢您的监督与支持，我们将持续改进服务质量。"
        )

    def get_reply_suggestion(self, content: str) -> str:
        """AI 气泡助手：根据反馈内容给出简短回复建议。"""
        lower = content.lower()
        if "排队" in lower or "等候" in lower:
            return "建议回复：已增开窗口+叫号升级+老人优先通道，预计下周五完成动态开窗系统联调。"
        if "材料" in lower or "重复" in lower:
            return "建议回复：推行政务通 APP 电子证照自动调取，同类型业务 30 天内免重复提交。"
        if "预约" in lower:
            return "建议回复：说明预约提醒机制、取消规则及爽约处理政策，提供重新预约入口。"
        if "态度" in lower or "服务" in lower:
            return "建议回复：致歉+承诺加强培训+提供投诉渠道，必要时安排回访。"
        if "app" in lower or "手机" in lower or "闪退" in lower:
            return "建议回复：收集设备型号与系统版本，提供临时解决方案（网页版/电话预约），承诺技术修复。"
        return "建议回复：确认收到诉求+说明处理时效+提供查询渠道+表达感谢与改进决心。"

    def auto_approve(self, _feedback_id: str, content: str) -> dict[str, Any]:
        """AI 自动审批：生成统一话术并标记 AI 已回复。"""
        reply = self.generate_reply(content)
        return {"reply": reply, "status": "ai_replied"}

    # ───── 自动化中心（自动分类 / 去重 / 优先级） ─────

    def get_auto_classification(self) -> list[dict[str, Any]]:
        """自动分类结果列表（对齐前端 AutoClassificationResult）。"""
        now = datetime.utcnow()
        iso = now.isoformat()
        return [
            {
                "feedback_id": "F1061",
                "content": "大厅排队时间太长，等了快两个小时还没叫到号，希望能增加窗口。",
                "suggested_topic": "大厅等候时间",
                "confidence": 0.94,
                "alternatives": [
                    {"topic": "叫号系统", "confidence": 0.78},
                    {"topic": "人员配置", "confidence": 0.62},
                ],
                "needs_review": False,
                "processed_at": iso,
            },
            {
                "feedback_id": "F1062",
                "content": "窗口工作人员态度恶劣，问了两句话就不耐烦了。",
                "suggested_topic": "服务态度",
                "confidence": 0.89,
                "alternatives": [
                    {"topic": "投诉建议", "confidence": 0.71},
                    {"topic": "人员培训", "confidence": 0.55},
                ],
                "needs_review": False,
                "processed_at": iso,
            },
            {
                "feedback_id": "F1063",
                "content": "社保转移需要什么材料？我已经在原参保地开了证明，接下来怎么做？",
                "suggested_topic": "社保转移",
                "confidence": 0.67,
                "alternatives": [
                    {"topic": "材料清单", "confidence": 0.58},
                    {"topic": "异地就医", "confidence": 0.41},
                ],
                "needs_review": True,
                "processed_at": iso,
                "reviewer_note": "涉及材料+流程，建议拆分为「社保转移」+「材料清单」两个主题",
            },
            {
                "feedback_id": "F1064",
                "content": "APP 总是闪退，一提交材料就卡死，安卓手机。",
                "suggested_topic": "系统故障",
                "confidence": 0.91,
                "alternatives": [
                    {"topic": "APP 使用", "confidence": 0.83},
                    {"topic": "材料提交", "confidence": 0.45},
                ],
                "needs_review": False,
                "processed_at": iso,
            },
            {
                "feedback_id": "F1065",
                "content": "昨天预约了今天 9 点的号，结果窗口没开，白跑一趟。",
                "suggested_topic": "预约管理",
                "confidence": 0.72,
                "alternatives": [
                    {"topic": "窗口开放", "confidence": 0.68},
                    {"topic": "通知服务", "confidence": 0.51},
                ],
                "needs_review": True,
                "processed_at": iso,
                "reviewer_note": "涉及爽约+窗口开放，需确认是否为预约系统同步问题",
            },
        ]

    def get_dedup_groups(self) -> list[dict[str, Any]]:
        """去重合并组列表（对齐前端 DedupGroup，group_id 字段）。"""
        iso = datetime.utcnow().isoformat()
        return [
            {
                "group_id": "DG-001",
                "representative_id": "F1001",
                "members": [
                    {"feedback_id": "F1001", "content": "大厅排队时间太长，建议增加窗口", "similarity": 1.0},
                    {"feedback_id": "F1003", "content": "等了两个小时，排队系统能不能优化一下", "similarity": 0.91},
                    {"feedback_id": "F1005", "content": "高峰期窗口太少，建议增派人手", "similarity": 0.87},
                    {"feedback_id": "F1007", "content": "排队叫号太慢，老年人站不住", "similarity": 0.84},
                ],
                "merged_topic": "大厅等候时间",
                "status": "merged",
                "merged_at": iso,
                "repeat_count": 4,
            },
            {
                "group_id": "DG-002",
                "representative_id": "F1002",
                "members": [
                    {"feedback_id": "F1002", "content": "材料需要重复提交，上次办过的还要重新复印", "similarity": 1.0},
                    {"feedback_id": "F1004", "content": "同样的材料交了好几遍，不同窗口要求不一样", "similarity": 0.93},
                    {"feedback_id": "F1006", "content": "复印件都带了，说格式不对要重新复印", "similarity": 0.78},
                ],
                "merged_topic": "材料重复提交",
                "status": "merged",
                "merged_at": iso,
                "repeat_count": 3,
            },
            {
                "group_id": "DG-003",
                "representative_id": "F1062",
                "members": [
                    {"feedback_id": "F1062", "content": "窗口工作人员态度恶劣，问了两句话就不耐烦了。", "similarity": 1.0},
                    {"feedback_id": "F1010", "content": "工作人员态度很差，咨询问题爱答不理", "similarity": 0.89},
                ],
                "merged_topic": "服务态度",
                "status": "pending",
                "repeat_count": 2,
            },
            {
                "group_id": "DG-004",
                "representative_id": "F1064",
                "members": [
                    {"feedback_id": "F1064", "content": "APP 总是闪退，一提交材料就卡死，安卓手机。", "similarity": 1.0},
                    {"feedback_id": "F1012", "content": "手机 APP 打开就闪退，根本用不了", "similarity": 0.85},
                    {"feedback_id": "F1015", "content": "安卓版 APP 频繁崩溃，什么时候修复", "similarity": 0.82},
                ],
                "merged_topic": "APP 闪退/崩溃",
                "status": "pending",
                "repeat_count": 3,
            },
        ]

    def get_priority_rules(self) -> list[dict[str, Any]]:
        """优先级评分规则列表（对齐前端 PriorityRule，RICE 模型）。"""
        iso = datetime.utcnow().isoformat()
        return [
            {
                "id": "pr-001",
                "name": "高负面情感自动升级",
                "enabled": True,
                "description": "当单条反馈被识别为强烈负面情感（置信度>0.85）且涉及服务态度/投诉时，自动上调优先级至 P4+",
                "factors": [
                    {"key": "reach", "label": "影响范围", "weight": 0.25, "value": 85, "max": 100, "note": "负面情感易在社交平台扩散"},
                    {"key": "impact", "label": "影响深度", "weight": 0.30, "value": 90, "max": 100, "note": "直接关系群众对政务服务的信任度"},
                    {"key": "confidence", "label": "置信度", "weight": 0.25, "value": 88, "max": 100, "note": "情感识别模型准确率"},
                    {"key": "effort", "label": "解决成本", "weight": 0.20, "value": 30, "max": 100, "note": "培训+流程优化即可改善，成本较低"},
                ],
                "threshold": 80,
                "auto_escalate": True,
                "updated_at": iso,
            },
            {
                "id": "pr-002",
                "name": "高频重复问题优先处理",
                "enabled": True,
                "description": "当周累计出现 3 次以上的同类重复反馈，自动提升处理优先级并触发标准化回复模板",
                "factors": [
                    {"key": "reach", "label": "影响范围", "weight": 0.30, "value": 80, "max": 100, "note": "高频 = 多用户受影响"},
                    {"key": "impact", "label": "影响深度", "weight": 0.25, "value": 65, "max": 100, "note": "多为流程/系统问题，解决后满意度提升明显"},
                    {"key": "confidence", "label": "置信度", "weight": 0.20, "value": 92, "max": 100, "note": "去重组准确率"},
                    {"key": "effort", "label": "解决成本", "weight": 0.25, "value": 55, "max": 100, "note": "需协调多部门，中等成本"},
                ],
                "threshold": 70,
                "auto_escalate": True,
                "updated_at": iso,
            },
            {
                "id": "pr-003",
                "name": "系统故障类紧急响应",
                "enabled": True,
                "description": "APP/系统宕机、闪退、无法提交材料等技术故障，立即标记为紧急并通知技术团队",
                "factors": [
                    {"key": "reach", "label": "影响范围", "weight": 0.35, "value": 95, "max": 100, "note": "线上渠道瘫痪影响所有线上用户"},
                    {"key": "impact", "label": "影响深度", "weight": 0.30, "value": 90, "max": 100, "note": "阻断业务办理，影响群众办事体验"},
                    {"key": "confidence", "label": "置信度", "weight": 0.15, "value": 85, "max": 100, "note": "技术故障关键词识别准确率"},
                    {"key": "effort", "label": "解决成本", "weight": 0.20, "value": 70, "max": 100, "note": "需技术团队介入，排查修复周期不确定"},
                ],
                "threshold": 85,
                "auto_escalate": True,
                "updated_at": iso,
            },
            {
                "id": "pr-004",
                "name": "政策咨询类常规处理",
                "enabled": True,
                "description": "一般性政策咨询（社保、医保、公积金等），使用标准化话术自动回复并归入知识库",
                "factors": [
                    {"key": "reach", "label": "影响范围", "weight": 0.20, "value": 60, "max": 100, "note": "单个用户咨询，影响范围有限"},
                    {"key": "impact", "label": "影响深度", "weight": 0.20, "value": 50, "max": 100, "note": "信息性问题，不直接涉及服务缺陷"},
                    {"key": "confidence", "label": "置信度", "weight": 0.30, "value": 90, "max": 100, "note": "政策类关键词匹配准确率高"},
                    {"key": "effort", "label": "解决成本", "weight": 0.30, "value": 15, "max": 100, "note": "知识库话术可直接回复，成本低"},
                ],
                "threshold": 45,
                "auto_escalate": False,
                "updated_at": iso,
            },
        ]

    def get_priority_adjustments(self) -> list[dict[str, Any]]:
        """优先级调整记录（对齐前端 PriorityAdjustment）。"""
        now = datetime.utcnow()
        return [
            {
                "feedback_id": "F1062",
                "old_priority": 2,
                "new_priority": 5,
                "reason": "情感负面置信度 0.94，触发「高负面情感自动升级」规则",
                "triggered_by": "pr-001",
                "adjusted_at": (now - timedelta(hours=2)).isoformat(),
            },
            {
                "feedback_id": "F1064",
                "old_priority": 1,
                "new_priority": 4,
                "reason": "系统故障类紧急响应规则命中：APP 闪退关键词 + 安卓设备",
                "triggered_by": "pr-003",
                "adjusted_at": (now - timedelta(hours=1)).isoformat(),
            },
            {
                "feedback_id": "F1001",
                "old_priority": 2,
                "new_priority": 4,
                "reason": "大厅等候时间属于高频重复问题（本周 11 次），触发自动升级",
                "triggered_by": "pr-002",
                "adjusted_at": (now - timedelta(hours=4)).isoformat(),
            },
            {
                "feedback_id": "F1061",
                "old_priority": 3,
                "new_priority": 3,
                "reason": "分类后重新评估，大厅等候时间与已有洞察主题一致，保持当前优先级",
                "triggered_by": "pr-002",
                "adjusted_at": (now - timedelta(minutes=30)).isoformat(),
            },
        ]

    def get_automation_summary(self) -> dict[str, Any]:
        """自动化执行概览（对齐前端 AutomationExecutionSummary，日维度）。"""
        return {
            "date": datetime.utcnow().date().isoformat(),
            "classified_count": 47,
            "review_queue_count": 6,
            "deduped_group_count": 12,
            "saved_feedback_count": 31,
            "priority_adjusted_count": 8,
            "auto_escalated_count": 3,
            "avg_confidence": 0.84,
            "manual_review_rate": 0.128,
        }

    # ───── 商务洞察（企业合作线索与市场动向） ─────

    def get_business_leads(self) -> list[dict[str, Any]]:
        """企业合作线索列表（对齐前端 BusinessLead）。"""
        now = datetime.utcnow()
        return [
            {
                "id": "BL-001",
                "feedback_id": "F1101",
                "content": "我们公司有 400 多名设计师，现在每人单独建账号太麻烦，希望支持批量导入和角色分组。",
                "company_name": "云帆数字设计",
                "industry": "企业服务",
                "company_type": "私企",
                "size_band": "500-2000 人",
                "matched_product": "企业版·批量账号管理",
                "match_reason": "反馈提及「批量导入 + 角色分组」，与企业版多人协作能力语义匹配",
                "value_score": 82,
                "confidence": 0.91,
                "stage": "pushed",
                "created_at": (now - timedelta(days=2)).isoformat(),
            },
            {
                "id": "BL-002",
                "feedback_id": "F1102",
                "content": "作为外包承接方，客户要求我们提供本地化部署版本，敏感数据不能出我们的机房。",
                "company_name": "中科软联",
                "industry": "软件外包",
                "company_type": "私企",
                "size_band": "200-500 人",
                "matched_product": "私有化部署包",
                "match_reason": "反馈提出「本地化部署 + 数据不出域」，匹配私有化版本需求",
                "value_score": 78,
                "confidence": 0.88,
                "stage": "qualified",
                "created_at": (now - timedelta(days=3)).isoformat(),
            },
            {
                "id": "BL-003",
                "feedback_id": "F1103",
                "content": "我们是省属国企，需要和内部 OA、统一认证对接，账号体系要对齐集团标准。",
                "company_name": "华东能源集团",
                "industry": "能源化工",
                "company_type": "国企",
                "size_band": "2000 人以上",
                "matched_product": "企业版·SSO/统一认证",
                "match_reason": "反馈提及「统一认证 + 集团账号标准」，匹配 SSO 集成能力",
                "value_score": 90,
                "confidence": 0.95,
                "stage": "pushed",
                "created_at": (now - timedelta(days=5)).isoformat(),
            },
            {
                "id": "BL-004",
                "feedback_id": "F1104",
                "content": "想基于贵司报表能力做二次开发，把反馈数据嵌入我们自己的 BI 看板。",
                "company_name": "擎天数据科技",
                "industry": "数据服务",
                "company_type": "私企",
                "size_band": "50-200 人",
                "matched_product": "开放 API / Webhook",
                "match_reason": "反馈提出「二次开发 + 嵌入 BI」，匹配开放 API 与数据集成能力",
                "value_score": 68,
                "confidence": 0.79,
                "stage": "identified",
                "created_at": (now - timedelta(days=1)).isoformat(),
            },
        ]

    def get_industry_shares(self) -> list[dict[str, Any]]:
        """行业分布（对齐前端 IndustryShare，含 trend 字段）。"""
        return [
            {"industry": "企业服务", "count": 38, "pct": 0.28, "trend": "up"},
            {"industry": "智能制造", "count": 31, "pct": 0.23, "trend": "up"},
            {"industry": "教育", "count": 24, "pct": 0.18, "trend": "flat"},
            {"industry": "能源化工", "count": 17, "pct": 0.12, "trend": "up"},
            {"industry": "数据服务", "count": 15, "pct": 0.11, "trend": "down"},
            {"industry": "零售消费", "count": 11, "pct": 0.08, "trend": "flat"},
        ]

    def get_market_signals(self) -> list[dict[str, Any]]:
        """市场动向信号（对齐前端 MarketSignal）。"""
        now = datetime.utcnow()
        return [
            {
                "id": "MS-001",
                "title": "私有化部署需求上升",
                "type": "opportunity",
                "summary": "近 30 天「私有化 / 数据不出域」类反馈增长 42%，集中在制造与能源行业，建议重点跟进私有化版本售卖。",
                "evidence_count": 23,
                "severity": 88,
                "related_industries": ["智能制造", "能源化工"],
                "created_at": (now - timedelta(hours=6)).isoformat(),
            },
            {
                "id": "MS-002",
                "title": "组织隔离成为教育行业刚需",
                "type": "gap",
                "summary": "教育机构普遍提出分院/分校数据隔离诉求，当前产品按企业单租户设计，存在能力缺口。",
                "evidence_count": 12,
                "severity": 76,
                "related_industries": ["教育"],
                "created_at": (now - timedelta(hours=12)).isoformat(),
            },
            {
                "id": "MS-003",
                "title": "开放 API 集成热度回落",
                "type": "shift",
                "summary": "「二次开发 / API」类反馈占比由 16% 降至 8%，可能与企业转向成熟集成市场有关，需验证是需求转移还是渠道变化。",
                "evidence_count": 9,
                "severity": 52,
                "related_industries": ["数据服务", "企业服务"],
                "created_at": (now - timedelta(hours=18)).isoformat(),
            },
            {
                "id": "MS-004",
                "title": "合规审计成为大型企业准入门槛",
                "type": "risk",
                "summary": "500 人以上企业客户中 63% 提及审计日志或合规要求，若缺失将影响政企大单准入。",
                "evidence_count": 27,
                "severity": 81,
                "related_industries": ["能源化工", "智能制造", "金融"],
                "created_at": (now - timedelta(hours=26)).isoformat(),
            },
        ]

    def get_common_needs(self) -> list[dict[str, Any]]:
        """共性需求归纳（对齐前端 CommonNeed）。"""
        return [
            {
                "id": "CN-001",
                "title": "批量账号与角色管理",
                "description": "大型组织需要批量导入成员、按部门/角色分组授权，减少单账号逐个配置的运维成本。",
                "feedback_count": 34,
                "customer_count": 12,
                "industries": ["企业服务", "能源化工", "教育"],
                "product_potential": "企业版·批量账号与 RBAC 角色分组",
                "priority": 5,
                "status": "planned",
            },
            {
                "id": "CN-002",
                "title": "私有化与数据不出域部署",
                "description": "具备合规诉求的政企客户要求本地化部署，数据不允许离开自有机房或堡垒环境。",
                "feedback_count": 29,
                "customer_count": 9,
                "industries": ["智能制造", "能源化工"],
                "product_potential": "私有化部署包（Docker/K8s + 本地模型）",
                "priority": 5,
                "status": "open",
            },
            {
                "id": "CN-003",
                "title": "统一认证与集团账号对接",
                "description": "国企与大型集团要求对接内部 OA、统一身份认证，账号体系需对齐集团标准。",
                "feedback_count": 18,
                "customer_count": 7,
                "industries": ["能源化工", "智能制造"],
                "product_potential": "企业版·SSO/标准协议联调",
                "priority": 4,
                "status": "planned",
            },
            {
                "id": "CN-004",
                "title": "审计日志与合规报告",
                "description": "受 GDPR / 等保等约束的客户需要完整操作审计、留痕与合规导出能力。",
                "feedback_count": 27,
                "customer_count": 8,
                "industries": ["智能制造", "能源化工", "数据服务"],
                "product_potential": "企业版·审计日志与合规报表",
                "priority": 4,
                "status": "open",
            },
        ]

    def get_business_summary(self) -> dict[str, Any]:
        """商务洞察总览（对齐前端 BusinessInsightSummary）。"""
        today = datetime.utcnow().date()
        start = today - timedelta(days=29)
        return {
            "total_leads": 4,
            "qualified_leads": 2,
            "pushed_leads": 2,
            "industry_count": 6,
            "total_feedback_count": 136,
            "customer_count": 58,
            "market_signal_count": 4,
            "common_need_count": 4,
            "report_period": f"{start.isoformat()} ~ {today.isoformat()}",
            "generated_at": datetime.utcnow().isoformat(),
        }

    # ───── 内部：构建对话回复 ─────

    def _build_reply(self, q: str) -> str:
        if "工单" in q or "情况" in q or "多少" in q or "今天" in q:
            return (
                "今日工单概览：\n"
                "• 新接入工单 **48** 条，待处理 **20** 条\n"
                "• 高优先级（P4+）**8** 条，已解决 **5** 条\n"
                "• 平均解决时长 **6.5** 小时\n"
                "• 主要渠道：热线 17 条、工单系统 12 条、门户 10 条\n\n"
                "如需下钻到具体工单列表，请点击下方「反馈管理」导航。"
            )
        if "自动" in q or "规则" in q or "配置" in q:
            return (
                "当前已启用 4 项自动化规则：\n"
                "1. **自动分类新工单** — 今日已自动处理 12 条\n"
                "2. **重复问题自动回复** — 命中 5 条高频问答\n"
                "3. **高优先级自动升级** — 已升级 2 条至值班负责人\n"
                "4. **材料清单智能校验** — 本月减少重复提交 38 次\n\n"
                "您可以在「洞察与决策」→「AI 自动化」中调整规则开关与阈值。"
            )
        if "流程" in q or "工作流" in q or "状态" in q:
            return (
                "当前有 3 个工作流正在运行：\n"
                "• 工单智能分类（67%）— 预计 3 分钟完成\n"
                "• 舆情情感监测（45%）— 预计 8 分钟完成\n"
                "• 高优先级自动升级（82%）— 预计 1 分钟完成\n\n"
                "另有 1 项已完成（重复问题汇总），1 项等待夜间窗口执行。"
            )
        if "政策" in q or "知识库" in q or "回复" in q:
            return (
                "知识库目前涵盖以下政策领域（本地模拟数据）：\n"
                "• 社保转移与异地就医备案\n"
                "• 房屋租赁备案与不动产登记\n"
                "• 生育津贴与灵活就业参保\n"
                "• 企业年金与营业执照变更\n\n"
                "对于高频咨询问题，AI 已生成标准化话术模板 12 套，可直接用于自动回复或审批建议。"
            )
        if "推荐" in q or "建议" in q or "怎么" in q:
            return (
                "基于当前数据，我建议优先关注以下事项：\n"
                "1. **大厅等候时间**仍是首要痛点（11 条反馈，强度 90），建议推进「动态开窗」优化任务\n"
                "2. **材料重复提交**问题突出，可优先启用「材料清单智能校验」规则\n"
                "3. 今日有 **8** 条高优先级工单未处理，其中 1 条已触发自动升级\n\n"
                "需要我帮您起草具体整改方案或生成回复话术吗？"
            )
        return (
            "您好，我是 SignalFlow 智能助手，可以帮助您：\n"
            "• 查询工单概况与统计数据\n"
            "• 查看 AI 工作流运行状态与自动化规则\n"
            "• 检索政策知识库并生成标准化回复\n"
            "• 提供整改建议与优先级排序\n\n"
            "请问今天需要我协助处理什么？您可以尝试输入「今天工单情况」「自动回复怎么配置」「大厅排队怎么解决」等。"
        )
