"""add deleted flag to books

Revision ID: 9f3c2b1a7d4e
Revises: f6c1b8d4a9e2
Create Date: 2026-03-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9f3c2b1a7d4e'
down_revision = 'f6c1b8d4a9e2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('books', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))

    with op.batch_alter_table('books', schema=None) as batch_op:
        batch_op.alter_column('deleted', server_default=None)


def downgrade():
    with op.batch_alter_table('books', schema=None) as batch_op:
        batch_op.drop_column('deleted')
