"""add dashboard loan indexes

Revision ID: 5d3a2f1b9c4e
Revises: 2b7e9c4f1a21
Create Date: 2026-04-01 11:10:00.000000

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = '5d3a2f1b9c4e'
down_revision = '2b7e9c4f1a21'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_loans_status', 'loans', ['status'], unique=False)
    op.create_index('ix_loans_returnDate', 'loans', ['returnDate'], unique=False)
    op.create_index('ix_loans_loanDate', 'loans', ['loanDate'], unique=False)
    op.create_index('ix_loans_userId', 'loans', ['userId'], unique=False)
    op.create_index('ix_loans_status_returnDate', 'loans', ['status', 'returnDate'], unique=False)
    op.create_index('ix_loans_userId_status_loanDate', 'loans', ['userId', 'status', 'loanDate'], unique=False)


def downgrade():
    op.drop_index('ix_loans_userId_status_loanDate', table_name='loans')
    op.drop_index('ix_loans_status_returnDate', table_name='loans')
    op.drop_index('ix_loans_userId', table_name='loans')
    op.drop_index('ix_loans_loanDate', table_name='loans')
    op.drop_index('ix_loans_returnDate', table_name='loans')
    op.drop_index('ix_loans_status', table_name='loans')
