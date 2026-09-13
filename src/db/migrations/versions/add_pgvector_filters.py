"""add_pgvector_embedding_and_filters

Revision ID: add_pgvector_embedding_and_filters
Revises: add_document_versioning
Create Date: 2026-09-12 22:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision: str = 'add_pgvector_filters'
down_revision: Union[str, Sequence[str], None] = 'add_document_versioning'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Separate text content from filtering metadata.

    - Adds a real pgvector column (``embedding_vector``, 384 dims) so retrieval
      uses native distance operators instead of a JSON blob.
    - Lifts hot filter fields (tenant_id, access_roles, category, department,
      classification, language) out of the JSONB payload into queryable columns.
    - Backfills both from the existing ``embedding`` / ``lineage`` JSON so no
      re-embedding is required.
    """
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column('chunks', sa.Column('embedding_vector', Vector(384), nullable=True))
    op.add_column('chunks', sa.Column('tenant_id', sa.String(), nullable=True))
    op.add_column('chunks', sa.Column('access_roles', postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column('chunks', sa.Column('category', sa.String(), nullable=True))
    op.add_column('chunks', sa.Column('department', sa.String(), nullable=True))
    op.add_column('chunks', sa.Column('classification', sa.String(), nullable=True))
    op.add_column('chunks', sa.Column('language', sa.String(), nullable=True))

    # Backfill the pgvector column from the stored JSON embedding
    op.execute(
        "UPDATE chunks SET embedding_vector = (embedding::text)::vector "
        "WHERE embedding IS NOT NULL"
    )

    # Backfill filter columns from the lineage JSON payload
    op.execute(
        "UPDATE chunks SET "
        "tenant_id = lineage->>'tenant_id', "
        "access_roles = lineage->'access_roles', "
        "category = lineage->>'category', "
        "department = lineage->>'department', "
        "classification = lineage->>'classification', "
        "language = lineage->>'language'"
    )

    # Inherit document-level taxonomy into chunks so each chunk is
    # independently filterable (category, department, doc_type live in the
    # parent document's meta payload, not the chunk lineage).
    op.execute(
        "UPDATE chunks c SET "
        "category = COALESCE(NULLIF(c.category, ''), d.meta->>'category'), "
        "department = COALESCE(NULLIF(c.department, ''), d.meta->>'department'), "
        "classification = COALESCE(NULLIF(c.classification, ''), d.meta->>'classification'), "
        "language = COALESCE(NULLIF(c.language, ''), d.meta->>'language') "
        "FROM documents d WHERE d.id = c.document_id"
    )

    op.execute(
        "CREATE INDEX ix_chunks_embedding_vector_hnsw ON chunks "
        "USING hnsw (embedding_vector vector_cosine_ops)"
    )
    op.create_index('ix_chunks_tenant_id', 'chunks', ['tenant_id'], unique=False)
    op.create_index('ix_chunks_category', 'chunks', ['category'], unique=False)
    op.execute(
        "CREATE INDEX ix_chunks_access_roles_gin ON chunks "
        "USING gin (access_roles jsonb_path_ops)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_chunks_access_roles_gin', table_name='chunks')
    op.drop_index('ix_chunks_category', table_name='chunks')
    op.drop_index('ix_chunks_tenant_id', table_name='chunks')
    op.drop_index('ix_chunks_embedding_vector_hnsw', table_name='chunks')
    op.drop_column('chunks', 'language')
    op.drop_column('chunks', 'classification')
    op.drop_column('chunks', 'department')
    op.drop_column('chunks', 'category')
    op.drop_column('chunks', 'access_roles')
    op.drop_column('chunks', 'tenant_id')
    op.drop_column('chunks', 'embedding_vector')