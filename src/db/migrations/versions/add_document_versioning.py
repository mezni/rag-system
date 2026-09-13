"""add_document_versioning

Revision ID: add_document_versioning
Revises: initial_schema
Create Date: 2026-09-12 20:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_document_versioning'
down_revision: Union[str, Sequence[str], None] = 'initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add pipeline-owned versioning (version + is_active) to documents/chunks.

    A modified file creates a new ``documents`` row (``version = prev + 1``,
    ``is_active = true``) while older versions are deactivated. Deletions flag
    ``is_active = false`` across every version of a source without erasing
    history. ``source_id`` therefore loses its uniqueness constraint.
    """
    op.add_column('documents', sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('documents', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')))
    op.add_column('chunks', sa.Column('version', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('chunks', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')))

    # Backfill from existing lifecycle/status flags
    op.execute("UPDATE documents SET is_active = (lifecycle_state = 'active')")
    op.execute("UPDATE chunks SET is_active = (status = 'active')")

    # Multiple versions of one source may now coexist
    op.drop_index(op.f('ix_documents_source_id'), table_name='documents')
    op.create_index(op.f('ix_documents_source_id'), 'documents', ['source_id'], unique=False)
    op.create_index('ix_documents_source_id_is_active', 'documents', ['source_id', 'is_active'], unique=False)
    op.create_index('ix_documents_source_id_version', 'documents', ['source_id', 'version'], unique=False)
    op.create_index('ix_chunks_document_id_is_active', 'chunks', ['document_id', 'is_active'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_chunks_document_id_is_active', table_name='chunks')
    op.drop_index('ix_documents_source_id_version', table_name='documents')
    op.drop_index('ix_documents_source_id_is_active', table_name='documents')
    op.drop_index(op.f('ix_documents_source_id'), table_name='documents')
    op.create_index(op.f('ix_documents_source_id'), 'documents', ['source_id'], unique=True)
    op.drop_column('chunks', 'is_active')
    op.drop_column('chunks', 'version')
    op.drop_column('documents', 'is_active')
    op.drop_column('documents', 'version')