"""Add config specs table

Revision ID: c2f0c9a7f4b1
Revises: a80a1b057f18
Create Date: 2026-02-18 20:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2f0c9a7f4b1'
down_revision = 'a80a1b057f18'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'config_specs',
        sa.Column('configSpecId', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('key', sa.String(length=100), nullable=False),
        sa.Column('valueType', sa.String(length=20), nullable=False),
        sa.Column('allowedValues', sa.Text(), nullable=True),
        sa.Column('minValue', sa.Integer(), nullable=True),
        sa.Column('maxValue', sa.Integer(), nullable=True),
        sa.Column('required', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('defaultValue', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('creationDate', sa.DateTime(), nullable=False),
        sa.Column('lastUpdate', sa.DateTime(), nullable=False),
        sa.Column('createdBy', sa.Integer(), nullable=False),
        sa.Column('updatedBy', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['createdBy'], ['users.userId']),
        sa.ForeignKeyConstraint(['updatedBy'], ['users.userId']),
        sa.PrimaryKeyConstraint('configSpecId'),
        sa.UniqueConstraint('key', name='uq_config_specs_key')
    )


def downgrade():
    op.drop_table('config_specs')
