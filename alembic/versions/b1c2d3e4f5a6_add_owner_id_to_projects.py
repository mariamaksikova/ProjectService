"""add owner_id to projects

Revision ID: b1c2d3e4f5a6
Revises: afca0b3f52b9
Create Date: 2026-05-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = 'afca0b3f52b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('projects', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.create_index('ix_projects_owner_id', 'projects', ['owner_id'])
    # Для существующих строк ставим owner_id=1 (дефолтный пользователь)
    op.execute("UPDATE projects SET owner_id = 1 WHERE owner_id IS NULL")
    op.alter_column('projects', 'owner_id', nullable=False)


def downgrade() -> None:
    op.drop_index('ix_projects_owner_id', table_name='projects')
    op.drop_column('projects', 'owner_id')
