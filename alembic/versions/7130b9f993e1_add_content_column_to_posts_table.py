"""add content column to posts table

Revision ID: 7130b9f993e1
Revises: 08dae2beaa29
Create Date: 2026-02-04 15:50:01.055826

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7130b9f993e1'
down_revision: Union[str, Sequence[str], None] = '08dae2beaa29'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('posts', sa.Column('content', sa.String(), nullable=False))


def downgrade() -> None:
    op.drop_column('posts', 'content')
    pass
