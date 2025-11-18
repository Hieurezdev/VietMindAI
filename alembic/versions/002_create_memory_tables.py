"""Create memory tables (users, short_term_memories, long_term_memories)

Revision ID: 002
Revises: 001
Create Date: 2025-11-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create memory-related tables."""
    # Create users table
    op.create_table(
        "users",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("preferences", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "last_interaction",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("user_id", name=op.f("pk_users")),
    )

    # Create indexes for users
    op.create_index(op.f("ix_users_created_at"), "users", ["created_at"], unique=False)
    op.create_index(
        op.f("ix_users_last_interaction"), "users", ["last_interaction"], unique=False
    )

    # Create short_term_memories table
    op.create_table(
        "short_term_memories",
        sa.Column("memory_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="user"),
        sa.Column("embedding", Vector(768), nullable=False),
        sa.Column("turn_number", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            name=op.f("fk_short_term_memories_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("memory_id", name=op.f("pk_short_term_memories")),
    )

    # Create indexes for short_term_memories
    op.create_index(
        op.f("ix_stm_user_id"), "short_term_memories", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_stm_session_id"), "short_term_memories", ["session_id"], unique=False
    )
    op.create_index(
        op.f("ix_stm_created_at"), "short_term_memories", ["created_at"], unique=False
    )
    op.create_index(
        op.f("ix_stm_expires_at"), "short_term_memories", ["expires_at"], unique=False
    )

    # Create vector index for short_term_memories
    op.execute(
        """
        CREATE INDEX ix_stm_embedding
        ON short_term_memories
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )

    # Create long_term_memories table
    op.create_table(
        "long_term_memories",
        sa.Column("memory_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "memory_type",
            sa.String(length=100),
            nullable=False,
            server_default="general",
        ),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("importance", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("embedding", Vector(768), nullable=False),
        sa.Column("access_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_accessed", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            name=op.f("fk_long_term_memories_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("memory_id", name=op.f("pk_long_term_memories")),
    )

    # Create indexes for long_term_memories
    op.create_index(
        op.f("ix_ltm_user_id"), "long_term_memories", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_ltm_memory_type"), "long_term_memories", ["memory_type"], unique=False
    )
    op.create_index(
        op.f("ix_ltm_importance"), "long_term_memories", ["importance"], unique=False
    )
    op.create_index(
        op.f("ix_ltm_created_at"), "long_term_memories", ["created_at"], unique=False
    )
    op.create_index(
        op.f("ix_ltm_last_accessed"),
        "long_term_memories",
        ["last_accessed"],
        unique=False,
    )

    # Create vector index for long_term_memories
    op.execute(
        """
        CREATE INDEX ix_ltm_embedding
        ON long_term_memories
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )


def downgrade() -> None:
    """Drop memory-related tables."""
    # Drop long_term_memories indexes and table
    op.execute("DROP INDEX IF EXISTS ix_ltm_embedding")
    op.drop_index(op.f("ix_ltm_last_accessed"), table_name="long_term_memories")
    op.drop_index(op.f("ix_ltm_created_at"), table_name="long_term_memories")
    op.drop_index(op.f("ix_ltm_importance"), table_name="long_term_memories")
    op.drop_index(op.f("ix_ltm_memory_type"), table_name="long_term_memories")
    op.drop_index(op.f("ix_ltm_user_id"), table_name="long_term_memories")
    op.drop_table("long_term_memories")

    # Drop short_term_memories indexes and table
    op.execute("DROP INDEX IF EXISTS ix_stm_embedding")
    op.drop_index(op.f("ix_stm_expires_at"), table_name="short_term_memories")
    op.drop_index(op.f("ix_stm_created_at"), table_name="short_term_memories")
    op.drop_index(op.f("ix_stm_session_id"), table_name="short_term_memories")
    op.drop_index(op.f("ix_stm_user_id"), table_name="short_term_memories")
    op.drop_table("short_term_memories")

    # Drop users indexes and table
    op.drop_index(op.f("ix_users_last_interaction"), table_name="users")
    op.drop_index(op.f("ix_users_created_at"), table_name="users")
    op.drop_table("users")
