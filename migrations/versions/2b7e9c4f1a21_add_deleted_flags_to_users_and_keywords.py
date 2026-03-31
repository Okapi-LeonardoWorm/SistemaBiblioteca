"""add deleted flags to users and keywords

Revision ID: 2b7e9c4f1a21
Revises: 9f3c2b1a7d4e
Create Date: 2026-03-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2b7e9c4f1a21'
down_revision = '9f3c2b1a7d4e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))

    with op.batch_alter_table('keyWords', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')))

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('deleted', server_default=None)

    with op.batch_alter_table('keyWords', schema=None) as batch_op:
        batch_op.alter_column('deleted', server_default=None)


def downgrade():
    with op.batch_alter_table('keyWords', schema=None) as batch_op:
        batch_op.drop_column('deleted')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('deleted')
