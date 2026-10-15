"""SignalFlow 后端 - 提示词模板单元测试。"""

from __future__ import annotations

import pytest

from app.llm.prompts import list_scenes, load


def test_list_scenes_contains_all_expected():
    scenes = list_scenes()
    assert set(scenes) == {"dedup", "cluster", "eval", "priority", "draft"}


def test_load_returns_system_and_user_messages():
    messages = load("cluster", feedbacks="group A")
    assert [m["role"] for m in messages] == ["system", "user"]
    assert "group A" in messages[1]["content"]
    assert "聚类" in messages[0]["content"]


def test_load_variables_interpolated():
    messages = load("dedup", feedbacks="f1: 加载很慢")
    assert "f1: 加载很慢" in messages[1]["content"]
    # 变量已被替换，不应残留 Python 格式占位符
    assert "{feedbacks}" not in messages[1]["content"]


def test_load_unknown_scene_raises():
    with pytest.raises(KeyError):
        load("unknown_scene", feedbacks="x")


def test_load_all_scenes_compile():
    """所有内置模板均能被 format 渲染，无 Python 占位符残留。"""
    samples = {
        "feedbacks": "f1",
        "topics": "主题: 性能",
        "assessments": "性能: impact=80",
        "decisions": "性能: action=跟进",
    }
    for scene in list_scenes():
        messages = load(scene, **samples)
        assert len(messages) == 2
        for msg in messages:
            content = msg["content"]
            assert "{feedbacks}" not in content
            assert "{topics}" not in content
            assert "{assessments}" not in content
            assert "{decisions}" not in content