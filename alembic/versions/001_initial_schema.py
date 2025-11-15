"""Initial schema with sessions, messages, and documents tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, TEXT, TIMESTAMP


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial database schema."""
    
    # Enable pgvector extension
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')
    
    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', TEXT, primary_key=True),
        sa.Column('user_id', TEXT, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('last_active_at', TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    
    # Create index on sessions.last_active_at
    op.create_index('idx_sessions_last_active', 'sessions', ['last_active_at'])
    
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column('session_id', TEXT, sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('role', TEXT, nullable=False),
        sa.Column('content', TEXT, nullable=False),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant', 'system')", name='check_message_role')
    )
    
    # Create composite index on messages(session_id, created_at)
    op.create_index('idx_messages_session_created', 'messages', ['session_id', sa.text('created_at DESC')])
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', TEXT, primary_key=True),
        sa.Column('title', TEXT, nullable=True),
        sa.Column('source', TEXT, nullable=True),
        sa.Column('metadata_json', JSONB, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    
    # Create index on documents.created_at
    op.create_index('idx_documents_created', 'documents', [sa.text('created_at DESC')])


def downgrade() -> None:
    """Drop all tables and extension."""
    
    # Drop indexes
    op.drop_index('idx_documents_created', table_name='documents')
    op.drop_index('idx_messages_session_created', table_name='messages')
    op.drop_index('idx_sessions_last_active', table_name='sessions')
    
    # Drop tables
    op.drop_table('documents')
    op.drop_table('messages')
    op.drop_table('sessions')
    
    # Drop pgvector extension
    op.execute('DROP EXTENSION IF EXISTS vector')
