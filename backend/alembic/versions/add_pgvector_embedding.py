"""add pgvector and product embedding

Revision ID: add_pgvector_embedding
Revises: 54eb8db08ec2
Create Date: 2026-05-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_pgvector_embedding'
down_revision: Union[str, None] = '54eb8db08ec2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable the pgvector extension natively in PostgreSQL
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # 2. Add the embedding column to products using raw SQL
    op.execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS embedding vector(1024);")


def downgrade() -> None:
    # Drop embedding column using raw SQL
    op.execute("ALTER TABLE products DROP COLUMN IF EXISTS embedding;")
    # Note: We do not drop the extension to avoid breaking other schemas

