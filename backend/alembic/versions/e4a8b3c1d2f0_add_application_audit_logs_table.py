"""add application_audit_logs table

Revision ID: e4a8b3c1d2f0
Revises: c7f0f77cf2a2
Create Date: 2026-06-23 17:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4a8b3c1d2f0"
down_revision: Union[str, Sequence[str], None] = "c7f0f77cf2a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "application_audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("application_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("from_status", sa.String(), nullable=True),
        sa.Column("to_status", sa.String(), nullable=True),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("actor_display_name", sa.String(), nullable=True),
        sa.Column("review_note", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_application_audit_logs_id"), "application_audit_logs", ["id"], unique=False)
    op.create_index(op.f("ix_application_audit_logs_application_id"), "application_audit_logs", ["application_id"], unique=False)
    op.create_index(op.f("ix_application_audit_logs_action"), "application_audit_logs", ["action"], unique=False)
    op.create_index(op.f("ix_application_audit_logs_actor_user_id"), "application_audit_logs", ["actor_user_id"], unique=False)
    op.create_index(op.f("ix_application_audit_logs_created_at"), "application_audit_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_application_audit_logs_created_at"), table_name="application_audit_logs")
    op.drop_index(op.f("ix_application_audit_logs_actor_user_id"), table_name="application_audit_logs")
    op.drop_index(op.f("ix_application_audit_logs_action"), table_name="application_audit_logs")
    op.drop_index(op.f("ix_application_audit_logs_application_id"), table_name="application_audit_logs")
    op.drop_index(op.f("ix_application_audit_logs_id"), table_name="application_audit_logs")
    op.drop_table("application_audit_logs")
