"""SignalFlow 后端 - 提示词模板加载。

开发期支持热加载（按 scene 名返回内置模板）；
生产期可扩展为从文件系统/对象存储加载。
"""

from __future__ import annotations

from typing import Any


# 内置提示词模板（scene -> system/user 消息）
# 注意：JSON 示例中的字面花括号须写成 {{ }}，避免被 str.format 当作占位符。
_BUILTIN_TEMPLATES: dict[str, dict[str, str]] = {
    "dedup": {
        "system": "你是一位反馈去重专家。请判断以下反馈列表中是否存在语义重复，返回 JSON：{{groups: [[id1, id2], [id3]]}}。",
        "user": "反馈列表（每条含 id 与内容）：\n{feedbacks}",
    },
    "cluster": {
        "system": "你是一位客户反馈聚类专家。请对去重后的反馈进行主题聚类，返回 JSON：{{clusters: [{{theme: '...', member_ids: [...], pain_points: [{{topic: '...', severity: 1-5}}]}}]}}。",
        "user": "去重后的反馈列表：\n{feedbacks}",
    },
    "eval": {
        "system": "你是一位客户体验评估专家。请评估每个主题的影响面与客户价值，返回 JSON：{{assessments: [{{topic: '...', impact_score: 0-100, customer_value: 0-100, confidence: 0.0-1.0}}]}}。",
        "user": "主题与证据链：\n{topics}",
    },
    "priority": {
        "system": "你是一位产品优先级分析师。请基于 RICE 思想给出优先级排序，返回 JSON：{{priorities: [{{topic: '...', priority_score: 0-100, rank: 1}}], decisions: [{{topic: '...', action: '...', confidence: 0.0-1.0}}]}}。",
        "user": "评估结果：\n{assessments}",
    },
    "draft": {
        "system": "你是一位客户成功专家。请为高优先级主题生成回复草稿，返回 JSON：{{drafts: [{{content: '...', target_feedback_ids: [...], priority: 0-100}}]}}。",
        "user": "高优先级项：\n{decisions}",
    },
}


def load(scene: str, **variables: Any) -> list[dict[str, str]]:
    """加载指定场景的提示词模板，并填充变量。

    Returns
    -------
    messages : list[dict[str, str]]
        OpenAI 格式的消息列表 [{"role": "system", "content": ...}, {"role": "user", "content": ...}]
    """
    tmpl = _BUILTIN_TEMPLATES.get(scene)
    if tmpl is None:
        raise KeyError(f"Prompt scene '{scene}' not found")
    messages: list[dict[str, str]] = []
    if "system" in tmpl:
        messages.append({"role": "system", "content": tmpl["system"].format(**variables)})
    messages.append({"role": "user", "content": tmpl["user"].format(**variables)})
    return messages


def list_scenes() -> list[str]:
    """返回所有可用场景名称。"""
    return list(_BUILTIN_TEMPLATES.keys())