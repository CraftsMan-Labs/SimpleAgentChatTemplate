"""initial schema

Revision ID: 20260304_0001
Revises:
Create Date: 2026-03-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260304_0001"
down_revision = None
branch_labels = None
depends_on = None


def _jsonb_or_json() -> sa.types.TypeEngine:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return postgresql.JSONB(astext_type=sa.Text())
    return sa.JSON()


def _uuid_or_str() -> sa.types.TypeEngine:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        return postgresql.UUID(as_uuid=True)
    return sa.String(length=36)


def upgrade() -> None:
    uuid_type = _uuid_or_str()
    json_type = _jsonb_or_json()

    op.create_table(
        "workflow_models",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("workflow_id", sa.String(length=255), nullable=False),
        sa.Column("workflow_path", sa.Text(), nullable=False),
        sa.Column("registry", json_type, nullable=False),
        sa.Column("metadata", json_type, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("model_id"),
    )

    op.create_table(
        "conversations",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("external_conversation_id", sa.String(length=255), nullable=True),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("user_id", sa.String(length=255), nullable=True),
        sa.Column("theme", sa.String(length=16), nullable=True),
        sa.Column(
            "status", sa.String(length=32), nullable=False, server_default="active"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_conversation_id"),
    )

    op.create_table(
        "messages",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("conversation_id", uuid_type, nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=True),
        sa.Column("tool_call_id", sa.String(length=255), nullable=True),
        sa.Column("tool_calls", json_type, nullable=True),
        sa.Column("metadata", json_type, nullable=False),
        sa.Column("turn_index", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_messages_conversation_turn", "messages", ["conversation_id", "turn_index"]
    )

    op.create_table(
        "workflow_runs",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("conversation_id", uuid_type, nullable=False),
        sa.Column("request_message_id", uuid_type, nullable=True),
        sa.Column("response_message_id", uuid_type, nullable=True),
        sa.Column("model_id", sa.String(length=255), nullable=False),
        sa.Column("workflow_id", sa.String(length=255), nullable=False),
        sa.Column("workflow_path", sa.Text(), nullable=False),
        sa.Column("terminal_node", sa.String(length=255), nullable=True),
        sa.Column("terminal_output", json_type, nullable=True),
        sa.Column("trace", json_type, nullable=True),
        sa.Column("trace_id", sa.String(length=255), nullable=True),
        sa.Column("step_timings", json_type, nullable=True),
        sa.Column("usage", json_type, nullable=True),
        sa.Column("total_elapsed_ms", sa.Integer(), nullable=True),
        sa.Column("raw_result", json_type, nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error", json_type, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["conversation_id"], ["conversations.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "workflow_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", uuid_type, nullable=False),
        sa.Column("seq", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("node_id", sa.String(length=255), nullable=True),
        sa.Column("delta", sa.Text(), nullable=True),
        sa.Column("payload", json_type, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["run_id"], ["workflow_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "seq", name="uq_workflow_events_run_seq"),
    )
    op.create_index("ix_workflow_events_run_seq", "workflow_events", ["run_id", "seq"])


def downgrade() -> None:
    op.drop_index("ix_workflow_events_run_seq", table_name="workflow_events")
    op.drop_table("workflow_events")
    op.drop_table("workflow_runs")
    op.drop_index("ix_messages_conversation_turn", table_name="messages")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("workflow_models")
