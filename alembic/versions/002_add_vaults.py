"""Add vaults table and update documents table

Revision ID: 002
Revises: 001
Create Date: 2025-11-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TEXT, TIMESTAMP


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vaults table and add vault_id to documents."""
    
    # Create vaults table
    op.create_table(
        'vaults',
        sa.Column('vault_id', TEXT, primary_key=True),
        sa.Column('name', TEXT, nullable=False, unique=True),
        sa.Column('description', TEXT, nullable=True),
        sa.Column('created_at', TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', TIMESTAMP(timezone=True), server_default=sa.text('NOW()'), nullable=False)
    )
    
    # Create indexes on vaults table
    op.create_index('idx_vaults_name', 'vaults', ['name'])
    op.create_index('idx_vaults_created_at', 'vaults', [sa.text('created_at DESC')])
    
    # Add vault_id column to documents table
    op.add_column('documents', sa.Column('vault_id', TEXT, nullable=True))
    
    # Create index on documents.vault_id
    op.create_index('idx_documents_vault_id', 'documents', ['vault_id'])
    
    # Add foreign key constraint (with CASCADE delete)
    op.create_foreign_key(
        'fk_documents_vault_id',
        'documents', 'vaults',
        ['vault_id'], ['vault_id'],
        ondelete='CASCADE'
    )


def downgrade() -> None:
    """Drop vaults table and remove vault_id from documents."""
    
    # Drop foreign key constraint
    op.drop_constraint('fk_documents_vault_id', 'documents', type_='foreignkey')
    
    # Drop index on documents.vault_id
    op.drop_index('idx_documents_vault_id', table_name='documents')
    
    # Remove vault_id column from documents
    op.drop_column('documents', 'vault_id')
    
    # Drop indexes on vaults table
    op.drop_index('idx_vaults_created_at', table_name='vaults')
    op.drop_index('idx_vaults_name', table_name='vaults')
    
    # Drop vaults table
    op.drop_table('vaults')
