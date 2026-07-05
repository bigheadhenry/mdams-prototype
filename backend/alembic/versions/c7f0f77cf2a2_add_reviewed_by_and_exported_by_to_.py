"""add reviewed_by and exported_by to applications

Revision ID: c7f0f77cf2a2
Revises: 001dea3060cf
Create Date: 2026-06-23 17:33:54.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c7f0f77cf2a2"
down_revision: Union[str, Sequence[str], None] = "001dea3060cf"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("applications", sa.Column("reviewed_by_user_id", sa.Integer(), nullable=True))
    op.add_column("applications", sa.Column("exported_by_user_id", sa.Integer(), nullable=True))
    op.create_index(
        op.f("ix_applications_reviewed_by_user_id"),
        "applications",
        ["reviewed_by_user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_applications_exported_by_user_id"),
        "applications",
        ["exported_by_user_id"],
        unique=False,
    )
    op.create_foreign_key(
        "fk_applications_reviewed_by_user_id",
        "applications",
        "users",
        ["reviewed_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_applications_exported_by_user_id",
        "applications",
        "users",
        ["exported_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint("fk_applications_exported_by_user_id", "applications", type_="foreignkey")
    op.drop_constraint("fk_applications_reviewed_by_user_id", "applications", type_="foreignkey")
    op.drop_index(op.f("ix_applications_exported_by_user_id"), table_name="applications")
    op.drop_index(op.f("ix_applications_reviewed_by_user_id"), table_name="applications")
    op.drop_column("applications", "exported_by_user_id")
    op.drop_column("applications", "reviewed_by_user_id")
