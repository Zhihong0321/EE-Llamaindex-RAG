"""Add agents table

Revision ID: 003
Revises: 002
Create Date: 2025-11-29

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create agents table."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS agents (
            agent_id TEXT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            vault_id TEXT NOT NULL REFERENCES vaults(vault_id) ON DELETE CASCADE,
            system_prompt TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            CONSTRAINT agents_name_vault_unique UNIQUE (name, vault_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_agents_vault_id ON agents(vault_id);
        CREATE INDEX IF NOT EXISTS idx_agents_created_at ON agents(created_at DESC);
    """)


def downgrade() -> None:
    """Drop agents table."""
    op.execute("DROP TABLE IF EXISTS agents CASCADE;")
