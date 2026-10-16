"""stage6 contract extensions

Revision ID: 000000000002
Revises: 000000000001
Create Date: 2026-10-15 18:10:00.000000+00:00

阶段 6 前后端联调契约扩展：
- feedbacks 增加前端 FeedbackView 展示扩展字段（sentiment / priority / topic 归属 / 处理人 / 回复内容）
- gov_policy_notices 增加送达人数与阅读率（前端 GovPolicyNotice 契约）
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "000000000002"
down_revision: Union[str, None] = "acf648a5708e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """检查表中是否已存在指定列。"""
    bind = op.get_bind()
    insp = inspect(bind)
    columns = [c["name"] for c in insp.get_columns(table_name)]
    return column_name in columns


def upgrade() -> None:
    # 反馈扩展字段（前端 FeedbackView 契约；仅展示用途，可为空）
    if not _column_exists("feedbacks", "sentiment"):
        op.add_column(
            "feedbacks",
            sa.Column(
                "sentiment",
                sa.String(length=16),
                nullable=True,
                comment="情感倾向：positive / neutral / negative",
            ),
        )
    if not _column_exists("feedbacks", "priority"):
        op.add_column(
            "feedbacks",
            sa.Column(
                "priority",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
                comment="优先级 0-5（AI 分析切片回填）",
            ),
        )
    if not _column_exists("feedbacks", "topic_id"):
        op.add_column(
            "feedbacks",
            sa.Column(
                "topic_id",
                sa.String(length=36),
                nullable=True,
                comment="归属洞察主题 id",
            ),
        )
    if not _column_exists("feedbacks", "topic_title"):
        op.add_column(
            "feedbacks",
            sa.Column(
                "topic_title",
                sa.String(length=256),
                nullable=True,
                comment="归属洞察主题标题（冗余展示）",
            ),
        )
    if not _column_exists("feedbacks", "reviewer"):
        op.add_column(
            "feedbacks",
            sa.Column(
                "reviewer",
                sa.String(length=128),
                nullable=True,
                comment="当前处理人",
            ),
        )
    if not _column_exists("feedbacks", "reply_content"):
        op.add_column(
            "feedbacks",
            sa.Column(
                "reply_content",
                sa.Text(),
                nullable=True,
                comment="已回复内容（人工/AI 生成）",
            ),
        )
    if not _column_exists("feedbacks", "replied_at"):
        op.add_column(
            "feedbacks",
            sa.Column(
                "replied_at",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="回复时间",
            ),
        )

    # 政策告知扩展字段（前端契约：送达人数 / 阅读率）
    if not _column_exists("gov_policy_notices", "sent_count"):
        op.add_column(
            "gov_policy_notices",
            sa.Column(
                "sent_count",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("0"),
                comment="送达人数",
            ),
        )
    if not _column_exists("gov_policy_notices", "read_rate"):
        op.add_column(
            "gov_policy_notices",
            sa.Column(
                "read_rate",
                sa.Float(),
                nullable=False,
                server_default=sa.text("0"),
                comment="阅读率 0-1",
            ),
        )


def downgrade() -> None:
    if _column_exists("gov_policy_notices", "read_rate"):
        op.drop_column("gov_policy_notices", "read_rate")
    if _column_exists("gov_policy_notices", "sent_count"):
        op.drop_column("gov_policy_notices", "sent_count")
    if _column_exists("feedbacks", "replied_at"):
        op.drop_column("feedbacks", "replied_at")
    if _column_exists("feedbacks", "reply_content"):
        op.drop_column("feedbacks", "reply_content")
    if _column_exists("feedbacks", "reviewer"):
        op.drop_column("feedbacks", "reviewer")
    if _column_exists("feedbacks", "topic_title"):
        op.drop_column("feedbacks", "topic_title")
    if _column_exists("feedbacks", "topic_id"):
        op.drop_column("feedbacks", "topic_id")
    if _column_exists("feedbacks", "priority"):
        op.drop_column("feedbacks", "priority")
    if _column_exists("feedbacks", "sentiment"):
        op.drop_column("feedbacks", "sentiment")