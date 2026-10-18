"""SignalFlow 演示种子数据脚本。

将前端 mocks 数据翻译为后端 ORM 对象，支持幂等执行（按主键/唯一键去重）。
用法（在 backend 容器内）：
    python -m app.seed
"""

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.feedback import Feedback
from app.models.gov import GovAlertItem, GovHotTopic, GovPolicyNotice
from app.models.insight import InsightTopic
from app.models.interview import InterviewRecord
from app.models.agent import Agent, AgentTool, Skill
from app.models.workflow import Workflow, WorkflowRun
from app.models.roadmap import RoadmapItem, TaskItem, ReplyDraft
from app.models.resource import ServerState, DatabaseState, ApiEndpointState, SystemLogEntry, ResourceAlert
from app.models.setting import ChannelConfig, Setting
from app.models.automation import AutomationRule
from app.models.business import BusinessLead, CommonNeed, MarketSignal

# 确定性 UUID 命名空间（便于重复运行生成同一 UUID）
_NS = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # DNS namespace


def _uuid(key: str) -> uuid.UUID:
    return uuid.uuid5(_NS, key)


def _dt(iso: str | None) -> datetime | None:
    if iso is None:
        return None
    if iso.endswith("Z"):
        iso = iso[:-1] + "+00:00"
    return datetime.fromisoformat(iso)


def _now() -> datetime:
    """当前 UTC 时间（演示数据统一时间基准）。"""
    return datetime.now(timezone.utc)


def _ago(*, days: int = 0, hours: int = 0, minutes: int = 0) -> datetime:
    """相对当前时间向前偏移，保证演示数据始终落在最近时间窗口内。"""
    return _now() - timedelta(days=days, hours=hours, minutes=minutes)


def _at(days_ago: int, hour: int, minute: int) -> datetime:
    """取「最近 N 天」中的某个 UTC 时刻（与前端 mocks 的 mockUtc 口径一致）。"""
    base = _now() - timedelta(days=days_ago)
    return base.replace(hour=hour, minute=minute, second=0, microsecond=0)


def _ref_day(days_ago: int) -> str:
    """source_ref 的 MMDD 日期前缀，与创建时间保持同一天。"""
    return (_now() - timedelta(days=days_ago)).strftime("%m%d")


# 反馈时间相对映射：id -> ((created_days_ago, hour, minute), (updated_days_ago, hour, minute))
# 与 frontend/src/mocks/feedbackDb.ts 的 mockUtc 偏移逐条对齐，保证 8088(mock) 与 5199(seed) 两端一致。
FB_REL_TIME: dict[str, tuple[tuple[int, int, int], tuple[int, int, int]]] = {
    "F1001": ((2, 1, 12), (1, 5, 40)),
    "F1002": ((2, 3, 5), (2, 8, 20)),
    "F1003": ((2, 6, 22), (2, 8, 10)),
    "F1004": ((2, 8, 45), (2, 8, 45)),
    "F1005": ((2, 0, 30), (1, 3, 12)),
    "F1006": ((2, 5, 20), (2, 7, 0)),
    "F1007": ((2, 7, 1), (1, 8, 30)),
    "F1008": ((2, 9, 48), (1, 2, 22)),
    "F1009": ((2, 2, 15), (2, 2, 15)),
    "F1010": ((2, 3, 35), (2, 6, 40)),
    "F1011": ((2, 6, 8), (2, 6, 8)),
    "F1012": ((2, 8, 52), (1, 4, 1)),
    "F1013": ((1, 6, 26), (1, 8, 32)),
    "F1014": ((2, 5, 40), (1, 2, 15)),
    "F1015": ((2, 7, 19), (2, 7, 19)),
    "F1016": ((2, 9, 3), (1, 2, 20)),
    "F1017": ((2, 3, 41), (1, 8, 5)),
    "F1018": ((2, 5, 55), (1, 4, 33)),
    "F1019": ((2, 7, 37), (2, 7, 37)),
    "F1020": ((2, 9, 28), (2, 9, 28)),
    "F1021": ((2, 8, 50), (1, 2, 0)),
    "F1022": ((2, 3, 44), (1, 2, 50)),
    "F1023": ((1, 5, 16), (1, 5, 16)),
    "F1024": ((1, 8, 2), (1, 8, 30)),
    "F1025": ((1, 1, 30), (1, 1, 30)),
    "F1026": ((1, 3, 22), (0, 6, 44)),
    "F1027": ((1, 6, 9), (0, 1, 25)),
    "F1028": ((1, 7, 58), (1, 7, 58)),
    "F1029": ((1, 2, 5), (1, 4, 30)),
    "F1030": ((1, 5, 28), (0, 2, 12)),
    "F1031": ((1, 7, 35), (1, 7, 35)),
    "F1032": ((1, 9, 20), (1, 9, 20)),
    "F1033": ((1, 1, 48), (1, 3, 15)),
    "F1034": ((1, 3, 14), (1, 6, 0)),
    "F1035": ((1, 6, 2), (1, 6, 2)),
    "F1036": ((1, 8, 33), (1, 8, 33)),
    "F1037": ((1, 1, 55), (1, 3, 5)),
    "F1038": ((1, 4, 16), (1, 7, 30)),
    "F1039": ((1, 6, 41), (1, 6, 41)),
    "F1040": ((1, 8, 58), (1, 8, 58)),
    "F1041": ((1, 2, 37), (1, 4, 45)),
    "F1042": ((1, 5, 21), (1, 5, 21)),
    "F1043": ((1, 7, 44), (0, 2, 28)),
    "F1044": ((1, 9, 9), (0, 1, 20)),
    "F1045": ((0, 1, 12), (0, 1, 12)),
    "F1046": ((0, 3, 26), (0, 3, 26)),
    "F1047": ((0, 6, 50), (0, 8, 35)),
    "F1048": ((0, 9, 37), (0, 9, 37)),
    "F1049": ((0, 1, 8), (0, 1, 8)),
    "F1050": ((0, 3, 3), (0, 3, 3)),
    "F1051": ((0, 7, 32), (0, 7, 32)),
    "F1052": ((0, 0, 55), (0, 0, 55)),
    "F1053": ((0, 2, 44), (0, 2, 44)),
    "F1054": ((0, 6, 17), (0, 6, 17)),
    "F1055": ((0, 1, 20), (0, 1, 20)),
    "F1056": ((0, 2, 6), (0, 2, 6)),
    "F1057": ((0, 3, 35), (0, 4, 0)),
    "F1058": ((0, 5, 52), (0, 5, 52)),
    "F1059": ((0, 1, 12), (0, 7, 20)),
    "F1060": ((0, 2, 40), (0, 6, 5)),
    "F1061": ((0, 8, 0), (0, 8, 5)),
    "F1062": ((0, 2, 0), (0, 8, 10)),
    "F1063": ((0, 7, 30), (0, 8, 15)),
    "F1064": ((0, 3, 20), (0, 8, 20)),
    "F1101": ((0, 9, 0), (0, 9, 0)),
    "F1102": ((1, 9, 0), (1, 9, 0)),
    "F1103": ((2, 9, 0), (2, 9, 0)),
    "F1104": ((2, 10, 0), (2, 10, 0)),
}

# 反馈 UUID -> 原始 id，用于把洞察证据时间对齐到对应反馈的创建时间
FB_UUID_TO_ID = {str(_uuid("feedback-%s" % k)): k for k in FB_REL_TIME}


def _fb_created_at(feedback_uuid: str) -> datetime:
    """按反馈 UUID 取该反馈的相对创建时间（找不到时回退到 1 天前）。"""
    fid = FB_UUID_TO_ID.get(str(feedback_uuid))
    return _at(*FB_REL_TIME[fid][0]) if fid else _ago(days=1)


def _seed_feedbacks(session: Session) -> None:
    rows = [
        {"id": "F1001", "tenant_id": "demo-gov", "source": "hotline", "source_ref": "HM-0930-001", "content": "上午九点在一楼大厅排队取号，等了四十分钟才轮到，叫号屏还跳过了好几个号，老人站着干着急。", "author": "王梅", "status": "closed", "sentiment": "negative", "priority": 5, "topic_id": "t2", "topic_title": "大厅等候时间过长", "reviewer": "张莉", "created_at": "2026-09-30T09:12:00Z", "updated_at": "2026-10-02T15:40:00Z", "reply_content": "您好，您反映的“大厅等候时间过长”问题我们已收悉并核实处理，给您带来不便深表歉意。后续我们将持续优化服务流程与体验，感谢您的理解与支持。如有疑问可拨打服务热线详询。", "replied_at": "2026-10-02T15:40:00Z"},
        {"id": "F1002", "tenant_id": "demo-gov", "source": "portal", "source_ref": None, "content": "从东门进来绕了两圈才找到停车场入口，路上没有任何指示牌，办完事出来又找不到车了。", "author": "李强", "status": "resolved", "sentiment": "neutral", "priority": 2, "topic_id": "t7", "topic_title": "停车与指引不清晰", "reviewer": "陈曦", "created_at": "2026-09-30T11:05:00Z", "updated_at": "2026-10-02T09:20:00Z"},
        {"id": "F1003", "tenant_id": "demo-gov", "source": "ticket", "source_ref": "GD-0930-012", "content": "办房屋租赁备案要求提交身份证、房产证、合同原件和复印件，材料上周刚交过一模一样的，这次又要，建议打通材料复用。", "author": "刘芳", "status": "analyzing", "sentiment": "negative", "priority": 4, "topic_id": "t1", "topic_title": "办事材料重复提交", "reviewer": "赵磊", "created_at": "2026-09-30T14:22:00Z", "updated_at": "2026-10-01T10:10:00Z"},
        {"id": "F1004", "tenant_id": "demo-gov", "source": "interview", "source_ref": None, "content": "访谈中多位老人反映：自助取号机字太小、不会操作，也没有志愿者协助，希望能保留人工通道。", "author": "周阿姨", "status": "new", "sentiment": "negative", "priority": 4, "topic_id": "t6", "topic_title": "老年与无障碍服务不足", "reviewer": None, "created_at": "2026-09-30T16:45:00Z", "updated_at": "2026-09-30T16:45:00Z"},
        {"id": "F1005", "tenant_id": "demo-gov", "source": "hotline", "source_ref": "HM-1001-009", "content": "预约系统昨天下单成功，今早到现场却说没查到记录，值班人员电话也打不通，白跑一趟。", "author": "吴晓东", "status": "resolved", "sentiment": "negative", "priority": 4, "topic_id": "t3", "topic_title": "线上预约系统不稳定", "reviewer": "孙浩", "created_at": "2026-10-01T08:30:00Z", "updated_at": "2026-10-02T11:12:00Z"},
        {"id": "F1006", "tenant_id": "demo-gov", "source": "review", "source_ref": "PJ-1001-021", "content": "综合窗口办社保转移中午排了一个多小时，柜台只开两个，其他窗口空着没人。", "author": "郑爽", "status": "analyzing", "sentiment": "negative", "priority": 4, "topic_id": "t2", "topic_title": "大厅等候时间过长", "reviewer": "张莉", "created_at": "2026-10-01T13:20:00Z", "updated_at": "2026-10-02T09:00:00Z"},
        {"id": "F1007", "tenant_id": "demo-gov", "source": "portal", "source_ref": None, "content": "网站上留了咨询企业年金的问题，三天没人回，400 电话也说不清楚，只能再跑一趟。", "author": "钱进", "status": "replied", "sentiment": "neutral", "priority": 3, "topic_id": "t4", "topic_title": "政策咨询响应偏慢", "reviewer": "何静", "created_at": "2026-10-01T15:01:00Z", "updated_at": "2026-10-03T17:30:00Z"},
        {"id": "F1008", "tenant_id": "demo-gov", "source": "ticket", "source_ref": "GD-1001-018", "content": "我的客户 APP 报错提示 token 过期，重装了三次还是闪退，iPhone 15 最新系统。", "author": "冯嘉", "status": "closed", "sentiment": "negative", "priority": 4, "topic_id": "t8", "topic_title": "移动端 APP 操作不便", "reviewer": "孙浩", "created_at": "2026-10-01T17:48:00Z", "updated_at": "2026-10-05T10:22:00Z"},
        {"id": "F1009", "tenant_id": "demo-gov", "source": "review", "source_ref": "PJ-1002-005", "content": "今天窗口的小伙子态度很好，把医保报销需要的材料一条条列给我，办得很顺利，点赞。", "author": "孙秀英", "status": "resolved", "sentiment": "positive", "priority": 1, "topic_id": "t5", "topic_title": "窗口服务体验不一", "reviewer": None, "created_at": "2026-10-02T10:15:00Z", "updated_at": "2026-10-02T10:15:00Z"},
        {"id": "F1010", "tenant_id": "demo-gov", "source": "hotline", "source_ref": "HM-1002-013", "content": "办营业执照变更，窗口说缺场地证明，可我在网上传过了，线下打印件又不认，重复交材料。", "author": "许峰", "status": "analyzing", "sentiment": "negative", "priority": 4, "topic_id": "t1", "topic_title": "办事材料重复提交", "reviewer": "赵磊", "created_at": "2026-10-02T11:35:00Z", "updated_at": "2026-10-03T09:40:00Z"},
        {"id": "F1011", "tenant_id": "demo-gov", "source": "portal", "source_ref": None, "content": "线上预约提交后页面一直转圈，刷新后发现约的时段被改了，差点错过办理日期。", "author": "何俊", "status": "new", "sentiment": "negative", "priority": 4, "topic_id": "t3", "topic_title": "线上预约系统不稳定", "reviewer": None, "created_at": "2026-10-02T14:08:00Z", "updated_at": "2026-10-02T14:08:00Z"},
        {"id": "F1012", "tenant_id": "demo-gov", "source": "sales", "source_ref": None, "content": "客户现场走访反馈：停车引导确实混乱，商务洽谈客户第一次来基本都要打电话问路。", "author": "罗成", "status": "closed", "sentiment": "neutral", "priority": 2, "topic_id": "t7", "topic_title": "停车与指引不清晰", "reviewer": "陈曦", "created_at": "2026-10-02T16:52:00Z", "updated_at": "2026-10-04T10:01:00Z"},
        {"id": "F1013", "tenant_id": "demo-gov", "source": "ticket", "source_ref": "GD-1003-007", "content": "社保窗口周末排长队，取号系统显示前面还有 68 人，实际等候接近两小时。", "author": "黄敏", "status": "closed", "sentiment": "negative", "priority": 5, "topic_id": "t2", "topic_title": "大厅等候时间过长", "reviewer": "张莉", "created_at": "2026-10-03T10:26:00Z", "updated_at": "2026-10-06T14:32:00Z"},
        {"id": "F1014", "tenant_id": "demo-gov", "source": "interview", "source_ref": None, "content": "访谈记录：老年人大厅办理业务平均比年轻人多花 20 分钟，主要卡在填表和手机操作环节。", "author": "周阿姨", "status": "resolved", "sentiment": "neutral", "priority": 3, "topic_id": "t6", "topic_title": "老年与无障碍服务不足", "reviewer": "何静", "created_at": "2026-10-03T13:40:00Z", "updated_at": "2026-10-07T09:15:00Z"},
        {"id": "F1015", "tenant_id": "demo-gov", "source": "hotline", "source_ref": "HM-1003-022", "content": "咨询生育津贴申领条件，热线转了三个人，等了两天没人回电话，政策解读口径不一。", "author": "孟凡", "status": "new", "sentiment": "negative", "priority": 3, "topic_id": "t4", "topic_title": "政策咨询响应偏慢", "reviewer": None, "created_at": "2026-10-03T15:19:00Z", "updated_at": "2026-10-03T15:19:00Z"},
        {"id": "F1016", "tenant_id": "demo-gov", "source": "review", "source_ref": "PJ-1003-014", "content": "新版 APP 预约入口藏在二级菜单里，字号小，操作流程比旧版多了三步。", "author": "秦朗", "status": "analyzing", "sentiment": "negative", "priority": 3, "topic_id": "t8", "topic_title": "移动端 APP 操作不便", "reviewer": "孙浩", "created_at": "2026-10-03T17:03:00Z", "updated_at": "2026-10-04T11:20:00Z"},
        {"id": "F1017", "tenant_id": "demo-gov", "source": "portal", "source_ref": None, "content": "同一套材料在三个窗口各交一遍，前台说系统没打通，建议部门间共享材料库。", "author": "宋佳", "status": "resolved", "sentiment": "negative", "priority": 4, "topic_id": "t1", "topic_title": "办事材料重复提交", "reviewer": "赵磊", "created_at": "2026-10-04T09:41:00Z", "updated_at": "2026-10-08T16:05:00Z"},
        {"id": "F1018", "tenant_id": "demo-gov", "source": "hotline", "source_ref": "HM-1004-016", "content": "窗口工作人员解答耐心，但不同窗口对同一问题说法不一样，建议统一培训口径。", "author": "唐丽", "status": "replied", "sentiment": "neutral", "priority": 2, "topic_id": "t5", "topic_title": "窗口服务体验不一", "reviewer": "陈曦", "created_at": "2026-10-04T11:55:00Z", "updated_at": "2026-10-06T10:33:00Z"},
        {"id": "F1019", "tenant_id": "demo-gov", "source": "review", "source_ref": "PJ-1004-009", "content": "预约页选择时段后提示库存不足，反复重试三次才成功，体验很差。", "author": "魏然", "status": "new", "sentiment": "negative", "priority": 3, "topic_id": "t3", "topic_title": "线上预约系统不稳定", "reviewer": None, "created_at": "2026-10-04T13:37:00Z", "updated_at": "2026-10-04T13:37:00Z"},
        {"id": "F1020", "tenant_id": "demo-gov", "source": "sales", "source_ref": None, "content": "重点企业走访：企业对绿色通道服务满意，希望把定制化办理推广到更多事项。", "author": "罗成", "status": "resolved", "sentiment": "positive", "priority": 1, "topic_id": "t2", "topic_title": "大厅等候时间过长", "reviewer": None, "created_at": "2026-10-04T15:28:00Z", "updated_at": "2026-10-04T15:28:00Z"},
        {"id": "F1021", "tenant_id": "demo-gov", "source": "ticket", "source_ref": "GD-1005-011", "content": "东门停车场夜间照明不足，地面车位线磨损看不清，容易刮蹭。", "author": "段鹏", "status": "closed", "sentiment": "neutral", "priority": 2, "topic_id": "t7", "topic_title": "停车与指引不清晰", "reviewer": "陈曦", "created_at": "2026-10-05T08:50:00Z", "updated_at": "2026-10-09T10:00:00Z"},
        {"id": "F1022", "tenant_id": "demo-gov", "source": "review", "source_ref": "PJ-1005-017", "content": "公积金政策页写的和窗口执行的不一致，被工作人员要求按新口径补材料。", "author": "林芳", "status": "analyzing", "sentiment": "negative", "priority": 3, "topic_id": "t4", "topic_title": "政策咨询响应偏慢", "reviewer": "何静", "created_at": "2026-10-05T10:44:00Z", "updated_at": "2026-10-06T09:50:00Z"},
        {"id": "F1023", "tenant_id": "demo-gov", "source": "portal", "source_ref": None, "content": "残疾人通道入口常年锁着，轮椅用户只能绕到正门，建议在门户上标注无障碍路线。", "author": "龚平", "status": "new", "sentiment": "negative", "priority": 4, "topic_id": "t6", "topic_title": "老年与无障碍服务不足", "reviewer": None, "created_at": "2026-10-05T13:16:00Z", "updated_at": "2026-10-05T13:16:00Z"},
        {"id": "F1024", "tenant_id": "demo-gov", "source": "hotline", "source_ref": "HM-1005-027", "content": "灵活就业参保材料清单线上线下不一致，线下要求的多一份委托书，来回折腾。", "author": "曹阳", "status": "analyzing", "sentiment": "negative", "priority": 4, "topic_id": "t1", "topic_title": "办事材料重复提交", "reviewer": "赵磊", "created_at": "2026-10-05T16:02:00Z", "updated_at": "2026-10-06T14:10:00Z"},
        {"id": "F1025", "tenant_id": "demo-gov", "source": "interview", "source_ref": None, "content": "回访：三成受访者对大厅等待时长不满，高峰时段取号后无排队进度提醒。", "author": "访谈组", "status": "new", "sentiment": "negative", "priority": 5, "topic_id": "t2", "topic_title": "大厅等候时间过长", "reviewer": None, "created_at": "2026-10-06T09:30:00Z", "updated_at": "2026-10-06T09:30:00Z"},
        {"id": "F1026", "tenant_id": "demo-gov", "source": "portal", "source_ref": None, "content": "APP 人脸识别在强光下无法通过，每次办理都要试四五次，建议增加手动验证。", "author": "叶青", "status": "resolved", "sentiment": "negative", "priority": 3, "topic_id": "t8", "topic_title": "移动端 APP 操作不便", "reviewer": "孙浩", "created_at": "2026-10-06T11:22:00Z", "updated_at": "2026-10-09T15:44:00Z"},
        {"id": "F1027", "tenant_id": "demo-gov", "source": "ticket", "source_ref": "GD-1006-003", "content": "综合窗口叫号顺序偶尔和取号时间不一致，短号后到却先办，引发排队不满。", "author": "韩雪", "status": "replied", "sentiment": "neutral", "priority": 3, "topic_id": "t5", "topic_title": "窗口服务体验不一", "reviewer": "陈曦", "created_at": "2026-10-06T14:09:00Z", "updated_at": "2026-10-08T09:25:00Z"},
        {"id": "F1028", "tenant_id": "demo-gov", "source": "hotline", "source_ref": "HM-1006-019", "content": "预约后系统未发短信提醒，到大厅才发现预约被取消，说是系统默认超时释放。", "author": "顾全", "status": "new", "sentiment": "negative", "priority": 4, "topic_id": "t3", "topic_title": "线上预约系统不稳定", "reviewer": None, "created_at": "2026-10-06T15:58:00Z", "updated_at": "2026-10-06T15:58:00Z"},
        {"id": "F1029", "tenant_id": "demo-gov", "source": "review", "source_ref": "PJ-1007-006", "content": "办理不动产登记，材料清单上十项材料有六项是重复提交过，历史数据应该能复用。", "author": "邵峰", "status": "analyzing", "sentiment": "negative", "priority": 4, "topic_id": "t1", "topic_title": "办事材料重复提交", "reviewer": "赵磊", "created_at": "2026-10-07T10:05:00Z", "updated_at": "2026-10-08T10:30:00Z"},
        {"id": "F1030", "tenant_id": "demo-gov", "source": "ticket", "source_ref": "GD-1007-015", "content": "咨询异地就医备案，提交后 5 个工作日才回复，期间病人都已经出院了。", "author": "于华", "status": "resolved", "sentiment": "neutral", "priority": 3, "topic_id": "t4", "topic_title": "政策咨询响应偏慢", "reviewer": "何静", "created_at": "2026-10-07T13:28:00Z", "updated_at": "2026-10-10T11:12:00Z"},
        {"id": "F1031", "tenant_id": "demo-gov", "source": "portal", "source_ref": None, "content": "高峰期取号后显示等待 120 分钟，实际等了 150 分钟，等候屏更新时间不实时。", "author": "章悦", "status": "new", "sentiment": "negative", "priority": 4, "topic_id": "t2", "topic_title": "大厅等候时间过长", "reviewer": None, "created_at": "2026-10-07T15:35:00Z", "updated_at": "2026-10-07T15:35:00Z"},
        {"id": "F1032", "tenant_id": "demo-gov", "source": "hotline", "source_ref": "HM-1007-024", "content": "帮八十岁母亲办高龄补贴，窗口要求用手机操作，老人没有智能手机，需要代办服务。", "author": "薛燕", "status": "new", "sentiment": "negative", "priority": 4, "topic_id": "t6", "topic_title": "老年与无障碍服务不足", "reviewer": None, "created_at": "2026-10-07T17:20:00Z", "updated_at": "2026-10-07T17:20:00Z"},
        {"id": "F1033", "tenant_id": "demo-gov", "source": "interview", "source_ref": None, "content": "用户访谈：年轻人普遍能接受线上办理，但觉得 APP 步骤繁琐，常用功能要翻三层。", "author": "访谈组", "status": "analyzing", "sentiment": "negative", "priority": 3, "topic_id": "t8", "topic_title": "移动端 APP 操作不便", "reviewer": "孙浩", "created_at": "2026-10-08T09:48:00Z", "updated_at": "2026-10-09T09:15:00Z"},
        {"id": "F1034", "tenant_id": "demo-gov", "source": "portal", "source_ref": None, "content": "预约改签功能不可用，只能取消重约，高峰时段基本抢不到号。", "author": "钟磊", "status": "closed", "sentiment": "neutral", "priority": 3, "topic_id": "t3", "topic_title": "线上预约系统不稳定", "reviewer": "孙浩", "created_at": "2026-10-08T11:14:00Z", "updated_at": "2026-10-11T10:00:00Z"},
        {"id": "F1035", "tenant_id": "demo-gov", "source": "hotline", "source_ref": "HM-1008-020", "content": "今天遇到的热线客服非常专业，主动帮忙预约了复诊号，还提醒我带齐材料。", "author": "程雪", "status": "resolved", "sentiment": "positive", "priority": 1, "topic_id": "t5", "topic_title": "窗口服务体验不一", "reviewer": None, "created_at": "2026-10-08T14:02:00Z", "updated_at": "2026-10-08T14:02:00Z"},
        {"id": "F1036", "tenant_id": "demo-gov", "source": "ticket", "source_ref": "GD-1008-004", "content": "个体户年报材料与税务部门要求不一致，两部门互不认账，要求纸质件重新提交。", "author": "贾宁", "status": "new", "sentiment": "negative", "priority": 4, "topic_id": "t1", "topic_title": "办事材料重复提交", "reviewer": None, "created_at": "2026-10-08T16:33:00Z", "updated_at": "2026-10-08T16:33:00Z"},
        {"id": "F1037", "tenant_id": "demo-gov", "source": "review", "source_ref": "PJ-1009-012", "content": "十一后第一天大厅爆满，叫号系统卡顿，等了一个小时发现号被叫过没人应。", "author": "戴琳", "status": "analyzing", "sentiment": "negative", "priority": 5, "topic_id": "t2", "topic_title": "大厅等候时间过长", "reviewer": "张莉", "created_at": "2026-10-09T09:55:00Z", "updated_at": "2026-10-10T10:05:00Z"},
        {"id": "F1038", "tenant_id": "demo-gov", "source": "portal", "source_ref": None, "content": "北门停车场没有电子余位屏，高峰期在门口排队等位，建议接入系统实时显示。", "author": "石磊", "status": "resolved", "sentiment": "neutral", "priority": 2, "topic_id": "t7", "topic_title": "停车与指引不清晰", "reviewer": "陈曦", "created_at": "2026-10-09T12:16:00Z", "updated_at": "2026-10-11T15:30:00Z"},
        {"id": "F1039", "tenant_id": "demo-gov", "source": "hotline", "source_ref": "HM-1009-026", "content": "咨询创业补贴政策，热线只给了网址让自行查看，没有直接解答，感受敷衍。", "author": "彭飞", "status": "new", "sentiment": "negative", "priority": 3, "topic_id": "t4", "topic_title": "政策咨询响应偏慢", "reviewer": None, "created_at": "2026-10-09T14:41:00Z", "updated_at": "2026-10-09T14:41:00Z"},
        {"id": "F1040", "tenant_id": "demo-gov", "source": "ticket", "source_ref": "GD-1009-009", "content": "无障碍电梯在检修期未提前公示，轮椅用户到了现场才知道，白跑一趟。", "author": "谭芳", "status": "new", "sentiment": "negative", "priority": 4, "topic_id": "t6", "topic_title": "老年与无障碍服务不足", "reviewer": None, "created_at": "2026-10-09T16:58:00Z", "updated_at": "2026-10-09T16:58:00Z"},
        {"id": "F1041", "tenant_id": "demo-gov", "source": "hotline", "source_ref": "HM-1010-017", "content": "预约时段被系统自动重排，致电热线确认又说以现场为准，两个口径不一致。", "author": "熊伟", "status": "analyzing", "sentiment": "negative", "priority": 4, "topic_id": "t3", "topic_title": "线上预约系统不稳定", "reviewer": "孙浩", "created_at": "2026-10-10T10:37:00Z", "updated_at": "2026-10-11T09:45:00Z"},
        {"id": "F1042", "tenant_id": "demo-gov", "source": "portal", "source_ref": None, "content": "材料清单页显示云盘上传成功，窗口却说系统里没有，要求重新上传打印。", "author": "姜伟", "status": "new", "sentiment": "negative", "priority": 4, "topic_id": "t1", "topic_title": "办事材料重复提交", "reviewer": None, "created_at": "2026-10-10T13:21:00Z", "updated_at": "2026-10-10T13:21:00Z"},
        {"id": "F1043", "tenant_id": "demo-gov", "source": "ticket", "source_ref": "GD-1010-013", "content": "周六上午医保窗口只开一个，排队时长破纪录，建议按预约量动态开窗。", "author": "苏娟", "status": "resolved", "sentiment": "negative", "priority": 4, "topic_id": "t2", "topic_title": "大厅等候时间过长", "reviewer": "张莉", "created_at": "2026-10-10T15:44:00Z", "updated_at": "2026-10-13T10:28:00Z"},
        {"id": "F1044", "tenant_id": "demo-gov", "source": "review", "source_ref": "PJ-1010-008", "content": "窗口回复标准不一，同一问题两个窗口给了两种答案，希望统一服务话术。", "author": "黎敏", "status": "replied", "sentiment": "neutral", "priority": 2, "topic_id": "t5", "topic_title": "窗口服务体验不一", "reviewer": "陈曦", "created_at": "2026-10-10T17:09:00Z", "updated_at": "2026-10-12T14:20:00Z"},
        {"id": "F1045", "tenant_id": "demo-gov", "source": "portal", "source_ref": None, "content": "APP 版本更新后消息通知全部失效，办事进度只能到大厅看，毫无线上体验。", "author": "范宁", "status": "new", "sentiment": "negative", "priority": 3, "topic_id": "t8", "topic_title": "移动端 APP 操作不便", "reviewer": None, "created_at": "2026-10-11T09:12:00Z", "updated_at": "2026-10-11T09:12:00Z"},
        {"id": "F1046", "tenant_id": "demo-gov", "source": "hotline", "source_ref": "HM-1011-021", "content": "热线咨询公租房申请，答复说等公示，但公示时间地点都没有告知，信息不透明。", "author": "任杰", "status": "new", "sentiment": "negative", "priority": 3, "topic_id": "t4", "topic_title": "政策咨询响应偏慢", "reviewer": None, "created_at": "2026-10-11T11:26:00Z", "updated_at": "2026-10-11T11:26:00Z"},
        {"id": "F1047", "tenant_id": "demo-gov", "source": "review", "source_ref": "PJ-1011-011", "content": "房产过户材料线上线下两份清单，线上说免提交的线下仍要纸质，体验割裂。", "author": "尹莉", "status": "analyzing", "sentiment": "negative", "priority": 4, "topic_id": "t1", "topic_title": "办事材料重复提交", "reviewer": "赵磊", "created_at": "2026-10-11T14:50:00Z", "updated_at": "2026-10-12T09:35:00Z"},
        {"id": "F1048", "tenant_id": "demo-gov", "source": "ticket", "source_ref": "GD-1011-016", "content": "教育部门与民政部门材料不通用，办理同一家庭业务要分别提交两套证明。", "author": "洪波", "status": "new", "sentiment": "negative", "priority": 4, "topic_id": "t2", "topic_title": "大厅等候时间过长", "reviewer": None, "created_at": "2026-10-11T17:37:00Z", "updated_at": "2026-10-11T17:37:00Z"},
        {"id": "F1049", "tenant_id": "demo-gov", "source": "hotline", "source_ref": "HM-1012-018", "content": "线上预约系统凌晨维护后数据回滚，白天的预约记录全部丢失，窗口不认补打的凭证。", "author": "牛丽", "status": "new", "sentiment": "negative", "priority": 5, "topic_id": "t3", "topic_title": "线上预约系统不稳定", "reviewer": None, "created_at": "2026-10-12T09:08:00Z", "updated_at": "2026-10-12T09:08:00Z"},
        {"id": "F1050", "tenant_id": "demo-gov", "source": "ticket", "source_ref": "GD-1012-008", "content": "窗口 AB 岗交接不清，上午受理的单子下午另一个窗口不认，要求重新排队。", "author": "夏雨", "status": "new", "sentiment": "negative", "priority": 3, "topic_id": "t5", "topic_title": "窗口服务体验不一", "reviewer": None, "created_at": "2026-10-12T11:03:00Z", "updated_at": "2026-10-12T11:03:00Z"},
        {"id": "F1051", "tenant_id": "demo-gov", "source": "portal", "source_ref": None, "content": "线上提交的电子签章线下不认可，要求重新盖章签字，数字化等于没做。", "author": "董洁", "status": "new", "sentiment": "negative", "priority": 4, "topic_id": "t1", "topic_title": "办事材料重复提交", "reviewer": None, "created_at": "2026-10-12T15:32:00Z", "updated_at": "2026-10-12T15:32:00Z"},
        {"id": "F1052", "tenant_id": "demo-gov", "source": "hotline", "source_ref": "HM-1013-023", "content": "早上八点四十到大厅，取号机前已经排了 30 人，开门前没有分流引导。", "author": "白帆", "status": "new", "sentiment": "negative", "priority": 4, "topic_id": "t2", "topic_title": "大厅等候时间过长", "reviewer": None, "created_at": "2026-10-13T08:55:00Z", "updated_at": "2026-10-13T08:55:00Z"},
        {"id": "F1053", "tenant_id": "demo-gov", "source": "review", "source_ref": "PJ-1013-007", "content": "昨日门户政策问答回复已读未回，今天热线又问了一遍，答复内容还不一致。", "author": "万琳", "status": "new", "sentiment": "negative", "priority": 3, "topic_id": "t4", "topic_title": "政策咨询响应偏慢", "reviewer": None, "created_at": "2026-10-13T10:44:00Z", "updated_at": "2026-10-13T10:44:00Z"},
        {"id": "F1054", "tenant_id": "demo-gov", "source": "portal", "source_ref": None, "content": "官方网站无障碍模式开关找不到，读屏软件无法朗读办理须知，视障用户无法使用。", "author": "欧阳", "status": "new", "sentiment": "neutral", "priority": 4, "topic_id": "t6", "topic_title": "老年与无障碍服务不足", "reviewer": None, "created_at": "2026-10-13T14:17:00Z", "updated_at": "2026-10-13T14:17:00Z"},
        {"id": "F1055", "tenant_id": "demo-gov", "source": "hotline", "source_ref": "HM-1014-003", "content": "今天大厅叫号系统故障，工作人员手工登记排队，秩序混乱，等了近一小时。", "author": "余凯", "status": "new", "sentiment": "negative", "priority": 5, "topic_id": "t2", "topic_title": "大厅等候时间过长", "reviewer": None, "created_at": "2026-10-14T09:20:00Z", "updated_at": "2026-10-14T09:20:00Z"},
        {"id": "F1056", "tenant_id": "demo-gov", "source": "ticket", "source_ref": "GD-1014-002", "content": "APP 适老化模式开启后字号仍偏小，按钮点击区域不足，建议优化大字号布局。", "author": "马玉", "status": "new", "sentiment": "negative", "priority": 3, "topic_id": "t8", "topic_title": "移动端 APP 操作不便", "reviewer": None, "created_at": "2026-10-14T10:06:00Z", "updated_at": "2026-10-14T10:06:00Z"},
        {"id": "F1057", "tenant_id": "demo-gov", "source": "portal", "source_ref": None, "content": "线上提交电子材料成功后窗口仍要求纸质件，材料复用机制需要真正落地。", "author": "龙飞", "status": "analyzing", "sentiment": "negative", "priority": 4, "topic_id": "t1", "topic_title": "办事材料重复提交", "reviewer": "赵磊", "created_at": "2026-10-14T11:35:00Z", "updated_at": "2026-10-14T12:00:00Z"},
        {"id": "F1058", "tenant_id": "demo-gov", "source": "review", "source_ref": "PJ-1014-004", "content": "改签功能依然报错，试了三次都没成功，只能到窗口重新取号办理。", "author": "方婷", "status": "new", "sentiment": "negative", "priority": 4, "topic_id": "t3", "topic_title": "线上预约系统不稳定", "reviewer": None, "created_at": "2026-10-14T13:52:00Z", "updated_at": "2026-10-14T13:52:00Z"},
        {"id": "F1059", "tenant_id": "demo-gov", "source": "hotline", "source_ref": "HM-1014-010", "content": "上午反映的叫号跳号问题，下午热线回电确认已修复，处理效率值得肯定。", "author": "王梅", "status": "resolved", "sentiment": "positive", "priority": 2, "topic_id": "t5", "topic_title": "窗口服务体验不一", "reviewer": "陈曦", "created_at": "2026-10-14T09:12:00Z", "updated_at": "2026-10-14T15:20:00Z"},
        {"id": "F1060", "tenant_id": "demo-gov", "source": "ticket", "source_ref": "GD-1014-005", "content": "咨询材料补正问题，窗口当天答复并给出清单，问题已解决。", "author": "陆超", "status": "resolved", "sentiment": "positive", "priority": 2, "topic_id": "t1", "topic_title": "办事材料重复提交", "reviewer": "赵磊", "created_at": "2026-10-14T10:40:00Z", "updated_at": "2026-10-14T14:05:00Z"},
        {"id": "F1061", "tenant_id": "demo-gov", "source": "portal", "source_ref": None, "content": "请问社保转移需要哪些材料？我已经在原参保地开了凭证，接下来怎么操作？", "author": "郑明", "status": "ai_reviewing", "sentiment": "neutral", "priority": 2, "topic_id": "t4", "topic_title": "政策咨询响应偏慢", "reviewer": "AI助手", "created_at": "2026-10-14T16:00:00Z", "updated_at": "2026-10-14T16:05:00Z"},
        {"id": "F1062", "tenant_id": "demo-gov", "source": "hotline", "source_ref": "HM-1014-030", "content": "大厅排队时间太长了，每次都等一个多小时，能不能多开几个窗口？", "author": "林晓", "status": "ai_replied", "sentiment": "negative", "priority": 4, "topic_id": "t2", "topic_title": "大厅等候时间过长", "reviewer": "AI自动审批", "created_at": "2026-10-14T10:00:00Z", "updated_at": "2026-10-14T16:10:00Z", "reply_content": "您好，您反映的“大厅等候时间过长”问题我们已收悉并核实处理，给您带来不便深表歉意。后续我们将持续优化服务流程与体验，感谢您的理解与支持。如有疑问可拨打服务热线详询。", "replied_at": "2026-10-14T16:10:00Z"},
        {"id": "F1063", "tenant_id": "demo-gov", "source": "portal", "source_ref": None, "content": "我想咨询一下生育津贴的申领条件，需要连续缴费多久？", "author": "周婷", "status": "ai_reviewing", "sentiment": "neutral", "priority": 2, "topic_id": "t4", "topic_title": "政策咨询响应偏慢", "reviewer": "AI助手", "created_at": "2026-10-14T15:30:00Z", "updated_at": "2026-10-14T16:15:00Z"},
        {"id": "F1064", "tenant_id": "demo-gov", "source": "ticket", "source_ref": "GD-1014-020", "content": "APP 闪退问题怎么处理？已经更新了最新版本还是不行。", "author": "吴刚", "status": "ai_replied", "sentiment": "negative", "priority": 3, "topic_id": "t8", "topic_title": "移动端 APP 操作不便", "reviewer": "AI自动审批", "created_at": "2026-10-14T11:20:00Z", "updated_at": "2026-10-14T16:20:00Z", "reply_content": "您好，您反映的“移动端 APP 操作不便”问题我们已收悉并核实处理，给您带来不便深表歉意。后续我们将持续优化服务流程与体验，感谢您的理解与支持。如有疑问可拨打服务热线详询。", "replied_at": "2026-10-14T16:20:00Z"},
        {"id": "F1101", "tenant_id": "demo-ent", "source": "sales", "source_ref": None, "content": "我们公司有 400 多名设计师，现在每人单独建账号太麻烦，希望支持批量导入和角色分组。", "author": "林倩", "status": "analyzing", "sentiment": "neutral", "priority": 4, "topic_id": "t9", "topic_title": "企业批量账号管理", "reviewer": "商务组", "created_at": "2026-10-12T09:00:00Z", "updated_at": "2026-10-12T09:00:00Z"},
        {"id": "F1102", "tenant_id": "demo-ent", "source": "sales", "source_ref": None, "content": "作为外包承接方，客户要求我们提供本地化部署版本，敏感数据不能出我们的机房。", "author": "陈奕帆", "status": "analyzing", "sentiment": "neutral", "priority": 5, "topic_id": "t10", "topic_title": "私有化部署需求", "reviewer": "商务组", "created_at": "2026-10-11T09:00:00Z", "updated_at": "2026-10-11T09:00:00Z"},
        {"id": "F1103", "tenant_id": "demo-ent", "source": "sales", "source_ref": None, "content": "我们是省属国企，需要和内部 OA、统一认证对接，账号体系要对齐集团标准。", "author": "孙杰", "status": "analyzing", "sentiment": "neutral", "priority": 4, "topic_id": "t11", "topic_title": "统一认证对接", "reviewer": "商务组", "created_at": "2026-10-10T09:00:00Z", "updated_at": "2026-10-10T09:00:00Z"},
        {"id": "F1104", "tenant_id": "demo-ent", "source": "sales", "source_ref": None, "content": "当前产品缺少审计日志导出，合规团队要求完整操作留痕，否则无法过等保三级。", "author": "周敏", "status": "analyzing", "sentiment": "negative", "priority": 5, "topic_id": "t12", "topic_title": "审计日志与合规", "reviewer": "商务组", "created_at": "2026-10-09T09:00:00Z", "updated_at": "2026-10-09T09:00:00Z"},
    ]
    for r in rows:
        uid = _uuid(f"feedback-{r['id']}")
        existing = session.execute(select(Feedback).where(Feedback.id == uid)).scalar()
        if existing:
            continue
        # 时间与 source_ref 相对生成，保证反馈始终落在最近三天（与前端 mocks 口径一致）
        created_rel, updated_rel = FB_REL_TIME[r["id"]]
        source_ref = r.get("source_ref")
        if source_ref:
            parts = source_ref.rsplit("-", 2)
            source_ref = f"{parts[0]}-{_ref_day(created_rel[0])}-{parts[-1]}"
        session.add(Feedback(
            id=uid,
            code=r["id"],
            tenant_id=r["tenant_id"],
            source=r["source"],
            source_ref=source_ref,
            content=r["content"],
            author=r.get("author"),
            status=r["status"],
            sentiment=r.get("sentiment"),
            priority=r.get("priority", 0),
            topic_id=r.get("topic_id"),
            topic_title=r.get("topic_title"),
            reviewer=r.get("reviewer"),
            reply_content=r.get("reply_content"),
            replied_at=_at(*updated_rel) if r.get("replied_at") else None,
            created_at=_at(*created_rel),
            updated_at=_at(*updated_rel),
        ))
    session.commit()
    print(f"[seed] feedbacks upsert done")


def _seed_insight_topics(session: Session) -> None:
    if session.execute(select(InsightTopic).limit(1)).scalar():
        print("[seed] insight_topics already seeded, skip")
        return
    topics = [
        {
            "id": "t1", "title": "办事材料重复提交", "short": "材料复用未落地，线上线下清单不一致", "feedback_count": 8, "customer_count": 8, "trend": "up", "strength": 82, "priority_score": 88,
            "score_card": {"total": 88, "max": 100, "level": "critical", "dimensions": [{"key": "impact", "label": "影响面", "score": 22, "max": 25, "note": "涉及不动产/社保/企业注册等多事项"}, {"key": "urgency", "label": "紧迫度", "score": 23, "max": 25, "note": "近 7 天反馈上升 18%"}, {"key": "feasibility", "label": "可行性", "score": 20, "max": 25, "note": "材料库共享为既有规划"}, {"key": "severity", "label": "严重度", "score": 23, "max": 25, "note": "线下要求与线上申报冲突"}]},
            "evidence": [{"feedback_id": str(_uuid("feedback-F1010")), "excerpt": "办营业执照变更，窗口说缺场地证明，可我在网上传过了...", "author": "许峰", "source": "hotline", "created_at": "2026-10-02T11:35:00Z", "sentiment": "negative"}],
        },
        {
            "id": "t2", "title": "大厅等候时间过长", "short": "高峰排队超 1 小时，动态开窗不足", "feedback_count": 10, "customer_count": 9, "trend": "up", "strength": 90, "priority_score": 92,
            "score_card": {"total": 92, "max": 100, "level": "critical", "dimensions": [{"key": "impact", "label": "影响面", "score": 24, "max": 25, "note": "涉社保/医保等高频窗口"}, {"key": "urgency", "label": "紧迫度", "score": 24, "max": 25, "note": "节假日高峰连续爆满"}, {"key": "feasibility", "label": "可行性", "score": 22, "max": 25, "note": "预约量驱动动态开窗可行"}, {"key": "severity", "label": "严重度", "score": 22, "max": 25, "note": "叫号系统故障放大不满"}]},
            "evidence": [{"feedback_id": str(_uuid("feedback-F1001")), "excerpt": "上午九点在一楼大厅排队取号，等了四十分钟才轮到...", "author": "王梅", "source": "hotline", "created_at": "2026-09-30T09:12:00Z", "sentiment": "negative"}],
        },
        {
            "id": "t3", "title": "线上预约系统不稳定", "short": "预约丢失/改签失败，短信提醒缺失", "feedback_count": 7, "customer_count": 7, "trend": "up", "strength": 74, "priority_score": 80,
            "score_card": {"total": 80, "max": 100, "level": "high", "dimensions": [{"key": "impact", "label": "影响面", "score": 19, "max": 25, "note": "影响预约全链路"}, {"key": "urgency", "label": "紧迫度", "score": 21, "max": 25, "note": "凌晨维护回滚丢数据"}, {"key": "feasibility", "label": "可行性", "score": 20, "max": 25, "note": "容灾与消息补发可快速修复"}, {"key": "severity", "label": "严重度", "score": 20, "max": 25, "note": "白跑一趟风险高"}]},
            "evidence": [{"feedback_id": str(_uuid("feedback-F1005")), "excerpt": "预约系统昨天下单成功，今早到现场却说没查到记录...", "author": "吴晓东", "source": "hotline", "created_at": "2026-10-01T08:30:00Z", "sentiment": "negative"}],
        },
        {
            "id": "t4", "title": "政策咨询响应偏慢", "short": "热线转接多、口径不一，答复超时", "feedback_count": 6, "customer_count": 6, "trend": "flat", "strength": 68, "priority_score": 72,
            "score_card": {"total": 72, "max": 100, "level": "high", "dimensions": [{"key": "impact", "label": "影响面", "score": 18, "max": 25, "note": "涉及政策解读多口径"}, {"key": "urgency", "label": "紧迫度", "score": 18, "max": 25, "note": "5 个工作日才回复"}, {"key": "feasibility", "label": "可行性", "score": 19, "max": 25, "note": "知识库问答可标准化"}, {"key": "severity", "label": "严重度", "score": 17, "max": 25, "note": "信息不透明易引发投诉"}]},
            "evidence": [{"feedback_id": str(_uuid("feedback-F1007")), "excerpt": "网站上留了咨询企业年金的问题，三天没人回...", "author": "钱进", "source": "portal", "created_at": "2026-10-01T15:01:00Z", "sentiment": "neutral"}],
        },
        {
            "id": "t5", "title": "窗口服务体验不一", "short": "AB 岗交接不清，答复口径不统一", "feedback_count": 5, "customer_count": 5, "trend": "flat", "strength": 58, "priority_score": 62,
            "score_card": {"total": 62, "max": 100, "level": "medium", "dimensions": [{"key": "impact", "label": "影响面", "score": 16, "max": 25, "note": "窗口服务标准化缺失"}, {"key": "urgency", "label": "紧迫度", "score": 15, "max": 25, "note": "正面评价同时存在，非线性恶化"}, {"key": "feasibility", "label": "可行性", "score": 16, "max": 25, "note": "话术与交接规范易落地"}, {"key": "severity", "label": "严重度", "score": 15, "max": 25, "note": "重复排队引发二次投诉"}]},
            "evidence": [{"feedback_id": str(_uuid("feedback-F1009")), "excerpt": "今天窗口的小伙子态度很好，把医保报销需要的材料一条条列给我...", "author": "孙秀英", "source": "review", "created_at": "2026-10-02T10:15:00Z", "sentiment": "positive"}],
        },
        {
            "id": "t6", "title": "老年与无障碍服务不足", "short": "适老化操作缺失，无障碍通道管理弱", "feedback_count": 5, "customer_count": 5, "trend": "up", "strength": 55, "priority_score": 70,
            "score_card": {"total": 70, "max": 100, "level": "high", "dimensions": [{"key": "impact", "label": "影响面", "score": 17, "max": 25, "note": "老年/残障群体高频受影响"}, {"key": "urgency", "label": "紧迫度", "score": 18, "max": 25, "note": "公共服务均等化要求"}, {"key": "feasibility", "label": "可行性", "score": 17, "max": 25, "note": "人工通道与适老改造可并行"}, {"key": "severity", "label": "严重度", "score": 18, "max": 25, "note": "涉及特殊群体权益"}]},
            "evidence": [{"feedback_id": str(_uuid("feedback-F1004")), "excerpt": "访谈中多位老人反映：自助取号机字太小、不会操作...", "author": "周阿姨", "source": "interview", "created_at": "2026-09-30T16:45:00Z", "sentiment": "negative"}],
        },
        {
            "id": "t7", "title": "停车与指引不清晰", "short": "入口无指示，余位信息缺失", "feedback_count": 3, "customer_count": 3, "trend": "down", "strength": 40, "priority_score": 45,
            "score_card": {"total": 45, "max": 100, "level": "low", "dimensions": [{"key": "impact", "label": "影响面", "score": 12, "max": 25, "note": "主要影响首次到访"}, {"key": "urgency", "label": "紧迫度", "score": 10, "max": 25, "note": "趋势回落"}, {"key": "feasibility", "label": "可行性", "score": 12, "max": 25, "note": "指示牌与余位屏成本低"}, {"key": "severity", "label": "严重度", "score": 11, "max": 25, "note": "体验问题为主"}]},
            "evidence": [{"feedback_id": str(_uuid("feedback-F1002")), "excerpt": "从东门进来绕了两圈才找到停车场入口...", "author": "李强", "source": "portal", "created_at": "2026-09-30T11:05:00Z", "sentiment": "neutral"}],
        },
        {
            "id": "t8", "title": "移动端 APP 操作不便", "short": "入口深、步骤多，适老化与稳定性差", "feedback_count": 4, "customer_count": 4, "trend": "flat", "strength": 66, "priority_score": 60,
            "score_card": {"total": 60, "max": 100, "level": "medium", "dimensions": [{"key": "impact", "label": "影响面", "score": 16, "max": 25, "note": "线上渠道主力人群"}, {"key": "urgency", "label": "紧迫度", "score": 15, "max": 25, "note": "推送失效影响进度透明"}, {"key": "feasibility", "label": "可行性", "score": 15, "max": 25, "note": "交互重构周期较长"}, {"key": "severity", "label": "严重度", "score": 14, "max": 25, "note": "闪退/人脸难通过阻断办理"}]},
            "evidence": [{"feedback_id": str(_uuid("feedback-F1008")), "excerpt": "我的客户 APP 报错提示 token 过期，重装了三次还是闪退...", "author": "冯嘉", "source": "ticket", "created_at": "2026-10-01T17:48:00Z", "sentiment": "negative"}],
        },
    ]
    for t in topics:
        # 证据时间与对应反馈创建时间对齐（相对生成）
        for ev in t["evidence"]:
            ev["created_at"] = _fb_created_at(ev["feedback_id"]).isoformat().replace("+00:00", "Z")
        session.add(InsightTopic(
            id=t["id"],
            title=t["title"],
            short=t["short"],
            feedback_count=t["feedback_count"],
            customer_count=t["customer_count"],
            trend=t["trend"],
            strength=t["strength"],
            priority_score=t["priority_score"],
            score_card=t["score_card"],
            evidence=t["evidence"],
            last_seen_at=_fb_created_at(t["evidence"][0]["feedback_id"]),
            created_at=_ago(days=48),
            updated_at=_ago(hours=3),
        ))
    session.commit()
    print(f"[seed] inserted {len(topics)} insight_topics")


def _seed_gov(session: Session) -> None:
    if session.execute(select(GovHotTopic).limit(1)).scalar():
        print("[seed] gov_hot_topics already seeded, skip")
    else:
        topics = [
            GovHotTopic(id="GT-2601", title="老旧小区加装电梯审批周期偏长", summary="居民对既有住宅加装电梯的审批流程、出资分摊与管线迁移意见集中，多部门协同耗时超过法定时限。", coverage=23, growth=42.0, regions=["玄武区", "鼓楼区"], department="住建局", root_cause="流程壁垒：规划、住建、属地街道分头审批，管线迁移缺乏牵头部门", evidence="「加了半年还在公示，说是管线迁移要等市政排期，到底谁牵头？」", task_status="generated", task_id="GT-2601-治理", created_at=_at(1, 11, 5)),
            GovHotTopic(id="GT-2602", title="高校毕业生就业补贴申领门槛不清", summary="应届生对补贴对象、申领材料与到账周期疑问集中，线上线下答复口径存在不一致。", coverage=17, growth=28.0, regions=["栖霞区", "秦淮区"], department="人社局", root_cause="政策告知不足：细则更新后未同步各渠道，问答知识库滞后", evidence="「公告写的是毕业两年内，窗口又说按毕业证日期，到底按哪个？」", task_status="pending", created_at=_at(1, 9, 0)),
            GovHotTopic(id="GT-2603", title="幼儿园入园学位缺口引发排队焦虑", summary="家长集中反映公办园学位不足、报名渠道扎堆，多个业主群出现转发焦虑情绪。", coverage=15, growth=35.0, regions=["秦淮区", "建邺区"], department="教育局", root_cause="供需缺口：片区学位规划滞后于人口导入，信息公开节奏慢", evidence="「同一时间只能报一个园，系统又卡，错过就没有学位了？」", task_status="pending", created_at=_at(2, 9, 0)),
            GovHotTopic(id="GT-2604", title="政务大厅叫号等待时长上升", summary="窗口业务高峰时段排队超过 40 分钟，老年人不会线上预约导致到店返工。", coverage=11, growth=-8.0, regions=["鼓楼区"], department="政务办", root_cause="服务流程：高峰分流不足，线下引导与线上预约未打通", evidence="「取了号还要等一个小时，说好的一窗受理呢？」", task_status="pending", created_at=_at(2, 10, 0)),
        ]
        session.add_all(topics)
        session.commit()
        print(f"[seed] inserted {len(topics)} gov_hot_topics")

    if session.execute(select(GovAlertItem).limit(1)).scalar():
        print("[seed] gov_alert_items already seeded, skip")
    else:
        alerts = [
            GovAlertItem(id="BR-001", level="blue", title="停车收费调整咨询增多", summary="多小区业主群讨论新一轮道路停车收费调整，以咨询为主，暂未发现聚集风险。", trigger="敏感词「收费上涨」频次 +180%，情绪偏中性", regions=["建邺区"], evidence_count=6, dispatched=False, created_at=_at(2, 9, 0)),
            GovAlertItem(id="YE-002", level="yellow", title="幼儿园学位舆情升温", summary="家长群转发热议学位缺口，出现「错过报名就没有学位」等焦虑表述，需口径统一。", trigger="异常量级 + 情绪分析呈焦虑主导", regions=["秦淮区", "建邺区"], evidence_count=15, dispatched=False, created_at=_at(1, 9, 0)),
            GovAlertItem(id="OR-003", level="orange", title="电梯加装业主矛盾聚集", summary="同一小区低层业主联合反对加装方案，存在群体性事件苗头，建议属地提前介入。", trigger="集中爆发式诉求 + 对立情绪指数 0.72", regions=["玄武区"], evidence_count=9, dispatched=False, created_at=_at(1, 10, 0)),
            GovAlertItem(id="RD-004", level="red", title="南部片区供暖管网故障影响面扩大", summary="供暖管线爆裂影响 3 个小区供热，伴随医疗与退费诉求，需应急抢修联动。", trigger="公共安全关键词 + 紧急件自动标记", regions=["雨花台区"], evidence_count=12, dispatched=True, dispatched_to="住建局应急专班", created_at=_at(0, 9, 0)),
        ]
        session.add_all(alerts)
        session.commit()
        print(f"[seed] inserted {len(alerts)} gov_alert_items")

    if session.execute(select(GovPolicyNotice).limit(1)).scalar():
        print("[seed] gov_policy_notices already seeded, skip")
    else:
        notices = [
            GovPolicyNotice(id="N4001", title="大厅高峰预约分流公告", content="10 月 15 日起 9:00-11:00 实行预约分流，请优先线上取号。", status="published", scope="全渠道", channel="短信 + APP 推送", sent_count=1284, read_rate=0.76, updated_at=_at(2, 9, 0)),
            GovPolicyNotice(id="N4002", title="叫号系统故障应急说明", content="今日上午 9:20-10:05 叫号系统临时故障，已恢复正常。", status="draft", scope="大厅广播", channel="现场广播", sent_count=0, read_rate=0.0, updated_at=_at(0, 2, 30)),
            GovPolicyNotice(id="N4003", title="就业补贴申领细则更新提醒", content="高校毕业生就业补贴申领细则已更新，请按最新材料清单申报。", status="published", scope="栖霞区 + 秦淮区", channel="政务网 + 短信", sent_count=862, read_rate=0.91, updated_at=_at(1, 7, 20)),
        ]
        session.add_all(notices)
        session.commit()
        print(f"[seed] inserted {len(notices)} gov_policy_notices")


def _seed_interviews(session: Session) -> None:
    if session.execute(select(InterviewRecord).limit(1)).scalar():
        print("[seed] interview_records already seeded, skip")
        return
    # 访谈日期相对生成，落在最近三天
    rel_day = {"IV-001": 0, "IV-002": 1, "IV-003": 2, "IV-004": 1, "IV-005": 2, "IV-006": 2}
    rows = [
        {"id": "IV-001", "company_name": "云帆数字设计", "company_type": "私企", "industry": "企业服务", "contact_name": "林倩", "contact_role": "IT 负责人", "interview_date": "2026-10-14T09:00:00Z", "duration_min": 38, "source": "视频会议", "status": "linked", "summary": "设计团队 400+ 成员，期望按部门批量开通账号，同时希望管理员能看到成员活跃度以决定续费规模。", "key_points": ["每季度新增约 40 名外包设计师，逐个建号耗时约 3 人天", "需要角色分组权限模板，希望按项目隔离数据", "对续费定价敏感，正在对比竞品"], "extraction": {"pain_points": ["批量建号运维成本高", "希望角色级权限模板"], "needs": ["批量账号导入", "角色分组授权", "成员活跃度报表"], "cooperation_intent": "high", "matched_needs": ["批量账号与角色管理"], "lead_candidate": True, "lead_reason": "明确多次提及批量账号与角色分组能力，与企业版合作意向高", "extracted_at": "2026-10-14T10:00:00Z"}, "linked_feedback_ids": ["F1101"], "linked_lead_id": "BL-006", "recorder": "王雨桐"},
        {"id": "IV-002", "company_name": "中科软联", "company_type": "私企", "industry": "软件外包", "contact_name": "陈奕帆", "contact_role": "交付总监", "interview_date": "2026-10-13T09:00:00Z", "duration_min": 45, "source": "现场走访", "status": "extracted", "summary": "作为外包承接方，客户要求把反馈系统部署在自有机房，敏感数据不出域，同时希望提供私有化运维文档。", "key_points": ["甲方合同要求数据不出域，需本地化交付", "希望提供离线模型更新与运维手册", "正在评估 3 家供应商，预计 Q4 决策"], "extraction": {"pain_points": ["数据出域合规风险", "私有化运维人力不足"], "needs": ["本地化部署", "离线模型更新", "运维文档与培训"], "cooperation_intent": "high", "matched_needs": ["私有化与数据不出域部署"], "lead_candidate": True, "lead_reason": "合同明确私有化部署诉求且有采购周期，形成高意向线索", "extracted_at": "2026-10-13T10:00:00Z"}, "linked_feedback_ids": ["F1102"], "recorder": "王雨桐"},
        {"id": "IV-003", "company_name": "华东能源集团", "company_type": "国企", "industry": "能源化工", "contact_name": "赵铭", "contact_role": "信息化处长", "interview_date": "2026-10-11T09:00:00Z", "duration_min": 52, "source": "视频会议", "status": "linked", "summary": "集团要求与内部 OA、统一认证对接，账号体系对齐集团标准，同时反馈数据要纳入集团审计平台。", "key_points": ["统一认证对接是硬性准入条件", "需要审计日志同步到集团平台", "集团信息化建设有专项资金"], "extraction": {"pain_points": ["账号体系与集团标准不一致"], "needs": ["SSO 集成", "审计日志对接", "集团级报表"], "cooperation_intent": "high", "matched_needs": ["统一认证与集团账号对接", "审计日志与合规报告"], "lead_candidate": True, "lead_reason": "集团专项预算明确，SSO 与审计为刚性需求", "extracted_at": "2026-10-11T10:00:00Z"}, "linked_feedback_ids": ["F1103"], "linked_lead_id": "BL-007", "recorder": "张弛"},
        {"id": "IV-004", "company_name": "擎天数据科技", "company_type": "私企", "industry": "数据服务", "contact_name": "沈一鸣", "contact_role": "产品经理", "interview_date": "2026-10-12T09:00:00Z", "duration_min": 30, "source": "电话", "status": "recorded", "summary": "想基于反馈数据能力做二次开发，把分析结果嵌入自有 BI 看板，尚未确认具体合作模式。", "key_points": ["倾向 API 对接方式，需评估数据开放范围", "预算有限，希望先做 POC 验证"], "linked_feedback_ids": [], "recorder": "张弛"},
        {"id": "IV-005", "company_name": "联达精密制造", "company_type": "外企", "industry": "智能制造", "contact_name": "Marco 李", "contact_role": "信息安全经理", "interview_date": "2026-10-10T09:00:00Z", "duration_min": 41, "source": "视频会议", "status": "scheduled", "summary": "外资合规要求高，正在调研审计日志与合规报告能力，原定今天访谈已改期到下周二。", "key_points": ["关注 GDPR 数据合规", "需要操作留痕与导出报告"], "linked_feedback_ids": [], "recorder": "王雨桐"},
        {"id": "IV-006", "company_name": "岭南智慧政务研究院", "company_type": "事业单位", "industry": "政务服务", "contact_name": "何靖", "contact_role": "业务主任", "interview_date": "2026-10-09T09:00:00Z", "duration_min": 47, "source": "展会", "status": "recorded", "summary": "在数字政府展会上交流，关注舆情监测与群众诉求分级督办，希望结合现有平台做试点。", "key_points": ["关注诉求自动分级与督办闭环", "希望演示舆情预警与处置联动"], "linked_feedback_ids": [], "recorder": "赵铭"},
    ]
    for r in rows:
        session.add(InterviewRecord(
            id=r["id"],
            company_name=r["company_name"],
            company_type=r.get("company_type"),
            industry=r.get("industry"),
            contact_name=r.get("contact_name"),
            contact_role=r.get("contact_role"),
            interview_date=_at(rel_day[r["id"]], 9, 0),
            duration_min=r.get("duration_min", 0),
            source=r.get("source"),
            status=r["status"],
            summary=r.get("summary"),
            key_points=r.get("key_points"),
            extraction=r.get("extraction"),
            linked_feedback_ids=r.get("linked_feedback_ids"),
            linked_lead_id=r.get("linked_lead_id"),
            recorder=r.get("recorder"),
            created_at=_at(2, 8, 0),
            updated_at=_ago(hours=3),
        ))
    session.commit()
    print(f"[seed] inserted {len(rows)} interview_records")


def _seed_agents(session: Session) -> None:
    if session.execute(select(Agent).limit(1)).scalar():
        print("[seed] agents already seeded, skip")
    else:
        agents = [
            Agent(id="AG-001", name="政策公告 Agent", category="内容生成", scenario="根据政策变化自动草拟对外公告，联动发布公告工作流", enabled=True, tools=["查政策库", "生成公告稿", "发送通知"], bound_workflow_ids=["WF-PUBLISH-NOTICE"], run_count=126, reliability=96, last_run_at=_ago(hours=2), preset=True, created_at=_ago(days=45), updated_at=_ago(hours=3)),
            Agent(id="AG-002", name="商单回复 Agent", category="回复生成", scenario="对接企业商机与询价反馈，生成专业报价与跟进话术", enabled=True, tools=["查商务线索", "生成回复", "更新跟进状态"], bound_workflow_ids=["WF-LEAD-REPLY"], run_count=84, reliability=93, last_run_at=_ago(hours=5), preset=True, created_at=_ago(days=45), updated_at=_ago(hours=3)),
            Agent(id="AG-003", name="舆情聚类 Agent", category="分析研判", scenario="多条舆论指向同一论点时自动聚类，形成统一处置建议", enabled=True, tools=["文本聚类", "情感分析", "生成处置建议"], bound_workflow_ids=["WF-SENTIMENT-ALERT"], run_count=210, reliability=91, last_run_at=_ago(minutes=30), preset=True, created_at=_ago(days=45), updated_at=_ago(hours=3)),
            Agent(id="AG-004", name="邻里诉求 Agent", category="诉求处置", scenario="专门处理邻里纠纷类诉求，按属地映射到社区网格", enabled=False, tools=["诉求分级", "属地派单", "生成回复"], bound_workflow_ids=["WF-NEIGHBOR-REQ"], run_count=32, reliability=88, last_run_at=_ago(days=2), preset=True, created_at=_ago(days=45), updated_at=_ago(hours=3)),
            Agent(id="AG-005", name="反馈自动回复 Agent", category="回复生成", scenario="对高频咨询自动生成规范回复草稿，进入人工审批队列", enabled=True, tools=["知识库检索", "话术生成", "审批入队"], bound_workflow_ids=["WF-AUTO-REPLY"], run_count=402, reliability=97, last_run_at=_ago(minutes=0), preset=True, created_at=_ago(days=45), updated_at=_ago(hours=3)),
        ]
        session.add_all(agents)
        session.commit()
        print(f"[seed] inserted {len(agents)} agents")

    if session.execute(select(AgentTool).limit(1)).scalar():
        print("[seed] agent_tools already seeded, skip")
    else:
        tools = [
            AgentTool(id="T001", key="police-search", name="查政策库", category="检索", description="检索最新政策文件与解读，作为公告与回复的事实依据", created_at=_ago(days=45)),
            AgentTool(id="T002", key="db-query", name="查数据库", category="检索", description="按自然语言查询反馈库/工单库，聚合统计口径", created_at=_ago(days=45)),
            AgentTool(id="T003", key="kb-search", name="知识库检索", category="检索", description="检索产品知识库与历史回复，提升话术一致性", created_at=_ago(days=45)),
            AgentTool(id="T004", key="gov-compile", name="生成公告稿", category="生成", description="按政策主题与面向对象生成规范公告草稿", created_at=_ago(days=45)),
            AgentTool(id="T005", key="reply-gen", name="生成回复", category="生成", description="面向客户咨询/商单生成专业回复草稿", created_at=_ago(days=45)),
            AgentTool(id="T006", key="tone-gen", name="话术生成", category="生成", description="基于情感与对象调整沟通话术与语气", created_at=_ago(days=45)),
            AgentTool(id="T007", key="cluster", name="文本聚类", category="分析", description="对多条反馈/舆论做主题聚类，识别共性论点", created_at=_ago(days=45)),
            AgentTool(id="T008", key="sentiment", name="情感分析", category="分析", description="判断反馈与舆论的情感倾向与强度", created_at=_ago(days=45)),
            AgentTool(id="T009", key="advice-gen", name="生成处置建议", category="分析", description="综合聚类与情感结果生成统一处置建议", created_at=_ago(days=45)),
            AgentTool(id="T010", key="level-classify", name="诉求分级", category="处置", description="按紧急度/影响面/区域对诉求分级", created_at=_ago(days=45)),
            AgentTool(id="T011", key="dispatch", name="属地派单", category="处置", description="将诉求按属地/部门自动映射派单", created_at=_ago(days=45)),
            AgentTool(id="T012", key="approval-enqueue", name="审批入队", category="处置", description="将生成草稿推入人工审批队列并附加依据", created_at=_ago(days=45)),
            AgentTool(id="T013", key="lead-update", name="更新跟进状态", category="处置", description="更新商务线索跟进阶段与备注", created_at=_ago(days=45)),
            AgentTool(id="T014", key="notify", name="发送通知", category="通知", description="通过站内信/短信/公众号推送结果", created_at=_ago(days=45)),
            AgentTool(id="T015", key="publish", name="发布公告", category="通知", description="将审批通过的公告发布到对内/对外渠道", created_at=_ago(days=45)),
        ]
        session.add_all(tools)
        session.commit()
        print(f"[seed] inserted {len(tools)} agent_tools")

    if session.execute(select(Skill).limit(1)).scalar():
        print("[seed] skills already seeded, skip")
    else:
        skills = [
            Skill(id="SK-POLICY-COMPOSE", name="政务公告撰写", category="政务", description="基于政策库与公告模板撰写规范对外公告", enabled=True, owner_agent_ids=["AG-001"], created_at=_ago(days=45)),
            Skill(id="SK-LEAD-REPLY", name="商单报价回复", category="商务", description="结合产品目录生成报价与跟进话术", enabled=True, owner_agent_ids=["AG-002"], created_at=_ago(days=45)),
            Skill(id="SK-OPINION-CLUSTER", name="舆情聚类研判", category="分析", description="多条舆论论点聚类与情感研判，输出统一处置建议", enabled=True, owner_agent_ids=["AG-003"], created_at=_ago(days=45)),
            Skill(id="SK-NEIGHBOR-DISPATCH", name="邻里诉求派单", category="诉求处置", description="邻里纠纷分级与属地网格派单", enabled=True, owner_agent_ids=["AG-004"], created_at=_ago(days=45)),
            Skill(id="SK-FAQ-AUTOREPLY", name="高频咨询自动回复", category="回复生成", description="高频咨询知识库检索与话术生成", enabled=True, owner_agent_ids=["AG-005"], created_at=_ago(days=45)),
            Skill(id="SK-INTERVIEW-EXTRACT", name="访谈纪要提炼", category="分析", description="访谈纪要痛点/需求提炼，联动商务线索", enabled=True, owner_agent_ids=[], created_at=_ago(days=45)),
            Skill(id="SK-SUPERVISION-REMIND", name="督办事项提醒", category="政务", description="超期与临期督办事项自动提醒与升级", enabled=False, owner_agent_ids=[], created_at=_ago(days=45)),
        ]
        session.add_all(skills)
        session.commit()
        print(f"[seed] inserted {len(skills)} skills")


def _seed_workflows(session: Session) -> None:
    if session.execute(select(Workflow).limit(1)).scalar():
        print("[seed] workflows already seeded, skip")
    else:
        wf_publish = Workflow(
            id="WF-PUBLISH-NOTICE", name="发布公告", description="监测政策变化 → 草拟公告 → 人工确认 → 多渠道发布。",
            enabled=True, trigger="定时每日09:00；事件：政策变更触发",
            nodes=[
                {"id": "n-start", "name": "开始", "type": "start", "status": "success"},
                {"id": "n-scan", "name": "扫描政策库", "type": "tool", "tool_keys": ["policy_search"], "status": "success", "description": "检索今日新增/变更政策"},
                {"id": "n-dec", "name": "是否有变更", "type": "decision", "status": "success", "description": "分支：有变更 → 草拟；无变更 → 结束"},
                {"id": "n-draft", "name": "草拟公告", "type": "agent", "agent_id": "AG-001", "status": "success", "description": "政策公告 Agent 生成草稿"},
                {"id": "n-review", "name": "人工审核", "type": "agent", "agent_id": "AG-001", "status": "success", "description": "运营人员确认或修改"},
                {"id": "n-send", "name": "发布通知", "type": "tool", "tool_keys": ["send_email", "send_sms"], "status": "success", "description": "邮件 + 站内信推送"},
                {"id": "n-end", "name": "结束", "type": "end", "status": "success"},
            ],
            edges=[
                {"from": "n-start", "to": "n-scan"}, {"from": "n-scan", "to": "n-dec"}, {"from": "n-dec", "to": "n-draft", "condition": "有变更"}, {"from": "n-dec", "to": "n-end", "condition": "无变更"},
                {"from": "n-draft", "to": "n-review"}, {"from": "n-review", "to": "n-send"}, {"from": "n-send", "to": "n-end"},
            ],
            agent_bindings={"n-draft": "AG-001", "n-review": "AG-001"},
            tool_chain={"n-scan": ["policy_search"], "n-send": ["send_email", "send_sms"]},
            updated_at=_ago(minutes=1),
        )
        wf_lead = Workflow(
            id="WF-LEAD-REPLY", name="商单自动回复", description="识别商务线索 → 匹配 Agent → 生成回复草稿 → 人工确认发送。",
            enabled=True, trigger="事件：新线索进待跟进；手动：生成回复",
            nodes=[
                {"id": "n-start", "name": "开始", "type": "start", "status": "success"},
                {"id": "n-match", "name": "匹配线索", "type": "tool", "tool_keys": ["lead_search"], "status": "success", "description": "读取线索详情与历史记录"},
                {"id": "n-reply", "name": "生成回复草稿", "type": "agent", "agent_id": "AG-002", "status": "success", "description": "商单回复 Agent 草拟跟进话术"},
                {"id": "n-confirm", "name": "人工确认", "type": "agent", "agent_id": "AG-002", "status": "success", "description": "商务人员确认或调整"},
                {"id": "n-send", "name": "发送邮件", "type": "tool", "tool_keys": ["send_email"], "status": "success", "description": "发送给客户"},
                {"id": "n-end", "name": "结束", "type": "end", "status": "success"},
            ],
            edges=[
                {"from": "n-start", "to": "n-match"}, {"from": "n-match", "to": "n-reply"}, {"from": "n-reply", "to": "n-confirm"},
                {"from": "n-confirm", "to": "n-send"}, {"from": "n-send", "to": "n-end"},
            ],
            agent_bindings={"n-reply": "AG-002", "n-confirm": "AG-002"},
            tool_chain={"n-match": ["lead_search"], "n-send": ["send_email"]},
            updated_at=_ago(minutes=1),
        )
        wf_auto = Workflow(
            id="WF-AUTO-REPLY", name="自动分类与去重", description="监听新增反馈 → AI 分类 → 去重组群 → 按优先级派单 → 生成待办。",
            enabled=True, trigger="事件：新反馈提交时实时触发",
            nodes=[
                {"id": "n-start", "name": "开始", "type": "start", "status": "success"},
                {"id": "n-ingest", "name": "接收反馈", "type": "tool", "tool_keys": ["feedback_search"], "status": "success", "description": "读取新增反馈内容"},
                {"id": "n-classify", "name": "AI 分类", "type": "agent", "agent_id": "AG-005", "status": "success", "description": "自动分类 Agent 打标签"},
                {"id": "n-dedup", "name": "去重组群", "type": "agent", "agent_id": "AG-005", "status": "success", "description": "相似反馈归并，避免重复处理"},
                {"id": "n-priority", "name": "优先级评估", "type": "decision", "status": "success", "description": "紧急/高/中/低"},
                {"id": "n-todo", "name": "生成待办", "type": "tool", "tool_keys": ["create_todo"], "status": "success", "description": "创建工单并指派"},
                {"id": "n-end", "name": "结束", "type": "end", "status": "success"},
            ],
            edges=[
                {"from": "n-start", "to": "n-ingest"}, {"from": "n-ingest", "to": "n-classify"}, {"from": "n-classify", "to": "n-dedup"},
                {"from": "n-dedup", "to": "n-priority"}, {"from": "n-priority", "to": "n-todo", "condition": "紧急/高"}, {"from": "n-priority", "to": "n-end", "condition": "中/低"},
                {"from": "n-todo", "to": "n-end"},
            ],
            agent_bindings={"n-classify": "AG-005", "n-dedup": "AG-005"},
            tool_chain={"n-ingest": ["feedback_search"], "n-todo": ["create_todo"]},
            updated_at=_ago(minutes=1),
        )
        wf_sentiment = Workflow(
            id="WF-SENTIMENT-ALERT", name="舆情监测与应急", description="舆情定时扫描 → 情感异常检测 → 阈值触发 → 生成预警 → 通知负责人。",
            enabled=True, trigger="定时30分钟扫描；事件：情感值骤降触发",
            nodes=[
                {"id": "n-start", "name": "开始", "type": "start", "status": "success"},
                {"id": "n-crawl", "name": "舆情扫描", "type": "tool", "tool_keys": ["news_search"], "status": "success", "description": "爬取社交媒体与新闻"},
                {"id": "n-sentiment", "name": "情感分析", "type": "agent", "agent_id": "AG-003", "status": "success", "description": "舆情聚类 Agent 分析情感走势"},
                {"id": "n-threshold", "name": "阈值判断", "type": "decision", "status": "success", "description": "情感值降幅 > 20%"},
                {"id": "n-alert", "name": "生成预警", "type": "agent", "agent_id": "AG-003", "status": "success", "description": "草拟预警报告"},
                {"id": "n-notify", "name": "通知推送", "type": "tool", "tool_keys": ["send_email", "send_sms"], "status": "success", "description": "推送给舆情值班组"},
                {"id": "n-end", "name": "结束", "type": "end", "status": "success"},
            ],
            edges=[
                {"from": "n-start", "to": "n-crawl"}, {"from": "n-crawl", "to": "n-sentiment"}, {"from": "n-sentiment", "to": "n-threshold"},
                {"from": "n-threshold", "to": "n-alert", "condition": "触发阈值"}, {"from": "n-threshold", "to": "n-end", "condition": "正常"},
                {"from": "n-alert", "to": "n-notify"}, {"from": "n-notify", "to": "n-end"},
            ],
            agent_bindings={"n-sentiment": "AG-003", "n-alert": "AG-003"},
            tool_chain={"n-crawl": ["news_search"], "n-notify": ["send_email", "send_sms"]},
            updated_at=_ago(minutes=1),
        )
        wf_neighbor = Workflow(
            id="WF-NEIGHBOR-REQ", name="多源诉求聚合解决", description="汇聚热线/微信/网格化上报 → 去重聚类 → 智能分拨 → 跟踪闭环。",
            enabled=False, trigger="事件：任意渠道新诉求实时触发",
            nodes=[
                {"id": "n-start", "name": "开始", "type": "start", "status": "idle"},
                {"id": "n-collect", "name": "多源汇聚", "type": "tool", "tool_keys": ["feedback_search"], "status": "idle", "description": "聚合热线、微信、网格化数据"},
                {"id": "n-dedup", "name": "去重聚类", "type": "agent", "agent_id": "AG-004", "status": "idle", "description": "诉求处置 Agent 识别重复诉求"},
                {"id": "n-assign", "name": "智能分拨", "type": "decision", "status": "idle", "description": "按属地/类型分派"},
                {"id": "n-track", "name": "跟踪闭环", "type": "agent", "agent_id": "AG-004", "status": "idle", "description": "跟踪处理进度直至办结"},
                {"id": "n-archive", "name": "归档", "type": "tool", "tool_keys": ["create_todo"], "status": "idle", "description": "标记已办结"},
                {"id": "n-end", "name": "结束", "type": "end", "status": "idle"},
            ],
            edges=[
                {"from": "n-start", "to": "n-collect"}, {"from": "n-collect", "to": "n-dedup"}, {"from": "n-dedup", "to": "n-assign"},
                {"from": "n-assign", "to": "n-track", "condition": "已分拨"}, {"from": "n-assign", "to": "n-archive", "condition": "重复/无效"},
                {"from": "n-track", "to": "n-archive"}, {"from": "n-archive", "to": "n-end"},
            ],
            agent_bindings={"n-dedup": "AG-004", "n-track": "AG-004"},
            tool_chain={"n-collect": ["feedback_search"], "n-archive": ["create_todo"]},
            updated_at=_ago(minutes=1),
        )
        session.add_all([wf_publish, wf_lead, wf_auto, wf_sentiment, wf_neighbor])
        session.commit()
        print("[seed] inserted 5 workflows")

    if session.execute(select(WorkflowRun).limit(1)).scalar():
        print("[seed] workflow_runs already seeded, skip")
    else:
        runs = [
WorkflowRun(id="R-241015-01", workflow_id="WF-PUBLISH-NOTICE", started_at=_ago(minutes=120), ended_at=_ago(minutes=118), status="success", output_summary="检测到 2 条政策变更，已发布对应公告"),
            WorkflowRun(id="R-241015-02", workflow_id="WF-PUBLISH-NOTICE", started_at=_ago(minutes=60), ended_at=_ago(minutes=58), status="success", output_summary="无新增政策变更"),
            WorkflowRun(id="R-241014-03", workflow_id="WF-LEAD-REPLY", started_at=_ago(minutes=180), ended_at=_ago(minutes=178), status="success", output_summary="为「智慧城市项目」生成跟进邮件，客户已回复"),
            WorkflowRun(id="R-241015-04", workflow_id="WF-LEAD-REPLY", started_at=_ago(minutes=30), status="running", output_summary="正在为「数字政务平台」生成方案草稿"),
            WorkflowRun(id="R-241015-05", workflow_id="WF-AUTO-REPLY", started_at=_ago(minutes=240), ended_at=_ago(minutes=238), status="success", output_summary="处理 17 条新增反馈，归并为 9 个待办"),
            WorkflowRun(id="R-241015-06", workflow_id="WF-AUTO-REPLY", started_at=_ago(minutes=90), ended_at=_ago(minutes=88), status="success", output_summary="处理 3 条紧急反馈，已创建工单"),
            WorkflowRun(id="R-241015-07", workflow_id="WF-SENTIMENT-ALERT", started_at=_ago(minutes=300), ended_at=_ago(minutes=298), status="success", output_summary="情感值正常，无异常舆情"),
            WorkflowRun(id="R-241015-08", workflow_id="WF-SENTIMENT-ALERT", started_at=_ago(minutes=45), ended_at=_ago(minutes=43), status="failed", output_summary="情感分析节点超时", error_message="模型推理节点 model-infer-01 负载过高，推理超时"),
        ]
        session.add_all(runs)
        session.commit()
        print(f"[seed] inserted {len(runs)} workflow_runs")


def _seed_roadmap(session: Session) -> None:
    if session.execute(select(RoadmapItem).limit(1)).scalar():
        print("[seed] roadmap_items already seeded, skip")
    else:
        items = [
            RoadmapItem(id="R2001", title="材料复用与一网通办改造", topic_id="t1", status="in_progress", version="v1.2", owner="数据治理组", due_date=_now() + timedelta(days=28), progress=45, task_count=4, created_at=_ago(days=28), updated_at=_ago(hours=3)),
            RoadmapItem(id="R2002", title="大厅动态开窗与排队提示", topic_id="t2", status="planning", version="v1.3", owner="运营管理组", due_date=_now() + timedelta(days=44), progress=0, task_count=2, created_at=_ago(days=17), updated_at=_ago(hours=3)),
            RoadmapItem(id="R2003", title="预约系统容灾与消息补发", topic_id="t3", status="scheduled", version="v1.1", owner="平台研发组", due_date=_now() + timedelta(days=7), progress=20, task_count=3, created_at=_ago(days=13), updated_at=_ago(hours=3)),
            RoadmapItem(id="R2004", title="政策知识库问答上线", topic_id="t4", status="released", version="v1.0", owner="政务内容组", due_date=_ago(days=18), progress=100, task_count=3, created_at=_ago(days=64), updated_at=_ago(hours=3)),
        ]
        session.add_all(items)
        session.commit()
        print(f"[seed] inserted {len(items)} roadmap_items")

    if session.execute(select(TaskItem).limit(1)).scalar():
        print("[seed] task_items already seeded, skip")
    else:
        tasks = [
            TaskItem(id="TK1001", roadmap_id="R2001", title="材料目录对齐（13 个高频事项）", status="done", owner="数据治理组", priority=1, created_at=_ago(days=26)),
            TaskItem(id="TK1002", roadmap_id="R2001", title="电子材料库接口联调", status="doing", owner="平台研发组", priority=1, created_at=_ago(days=20)),
            TaskItem(id="TK1003", roadmap_id="R2001", title="窗口免提交规则试点", status="doing", owner="运营管理组", priority=2, created_at=_ago(days=12)),
            TaskItem(id="TK1004", roadmap_id="R2001", title="线上清单与线下口径统一", status="todo", owner="政务内容组", priority=2, created_at=_ago(days=8)),
            TaskItem(id="TK1005", roadmap_id="R2002", title="高峰时段取号数据分析", status="todo", owner="运营管理组", priority=1, created_at=_ago(days=10)),
            TaskItem(id="TK1006", roadmap_id="R2002", title="动态开窗规则评审", status="todo", owner="运营管理组", priority=3, created_at=_ago(days=7)),
            TaskItem(id="TK1007", roadmap_id="R2003", title="预约数据每日快照备份", status="doing", owner="平台研发组", priority=1, created_at=_ago(days=9)),
            TaskItem(id="TK1008", roadmap_id="R2003", title="短信提醒补偿任务", status="todo", owner="平台研发组", priority=2, created_at=_ago(days=6)),
            TaskItem(id="TK1009", roadmap_id="R2003", title="改签幂等与重试修复", status="todo", owner="平台研发组", priority=1, created_at=_ago(days=5)),
            TaskItem(id="TK1010", roadmap_id="R2004", title="政策问答语料整理", status="done", owner="政务内容组", priority=1, created_at=_ago(days=59)),
            TaskItem(id="TK1011", roadmap_id="R2004", title="问答系统评测通过", status="done", owner="平台研发组", priority=2, created_at=_ago(days=38)),
            TaskItem(id="TK1012", roadmap_id="R2004", title="对外发布与值班培训", status="done", owner="运营管理组", priority=3, created_at=_ago(days=23)),
        ]
        session.add_all(tasks)
        session.commit()
        print(f"[seed] inserted {len(tasks)} task_items")

    if session.execute(select(ReplyDraft).limit(1)).scalar():
        print("[seed] reply_drafts already seeded, skip")
    else:
        drafts = [
            ReplyDraft(id="D3001", feedback_id=str(_uuid("feedback-F1055")), excerpt="今天大厅叫号系统故障，工作人员手工登记排队，秩序混乱，等了近一小时。", draft="您好，抱歉给您带来不便。今日上午叫号系统临时故障已修复，我们对排队秩序问题已启动复盘，后续将增加故障应急广播与手工叫号预案，感谢您的反馈。", tone="致歉+整改承诺", status="draft", updated_at=_ago(hours=4)),
            ReplyDraft(id="D3002", feedback_id=str(_uuid("feedback-F1049")), excerpt="线上预约系统凌晨维护后数据回滚，白天的预约记录全部丢失，窗口不认补打的凭证。", draft="您好，关于预约记录回滚问题我们正在核查数据链路，已为您恢复预约记录并短信通知，窗口将按恢复后的记录办理，给您造成不便非常抱歉。", tone="致歉+处理进展", status="draft", updated_at=_ago(days=1, hours=3)),
            ReplyDraft(id="D3003", feedback_id=str(_uuid("feedback-F1053")), excerpt="昨日门户政策问答回复已读未回，今天热线又问了一遍，答复内容还不一致。", draft="您好，您反映的政策问答未回复与口径不一致问题已转政务内容组，将在 1 个工作日内统一口径并书面回复，感谢监督。", tone="说明+时限承诺", status="approved", updated_at=_ago(hours=5)),
        ]
        session.add_all(drafts)
        session.commit()
        print(f"[seed] inserted {len(drafts)} reply_drafts")


def _seed_resources(session: Session) -> None:
    if session.execute(select(ServerState).limit(1)).scalar():
        print("[seed] server_states already seeded, skip")
    else:
        servers = [
            ServerState(id="SRV-01", name="api-gateway-01", role="API 网关", cpu=42.0, mem=55.0, disk=46.0, load="0.8, 0.6, 0.5", uptime="32 天", status="healthy", updated_at=_ago(minutes=2)),
            ServerState(id="SRV-02", name="app-worker-01", role="应用服务", cpu=68.0, mem=61.0, disk=52.0, load="1.6, 1.3, 1.1", uptime="18 天", status="healthy", updated_at=_ago(minutes=2)),
            ServerState(id="SRV-03", name="scheduler-01", role="任务调度", cpu=35.0, mem=44.0, disk=58.0, load="0.4, 0.5, 0.4", uptime="45 天", status="healthy", updated_at=_ago(minutes=2)),
            ServerState(id="SRV-04", name="model-infer-01", role="模型推理", cpu=82.0, mem=74.0, disk=63.0, load="3.4, 2.9, 2.6", uptime="12 天", status="warning", updated_at=_ago(minutes=2)),
        ]
        session.add_all(servers)
        session.commit()
        print(f"[seed] inserted {len(servers)} server_states")

    if session.execute(select(DatabaseState).limit(1)).scalar():
        print("[seed] database_states already seeded, skip")
    else:
        dbs = [
            DatabaseState(id="DB-01", name="postgres-main", engine="PostgreSQL 16 (pgvector)", status="healthy", connections=23, max_connections=100, slow_queries=2, tablespace_pct=38.0, last_check=_ago(minutes=2)),
            DatabaseState(id="DB-02", name="redis-cache", engine="Redis 7", status="healthy", connections=8, max_connections=64, slow_queries=0, tablespace_pct=12.0, last_check=_ago(minutes=1)),
            DatabaseState(id="DB-03", name="milvus-vector", engine="Milvus 2.4", status="degraded", connections=5, max_connections=32, slow_queries=7, tablespace_pct=71.0, last_check=_ago(minutes=4)),
        ]
        session.add_all(dbs)
        session.commit()
        print(f"[seed] inserted {len(dbs)} database_states")

    if session.execute(select(ApiEndpointState).limit(1)).scalar():
        print("[seed] api_endpoint_states already seeded, skip")
    else:
        apis = [
            ApiEndpointState(id="API-01", method="GET", path="/api/v1/healthz", status="healthy", response_ms=23, error_rate=0.0, rps=12.4, updated_at=_ago(minutes=2)),
            ApiEndpointState(id="API-02", method="GET", path="/api/v1/feedbacks", status="healthy", response_ms=41, error_rate=0.2, rps=8.1, updated_at=_ago(minutes=2)),
            ApiEndpointState(id="API-03", method="GET", path="/api/v1/insights/topics", status="healthy", response_ms=56, error_rate=0.4, rps=3.2, updated_at=_ago(minutes=2)),
            ApiEndpointState(id="API-04", method="POST", path="/api/v1/ai/classify", status="healthy", response_ms=320, error_rate=1.1, rps=2.7, updated_at=_ago(minutes=2)),
            ApiEndpointState(id="API-05", method="POST", path="/api/v1/ai/reply/generate", status="healthy", response_ms=480, error_rate=1.8, rps=1.9, updated_at=_ago(minutes=2)),
            ApiEndpointState(id="API-06", method="GET", path="/api/v1/gov/summary", status="degraded", response_ms=612, error_rate=3.4, rps=1.2, updated_at=_ago(minutes=2)),
            ApiEndpointState(id="API-07", method="GET", path="/api/v1/business/leads", status="healthy", response_ms=63, error_rate=0.3, rps=1.5, updated_at=_ago(minutes=2)),
            ApiEndpointState(id="API-08", method="POST", path="/api/v1/workflows/run", status="healthy", response_ms=240, error_rate=0.9, rps=0.8, updated_at=_ago(minutes=2)),
            ApiEndpointState(id="API-09", method="GET", path="/api/v1/resources/health", status="healthy", response_ms=35, error_rate=0.0, rps=2.3, updated_at=_ago(minutes=2)),
            ApiEndpointState(id="API-10", method="GET", path="/api/v1/resources/logs", status="healthy", response_ms=52, error_rate=0.1, rps=1.7, updated_at=_ago(minutes=2)),
            ApiEndpointState(id="API-11", method="GET", path="/api/v1/interviews", status="healthy", response_ms=47, error_rate=0.2, rps=1.1, updated_at=_ago(minutes=2)),
            ApiEndpointState(id="API-12", method="GET", path="/api/v1/agents", status="healthy", response_ms=39, error_rate=0.0, rps=1.4, updated_at=_ago(minutes=2)),
            ApiEndpointState(id="API-13", method="POST", path="/api/v1/notices/publish", status="degraded", response_ms=880, error_rate=4.6, rps=0.2, updated_at=_ago(minutes=2)),
            ApiEndpointState(id="API-14", method="GET", path="/api/v1/report/export", status="down", response_ms=0, error_rate=100.0, rps=0.0, updated_at=_ago(minutes=2)),
        ]
        session.add_all(apis)
        session.commit()
        print(f"[seed] inserted {len(apis)} api_endpoint_states")

    if session.execute(select(SystemLogEntry).limit(1)).scalar():
        print("[seed] system_log_entries already seeded, skip")
    else:
        logs = [
            SystemLogEntry(id="LG-001", time=_ago(minutes=1), level="warn", module="milvus-vector", message="向量检索延迟上升：P95 从 120ms 升至 320ms，建议检查索引重建任务"),
            SystemLogEntry(id="LG-002", time=_ago(minutes=3), level="error", module="report-service", message="导出任务 EXP-2045 失败：PDF 渲染进程内存溢出，已自动重试 2 次"),
            SystemLogEntry(id="LG-003", time=_ago(minutes=6), level="info", module="scheduler-01", message="工作流 WF-SENTIMENT-ALERT 定时触发完成，共处理 12 条新增舆情"),
            SystemLogEntry(id="LG-004", time=_ago(minutes=9), level="info", module="app-worker-01", message="Agent AG-002 完成商单回复草稿 3 份，进入人工审批队列"),
            SystemLogEntry(id="LG-005", time=_ago(minutes=14), level="info", module="api-gateway-01", message="接口 /api/v1/gov/summary 响应时间超过 600ms，已记录慢请求采样"),
            SystemLogEntry(id="LG-006", time=_ago(minutes=20), level="info", module="scheduler-01", message="数据同步任务 SYNC-042 完成：反馈库新增 10 条，去重合并 3 组"),
            SystemLogEntry(id="LG-007", time=_ago(minutes=26), level="warn", module="model-infer-01", message="推理节点 GPU 显存使用率 88%，未来 1 小时有批量聚类任务，存在排队风险"),
            SystemLogEntry(id="LG-008", time=_ago(minutes=36), level="info", module="postgres-main", message="慢查询收敛：近 1 小时慢 SQL 2 条，均为含向量检索的大范围筛选"),
            SystemLogEntry(id="LG-009", time=_ago(minutes=48), level="error", module="report-service", message="导出任务 EXP-2039 重试超过上限，已转人工处理，工单编号 TK-1180"),
            SystemLogEntry(id="LG-010", time=_ago(minutes=60), level="info", module="app-worker-01", message="Agent AG-001 完成政策公告草稿《智能客服平台升级通知》，等待发布审批"),
        ]
        session.add_all(logs)
        session.commit()
        print(f"[seed] inserted {len(logs)} system_log_entries")

    if session.execute(select(ResourceAlert).limit(1)).scalar():
        print("[seed] resource_alerts already seeded, skip")
    else:
        alerts = [
            ResourceAlert(id="AL-001", level="error", title="导出服务连续失败", time=_ago(minutes=3), target="report-service / EXP-2045"),
            ResourceAlert(id="AL-002", level="warn", title="模型推理节点负载过高", time=_ago(minutes=26), target="model-infer-01"),
            ResourceAlert(id="AL-003", level="warn", title="向量库检索延迟上升", time=_ago(minutes=1), target="milvus-vector"),
            ResourceAlert(id="AL-004", level="info", title="政策公告草稿待审批", time=_ago(minutes=60), target="Agent AG-001"),
        ]
        session.add_all(alerts)
        session.commit()
        print(f"[seed] inserted {len(alerts)} resource_alerts")


def _seed_settings(session: Session) -> None:
    if session.execute(select(ChannelConfig).limit(1)).scalar():
        print("[seed] channel_configs already seeded, skip")
    else:
        channels = [
            ChannelConfig(id="CC-001", key="ticket", label="工单系统", enabled=True, connected=True, last_sync=_ago(minutes=0), incoming=12, note="工单系统已对接", updated_at=_ago(minutes=0)),
            ChannelConfig(id="CC-002", key="portal", label="门户留言", enabled=True, connected=True, last_sync=_ago(minutes=0), incoming=9, note="门户留言已对接", updated_at=_ago(minutes=0)),
            ChannelConfig(id="CC-003", key="review", label="评价中心", enabled=True, connected=True, last_sync=_ago(minutes=10), incoming=7, note="评价中心已对接", updated_at=_ago(minutes=0)),
            ChannelConfig(id="CC-004", key="hotline", label="热线录音", enabled=True, connected=True, last_sync=_ago(minutes=15), incoming=11, note="热线录音转写待接 LLM", updated_at=_ago(minutes=0)),
            ChannelConfig(id="CC-005", key="interview", label="客户访谈", enabled=True, connected=False, last_sync=None, incoming=0, note="访谈为线下导入，未接自动同步", updated_at=_ago(minutes=0)),
            ChannelConfig(id="CC-006", key="sales", label="商务反馈", enabled=True, connected=True, last_sync=_ago(minutes=0), incoming=5, note="商务侧反馈已接入，线索同步正常", updated_at=_ago(minutes=0)),
        ]
        session.add_all(channels)
        session.commit()
        print(f"[seed] inserted {len(channels)} channel_configs")


def _seed_automation(session: Session) -> None:
    if session.execute(select(AutomationRule).limit(1)).scalar():
        print("[seed] automation_rules already seeded, skip")
        return
    rules = [
        AutomationRule(id="rule-001", name="自动分类新工单", description="根据内容关键词与历史聚类模型，自动为新提交工单分配主题标签与优先级", enabled=True, scenario="工单接入", icon="tags", tone="primary", stats="今日已自动分类 12 条", updated_at=_ago(minutes=0)),
        AutomationRule(id="rule-002", name="重复问题自动回复", description="对匹配到知识库高频问答模板的工单，自动生成统一规范回复并进入待审批队列", enabled=True, scenario="回复生成", icon="message", tone="success", stats="今日已命中 5 条", updated_at=_ago(minutes=0)),
        AutomationRule(id="rule-003", name="高优先级自动升级", description="P4+ 工单或情感极负面反馈，自动推送至值班负责人并生成督办任务", enabled=True, scenario="风险预警", icon="alert", tone="warning", stats="今日已升级 2 条", updated_at=_ago(minutes=0)),
        AutomationRule(id="rule-004", name="情感负面实时预警", description="监测热线/门户/评价渠道，连续出现负面情感反馈时触发预警通知", enabled=True, scenario="舆情监测", icon="bell", tone="danger", stats="今日已触发 1 次", updated_at=_ago(minutes=0)),
    ]
    session.add_all(rules)
    session.commit()
    print(f"[seed] inserted {len(rules)} automation_rules")


def _seed_business(session: Session) -> None:
    # BusinessLead
    if not session.execute(select(BusinessLead).limit(1)).scalar():
        leads = [
            BusinessLead(id="BL-001", feedback_id="F1101", content="我们公司有 400 多名设计师，现在每人单独建账号太麻烦，希望支持批量导入和角色分组。", company_name="云帆数字设计", industry="企业服务", company_type="私企", size_band="500-2000 人", matched_product="企业版·批量账号管理", match_reason="反馈提及「批量导入 + 角色分组」，与企业版多人协作能力语义匹配", value_score=82, confidence=91, stage="pushed", created_at=_ago(days=0, hours=8)),
            BusinessLead(id="BL-002", feedback_id="F1102", content="作为外包承接方，客户要求我们提供本地化部署版本，敏感数据不能出我们的机房。", company_name="中科软联", industry="软件外包", company_type="私企", size_band="200-500 人", matched_product="私有化部署包", match_reason="反馈提出「本地化部署 + 数据不出域」，匹配私有化版本需求", value_score=78, confidence=88, stage="qualified", created_at=_ago(days=1, hours=2)),
            BusinessLead(id="BL-003", feedback_id="F1103", content="我们是省属国企，需要和内部 OA、统一认证对接，账号体系要对齐集团标准。", company_name="华东能源集团", industry="能源化工", company_type="国企", size_band="2000 人以上", matched_product="企业版·SSO/统一认证", match_reason="反馈提及「统一认证 + 集团账号标准」，匹配 SSO 集成能力", value_score=90, confidence=95, stage="pushed", created_at=_ago(days=1, hours=20)),
            BusinessLead(id="BL-004", feedback_id="F1104", content="当前产品缺少审计日志导出，合规团队要求完整操作留痕，否则无法过等保三级。", company_name="数智科技", industry="数据服务", company_type="私企", size_band="500-2000 人", matched_product="企业版·审计日志与合规报表", match_reason="反馈提出「审计日志 + 等保合规」刚需，匹配企业版审计能力", value_score=85, confidence=92, stage="identified", created_at=_ago(days=2, hours=10)),
        ]
        session.add_all(leads)
        session.commit()
        print(f"[seed] inserted {len(leads)} business_leads")
    else:
        print("[seed] business_leads already seeded, skip")

    # MarketSignal
    if not session.execute(select(MarketSignal).limit(1)).scalar():
        signals = [
            MarketSignal(id="MS-001", title="大型客户批量账号管理需求集中爆发", type="opportunity", summary="近期连续收到 4 条中大型企业反馈，均提到「批量导入成员 + 角色分组授权」诉求，说明该需求正从头部客户向腰部蔓延。", evidence_count=4, severity=3, related_industries=["企业服务", "教育", "智能制造"], created_at=_ago(days=0, hours=9)),
            MarketSignal(id="MS-002", title="数据不出域成为政企客户准入硬门槛", type="risk", summary="连续 3 家客户明确要求私有化部署，若不能提供本地化方案，可能直接失去政企赛道。", evidence_count=3, severity=4, related_industries=["能源化工", "智能制造", "政务"], created_at=_ago(days=1, hours=5)),
            MarketSignal(id="MS-003", title="国企客户统一认证对接需求增加", type="opportunity", summary="Q3 以来已有 2 家国企提出 SSO/OAuth2 对接诉求，预计 Q4 会进一步增多，建议优先排期。", evidence_count=2, severity=2, related_industries=["能源化工", "金融"], created_at=_ago(days=1, hours=22)),
        ]
        session.add_all(signals)
        session.commit()
        print(f"[seed] inserted {len(signals)} market_signals")
    else:
        print("[seed] market_signals already seeded, skip")

    # CommonNeed
    if not session.execute(select(CommonNeed).limit(1)).scalar():
        needs = [
            CommonNeed(id="CN-001", title="批量账号与角色管理", description="大型组织需要批量导入成员、按部门/角色分组授权，减少单账号逐个配置的运维成本。", feedback_count=34, customer_count=12, industries=["企业服务", "能源化工", "教育"], product_potential="企业版·批量账号与 RBAC 角色分组", priority=5, status="planned", created_at=_ago(days=0, hours=10)),
            CommonNeed(id="CN-002", title="私有化与数据不出域部署", description="具备合规诉求的政企客户要求本地化部署，数据不允许离开自有机房或堡垒环境。", feedback_count=29, customer_count=9, industries=["智能制造", "能源化工"], product_potential="私有化部署包（Docker/K8s + 本地模型）", priority=5, status="open", created_at=_ago(days=1, hours=6)),
            CommonNeed(id="CN-003", title="统一认证与集团账号对接", description="国企与大型集团要求对接内部 OA、统一身份认证，账号体系需对齐集团标准。", feedback_count=18, customer_count=7, industries=["能源化工", "智能制造"], product_potential="企业版·SSO/标准协议联调", priority=4, status="planned", created_at=_ago(days=1, hours=23)),
            CommonNeed(id="CN-004", title="审计日志与合规报告", description="受 GDPR / 等保等约束的客户需要完整操作审计、留痕与合规导出能力。", feedback_count=27, customer_count=8, industries=["智能制造", "能源化工", "数据服务"], product_potential="企业版·审计日志与合规报表", priority=4, status="open", created_at=_ago(days=2, hours=7)),
        ]
        session.add_all(needs)
        session.commit()
        print(f"[seed] inserted {len(needs)} common_needs")
    else:
        print("[seed] common_needs already seeded, skip")


_RESET_MODELS: list[type[Any]] = [
    Feedback,
    InsightTopic,
    GovHotTopic,
    GovAlertItem,
    GovPolicyNotice,
    InterviewRecord,
    Agent,
    AgentTool,
    Skill,
    Workflow,
    WorkflowRun,
    RoadmapItem,
    TaskItem,
    ReplyDraft,
    ServerState,
    DatabaseState,
    ApiEndpointState,
    SystemLogEntry,
    ResourceAlert,
    ChannelConfig,
    Setting,
    AutomationRule,
    BusinessLead,
    MarketSignal,
    CommonNeed,
]


def seed_all(*, reset: bool = False) -> None:
    """灌入演示数据（幂等）。

    - reset=False（默认）：仅首次灌入，已存在的表数据保持不变（适合生产环境首次部署）。
    - reset=True：先清空演示表再重新生成，使所有时间字段按“当前时间”相对生成，
      保证种子数据始终落在最近时段（适合演示/联调环境刷新数据）。
    """
    session = SessionLocal()
    try:
        if reset:
            for model in _RESET_MODELS:
                session.execute(delete(model))
            session.commit()
            print("[seed] demo tables cleared")
        _seed_feedbacks(session)
        _seed_insight_topics(session)
        _seed_gov(session)
        _seed_interviews(session)
        _seed_agents(session)
        _seed_workflows(session)
        _seed_roadmap(session)
        _seed_resources(session)
        _seed_settings(session)
        _seed_automation(session)
        _seed_business(session)
        print("[seed] all done")
    except Exception as e:
        session.rollback()
        print(f"[seed] error: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    reset = "--reset" in sys.argv
    seed_all(reset=reset)
