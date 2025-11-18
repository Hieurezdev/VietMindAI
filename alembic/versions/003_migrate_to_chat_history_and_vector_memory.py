"""Migrate to ChatHistory and VectorMemory tables

Revision ID: 003
Revises: 002
Create Date: 2025-01-18 00:00:00.000000

This migration converts the old 2-table memory system (ShortTermMemory, LongTermMemory)
to the new 2-table system (ChatHistory, VectorMemory).

Changes:
- Drop old tables: short_term_memories, long_term_memories
- Create new tables: chat_history, vector_memories
- Keep users and knowledge_chunks tables unchanged
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade to ChatHistory and VectorMemory tables."""

    # Drop old memory tables (if they exist)
    op.execute("DROP TABLE IF EXISTS short_term_memories CASCADE")
    op.execute("DROP TABLE IF EXISTS long_term_memories CASCADE")

    # Create chat_history table (replaces short_term_memories)
    op.create_table(
        'chat_history',
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='User ID'),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False, comment='Session ID to group conversation turns'),
        sa.Column('role', sa.String(length=20), nullable=False, comment='Role: user, assistant, system'),
        sa.Column('content', sa.Text(), nullable=False, comment='Message content'),
        sa.Column('turn_number', sa.Integer(), nullable=False, server_default='0', comment='Turn number in conversation'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True, comment='When this chat history should expire'),
        sa.PrimaryKeyConstraint('message_id')
    )

    # Create indexes for chat_history
    op.create_index('ix_chat_history_user_session', 'chat_history', ['user_id', 'session_id'])
    op.create_index('ix_chat_history_user_created', 'chat_history', ['user_id', 'created_at'])
    op.create_index(op.f('ix_chat_history_user_id'), 'chat_history', ['user_id'])
    op.create_index(op.f('ix_chat_history_created_at'), 'chat_history', ['created_at'])
    op.create_index(op.f('ix_chat_history_expires_at'), 'chat_history', ['expires_at'])

    # Create vector_memories table (replaces long_term_memories)
    op.create_table(
        'vector_memories',
        sa.Column('memory_id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, comment='User ID'),
        sa.Column('content', sa.Text(), nullable=False, comment='Summarized content or insight from conversation'),
        sa.Column('summary', sa.Text(), nullable=False, server_default='', comment='Brief summary (5-20 words)'),
        sa.Column('memory_type', sa.String(length=50), nullable=False, server_default='episodic', comment='Type: episodic, insight, pattern, event, etc.'),
        sa.Column('tags', sa.Text(), nullable=False, server_default='', comment='Comma-separated tags (e.g., \'work,stress,anxiety\')'),
        sa.Column('importance', sa.Float(), nullable=False, server_default='0.5', comment='Importance score (0.0 to 1.0)'),
        sa.Column('embedding', Vector(768), nullable=False, comment='768-dimensional embedding from Gemini'),
        sa.Column('source_session_id', postgresql.UUID(as_uuid=True), nullable=True, comment='Original session ID if created from chat consolidation'),
        sa.Column('event_date', sa.DateTime(timezone=True), nullable=True, comment='When the event/episode occurred (if applicable)'),
        sa.Column('access_count', sa.Integer(), nullable=False, server_default='0', comment='Number of times this memory was accessed'),
        sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True, comment='Last time this memory was accessed'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('memory_id')
    )

    # Create indexes for vector_memories
    op.create_index('ix_vector_memories_user_id', 'vector_memories', ['user_id'])
    op.create_index('ix_vector_memories_memory_type', 'vector_memories', ['memory_type'])
    op.create_index('ix_vector_memories_importance', 'vector_memories', ['importance'])
    op.create_index('ix_vector_memories_created_at', 'vector_memories', ['created_at'])
    op.create_index('ix_vector_memories_event_date', 'vector_memories', ['event_date'])

    # Create vector similarity search index for vector_memories
    op.execute("""
        CREATE INDEX ix_vector_memories_embedding
        ON vector_memories
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)


def downgrade() -> None:
    """Downgrade back to ShortTermMemory and LongTermMemory tables."""

    # Drop new tables
    op.drop_table('vector_memories')
    op.drop_table('chat_history')

    # Recreate old short_term_memories table
    op.create_table(
        'short_term_memories',
        sa.Column('memory_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False, server_default='user'),
        sa.Column('embedding', Vector(768), nullable=False),
        sa.Column('turn_number', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('memory_id')
    )
    op.create_index('ix_stm_user_id', 'short_term_memories', ['user_id'])
    op.create_index('ix_stm_session_id', 'short_term_memories', ['session_id'])
    op.create_index('ix_stm_created_at', 'short_term_memories', ['created_at'])
    op.create_index('ix_stm_expires_at', 'short_term_memories', ['expires_at'])
    op.execute("""
        CREATE INDEX ix_stm_embedding
        ON short_term_memories
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)

    # Recreate old long_term_memories table
    op.create_table(
        'long_term_memories',
        sa.Column('memory_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('memory_type', sa.String(length=100), nullable=False, server_default='general'),
        sa.Column('summary', sa.Text(), nullable=False, server_default=''),
        sa.Column('importance', sa.Float(), nullable=False, server_default='0.5'),
        sa.Column('embedding', Vector(768), nullable=False),
        sa.Column('access_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_accessed', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('memory_id')
    )
    op.create_index('ix_ltm_user_id', 'long_term_memories', ['user_id'])
    op.create_index('ix_ltm_memory_type', 'long_term_memories', ['memory_type'])
    op.create_index('ix_ltm_importance', 'long_term_memories', ['importance'])
    op.create_index('ix_ltm_created_at', 'long_term_memories', ['created_at'])
    op.create_index('ix_ltm_last_accessed', 'long_term_memories', ['last_accessed'])
    op.execute("""
        CREATE INDEX ix_ltm_embedding
        ON long_term_memories
        USING ivfflat (embedding vector_cosine_ops)
        WITH (lists = 100)
    """)
