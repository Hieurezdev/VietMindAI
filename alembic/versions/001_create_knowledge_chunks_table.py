"""Create knowledge_chunks table with pgvector support

Revision ID: 001
Revises:
Create Date: 2025-11-18

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql as pg

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create knowledge_chunks table with pgvector extension."""
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create knowledge_chunks table
    op.create_table(
        "knowledge_chunks",
        sa.Column("uuid", sa.UUID(), nullable=False),
        sa.Column("headers", sa.Text(), nullable=False, server_default=""),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("keywords", pg.ARRAY(sa.Text()), nullable=False, server_default=sa.text("ARRAY[]::text[]")),
        sa.Column("type", sa.String(length=100), nullable=False, server_default=""),
        sa.Column("embedding", Vector(768), nullable=False),
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
        sa.PrimaryKeyConstraint("uuid", name=op.f("pk_knowledge_chunks")),
    )

    # Create indexes
    op.create_index(
        "ix_knowledge_chunks_type",
        "knowledge_chunks",
        ["type"],
        unique=False,
    )
    op.create_index(
        "ix_knowledge_chunks_created_at",
        "knowledge_chunks",
        ["created_at"],
        unique=False,
    )

    # Create vector index for similarity search using IVFFLAT
    # Note: IVFFLAT requires training data, so we create it after some data is inserted
    # For now, we create it with a small lists parameter
    op.execute(
        """
        CREATE INDEX ix_knowledge_chunks_embedding
        ON knowledge_chunks
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
        """
    )


def downgrade() -> None:
    """Drop knowledge_chunks table and pgvector extension."""
    # Drop indexes
    op.drop_index("ix_knowledge_chunks_embedding", table_name="knowledge_chunks")
    op.drop_index(
        op.f("ix_knowledge_chunks_created_at"), table_name="knowledge_chunks"
    )
    op.drop_index(op.f("ix_knowledge_chunks_type"), table_name="knowledge_chunks")

    # Drop table
    op.drop_table("knowledge_chunks")

    # Note: We don't drop the vector extension as it might be used by other tables
    # op.execute("DROP EXTENSION IF EXISTS vector")
