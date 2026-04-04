"""add_backup_domain_tables

Revision ID: 1f9b7a2c6d3e
Revises: 7c9e2d1f4a6b
Create Date: 2026-04-03 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1f9b7a2c6d3e'
down_revision = '7c9e2d1f4a6b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'backup_schedules',
        sa.Column('scheduleId', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('frequency', sa.String(length=20), nullable=False),
        sa.Column('runTime', sa.String(length=5), nullable=False),
        sa.Column('weekDays', sa.String(length=20), nullable=True),
        sa.Column('timezone', sa.String(length=64), nullable=False, server_default='America/Sao_Paulo'),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('nextRunAt', sa.DateTime(), nullable=True),
        sa.Column('creationDate', sa.DateTime(), nullable=False),
        sa.Column('lastUpdate', sa.DateTime(), nullable=False),
        sa.Column('createdBy', sa.Integer(), nullable=False),
        sa.Column('updatedBy', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['createdBy'], ['users.userId']),
        sa.ForeignKeyConstraint(['updatedBy'], ['users.userId']),
        sa.PrimaryKeyConstraint('scheduleId'),
    )

    op.create_index('ix_backup_schedules_enabled_next', 'backup_schedules', ['enabled', 'nextRunAt'])

    op.create_table(
        'backup_runs',
        sa.Column('runId', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('scheduleId', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='queued'),
        sa.Column('fileName', sa.String(length=255), nullable=True),
        sa.Column('localPath', sa.Text(), nullable=True),
        sa.Column('fileHash', sa.String(length=64), nullable=True),
        sa.Column('fileSizeBytes', sa.BigInteger(), nullable=True),
        sa.Column('startedAt', sa.DateTime(), nullable=True),
        sa.Column('finishedAt', sa.DateTime(), nullable=True),
        sa.Column('errorMessage', sa.Text(), nullable=True),
        sa.Column('creationDate', sa.DateTime(), nullable=False),
        sa.Column('lastUpdate', sa.DateTime(), nullable=False),
        sa.Column('createdBy', sa.Integer(), nullable=True),
        sa.Column('updatedBy', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['createdBy'], ['users.userId']),
        sa.ForeignKeyConstraint(['updatedBy'], ['users.userId']),
        sa.ForeignKeyConstraint(['scheduleId'], ['backup_schedules.scheduleId']),
        sa.PrimaryKeyConstraint('runId'),
    )

    op.create_index('ix_backup_runs_status_started', 'backup_runs', ['status', 'startedAt'])

    op.create_table(
        'backup_uploads',
        sa.Column('uploadId', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('runId', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=30), nullable=False, server_default='google_drive'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('retryCount', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('nextRetryAt', sa.DateTime(), nullable=True),
        sa.Column('uploadedAt', sa.DateTime(), nullable=True),
        sa.Column('remoteFileId', sa.String(length=255), nullable=True),
        sa.Column('lastError', sa.Text(), nullable=True),
        sa.Column('creationDate', sa.DateTime(), nullable=False),
        sa.Column('lastUpdate', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['runId'], ['backup_runs.runId']),
        sa.PrimaryKeyConstraint('uploadId'),
        sa.UniqueConstraint('runId', name='uq_backup_uploads_run_id'),
    )

    op.create_index('ix_backup_uploads_status_nextretry', 'backup_uploads', ['status', 'nextRetryAt'])

    op.create_table(
        'oauth_credentials',
        sa.Column('credentialId', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('accessToken', sa.Text(), nullable=True),
        sa.Column('refreshToken', sa.Text(), nullable=True),
        sa.Column('tokenType', sa.String(length=30), nullable=True),
        sa.Column('scope', sa.Text(), nullable=True),
        sa.Column('expiresAt', sa.DateTime(), nullable=True),
        sa.Column('isEncrypted', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('creationDate', sa.DateTime(), nullable=False),
        sa.Column('lastUpdate', sa.DateTime(), nullable=False),
        sa.Column('createdBy', sa.Integer(), nullable=True),
        sa.Column('updatedBy', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['createdBy'], ['users.userId']),
        sa.ForeignKeyConstraint(['updatedBy'], ['users.userId']),
        sa.PrimaryKeyConstraint('credentialId'),
        sa.UniqueConstraint('provider', name='uq_oauth_credentials_provider'),
    )


def downgrade():
    op.drop_table('oauth_credentials')
    op.drop_index('ix_backup_uploads_status_nextretry', table_name='backup_uploads')
    op.drop_table('backup_uploads')
    op.drop_index('ix_backup_runs_status_started', table_name='backup_runs')
    op.drop_table('backup_runs')
    op.drop_index('ix_backup_schedules_enabled_next', table_name='backup_schedules')
    op.drop_table('backup_schedules')
