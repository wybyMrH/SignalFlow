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
