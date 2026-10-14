"""SignalFlow 后端 - 工作流状态定义（LangGraph State）。

State 是图中各节点共享的容器：输入原始反馈，逐节点填充派生结果。
字段标注为可选，表示"尚未由对应节点产出"；权威业务状态在持久化层。
"""

from typing import Annotated, TypedDict


class FeedbackAnalysisState(TypedDict, total=False):
    """反馈分析工作流的共享状态。"""

    # 输入：本次批量分析的反馈原文列表
    feedback_ids: list[str]
    contents: list[str]
    tenant_id: str

    # 派生数据（节点产出，未产出前为缺省）
    embeddings: Annotated[list[list[float]], "由去重/向量节点填充"]
    dedup_groups: list[list[str]]
    clusters: Annotated[list[dict], "聚类结果：cluster_id -> member ids"]
    themes: list[str]
    pain_points: list[dict]
    impact_assessments: list[dict]
    priorities: list[dict]
    decisions: Annotated[list[dict], "候选+置信度决策建议"]
    reply_drafts: list[dict]

    # 执行元信息
    error: str | None