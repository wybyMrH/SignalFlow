"""feedback business code

Revision ID: 000000000004
Revises: 000000000003
Create Date: 2026-10-18 17:20:00.000000+00:00

反馈展示编号字段：
- feedbacks 增加 code（业务短编号，如 F1048），与前端 mock 数据 id 口径一致，
  使 8088(mock) 与 5199(真后端) 的「反馈管理」列表展示完全一致。
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = "000000000004"
down_revision: Union[str, None] = "000000000003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table_name: str, column_name: str) -> bool:
    """检查表中是否已存在指定列（幂等迁移）。"""
    bind = op.get_bind()
    insp = inspect(bind)
    return column_name in [c["name"] for c in insp.get_columns(table_name)]


def upgrade() -> None:
    if not _column_exists("feedbacks", "code"):
        op.add_column(
            "feedbacks",
            sa.Column("code", sa.String(length=32), nullable=True, comment="业务编号（展示用）"),
        )
        op.create_index("ix_feedbacks_code", "feedbacks", ["code"], unique=False)


def downgrade() -> None:
    if _column_exists("feedbacks", "code"):
        op.drop_index("ix_feedbacks_code", table_name="feedbacks")
        op.drop_column("feedbacks", "code")