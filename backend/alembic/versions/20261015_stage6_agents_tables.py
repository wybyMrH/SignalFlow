"""stage6 agents/skills tables

Revision ID: 000000000003
Revises: 000000000002
Create Date: 2026-10-15 19:15:00.000000+00:00

阶段 6 前后端联调契约补充：
- agents：AI Agent 定义表（前端 AgentStatus 契约）
- agent_tools：Agent 可配置工具目录（前端 AgentToolDef 契约）
- skills：Skill 领域能力包（前端 SkillDef 契约）
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "000000000003"
down_revision: Union[str, None] = "000000000002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    """检查表是否已存在（幂等迁移）。"""
    bind = op.get_bind()
    insp = inspect(bind)
    return insp.has_table(table_name)


def upgrade() -> None:
    if not _table_exists("agents"):
        op.create_table(
            "agents",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("category", sa.String(length=64), nullable=True),
            sa.Column("scenario", sa.Text(), nullable=True),
            sa.Column("enabled", sa.Boolean(), nullable=False),
            sa.Column("tools", sa.JSON(), nullable=True),
            sa.Column("bound_workflow_ids", sa.JSON(), nullable=True),
            sa.Column("run_count", sa.Integer(), nullable=False),
            sa.Column("reliability", sa.Integer(), nullable=False),
            sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("preset", sa.Boolean(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )

    if not _table_exists("agent_tools"):
        op.create_table(
            "agent_tools",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("key", sa.String(length=64), nullable=False),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("category", sa.String(length=64), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("key"),
        )

    if not _table_exists("skills"):
        op.create_table(
            "skills",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("name", sa.String(length=128), nullable=False),
            sa.Column("category", sa.String(length=64), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("enabled", sa.Boolean(), nullable=False),
            sa.Column("owner_agent_ids", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    if _table_exists("skills"):
        op.drop_table("skills")
    if _table_exists("agent_tools"):
        op.drop_table("agent_tools")
    if _table_exists("agents"):
        op.drop_table("agents")