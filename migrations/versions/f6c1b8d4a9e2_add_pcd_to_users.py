"""add pcd to users

Revision ID: f6c1b8d4a9e2
Revises: e4f9c2ab17de
Create Date: 2026-03-10 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f6c1b8d4a9e2'
down_revision = 'e4f9c2ab17de'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('users', sa.Column('pcd', sa.Boolean(), nullable=False, server_default=sa.text('false')))
    op.alter_column('users', 'pcd', server_default=None)


def downgrade():
    op.drop_column('users', 'pcd')
