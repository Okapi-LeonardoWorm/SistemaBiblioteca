from datetime import datetime
from uuid import uuid4

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from app import db
from app.models import BackupRun, BackupSchedule, BackupUpload, Configuration, OAuthCredential
from app.services import (
    build_google_oauth_authorize_url,
    calculate_next_run_at,
    create_local_backup_now,
    disconnect_google_oauth,
    exchange_google_oauth_code,
    process_pending_drive_uploads_once,
    upsert_backup_config_value,
)
from app.utils import can_edit_backup_screen, can_view_backup_screen

bp = Blueprint('backups', __name__)


def _get_config_value(key: str, default: str = '') -> str:
    row = Configuration.query.filter_by(key=key).first()
    if not row or row.value is None:
        return default
    return str(row.value)


def _parse_enabled(raw_value: str | None) -> bool:
    return str(raw_value or '').strip() in {'1', 'true', 'True', 'on', 'yes', 'sim'}


def _normalize_week_days(raw_value: str) -> str:
    parts = [item.strip() for item in (raw_value or '').split(',') if item.strip()]
    normalized = []
    for part in parts:
        try:
            day = int(part)
        except (TypeError, ValueError):
            continue
        if 0 <= day <= 6 and str(day) not in normalized:
            normalized.append(str(day))
    return ','.join(normalized)


@bp.route('/backups')
@login_required
def backup_management():
    if not can_view_backup_screen():
        flash('Acesso negado para gestão de backups.', 'warning')
        return redirect(url_for('navigation.menu'))

    schedules = BackupSchedule.query.order_by(BackupSchedule.enabled.desc(), BackupSchedule.name.asc()).all()
    runs = BackupRun.query.order_by(BackupRun.runId.desc()).limit(30).all()

    uploads_by_run = {}
    if runs:
        run_ids = [item.runId for item in runs]
        uploads = BackupUpload.query.filter(BackupUpload.runId.in_(run_ids)).all()
        uploads_by_run = {row.runId: row for row in uploads}

    google_connected = OAuthCredential.query.filter_by(provider='google_drive').first()
    google_is_connected = bool(google_connected and google_connected.accessToken)
    google_client_id = _get_config_value('BACKUP_GOOGLE_OAUTH_CLIENT_ID', '')
    google_client_secret = _get_config_value('BACKUP_GOOGLE_OAUTH_CLIENT_SECRET', '')
    google_redirect_uri = _get_config_value('BACKUP_GOOGLE_OAUTH_REDIRECT_URI', '')
    google_folder_id = _get_config_value('BACKUP_GOOGLE_DRIVE_FOLDER_ID', '')
    google_folder_name = _get_config_value('BACKUP_GOOGLE_DRIVE_FOLDER_NAME', 'Backups_Sistema_Biblioteca')
    google_auto_create_folder = _get_config_value('BACKUP_GOOGLE_DRIVE_AUTO_CREATE_FOLDER', '1')
    google_scopes = _get_config_value('BACKUP_GOOGLE_OAUTH_SCOPES', 'https://www.googleapis.com/auth/drive.file')
    google_ready_to_connect = bool(google_client_id and google_client_secret)

    return render_template(
        'backups.html',
        schedules=schedules,
        runs=runs,
        uploads_by_run=uploads_by_run,
        can_edit=can_edit_backup_screen(),
        google_is_connected=google_is_connected,
        google_client_id=google_client_id,
        google_client_secret=google_client_secret,
        google_redirect_uri=google_redirect_uri,
        google_folder_id=google_folder_id,
        google_folder_name=google_folder_name,
        google_auto_create_folder=google_auto_create_folder,
        google_scopes=google_scopes,
        google_ready_to_connect=google_ready_to_connect,
    )


@bp.route('/backups/run-now', methods=['POST'])
@login_required
def run_backup_now():
    if not can_edit_backup_screen():
        flash('Acesso negado para executar backup.', 'danger')
        return redirect(url_for('backups.backup_management'))

    try:
        create_local_backup_now(requested_by=current_user.userId)
        flash('Backup local criado com sucesso e pendência de upload registrada.', 'success')
    except Exception as exc:
        flash(f'Falha ao executar backup: {exc}', 'danger')

    return redirect(url_for('backups.backup_management'))


@bp.route('/backups/schedules/new', methods=['POST'])
@login_required
def create_schedule():
    if not can_edit_backup_screen():
        flash('Acesso negado para editar agendamentos.', 'danger')
        return redirect(url_for('backups.backup_management'))

    name = (request.form.get('name') or '').strip()
    frequency = (request.form.get('frequency') or '').strip().lower()
    run_time = (request.form.get('runTime') or '').strip()
    week_days = _normalize_week_days(request.form.get('weekDays') or '')
    timezone = (request.form.get('timezone') or 'America/Sao_Paulo').strip() or 'America/Sao_Paulo'
    enabled = _parse_enabled(request.form.get('enabled'))

    if not name:
        flash('Informe o nome do agendamento.', 'warning')
        return redirect(url_for('backups.backup_management'))

    if frequency not in {'daily', 'weekly'}:
        flash('Tipo de frequência inválido.', 'warning')
        return redirect(url_for('backups.backup_management'))

    try:
        datetime.strptime(run_time, '%H:%M')
    except ValueError:
        flash('Horário inválido. Use o formato HH:MM.', 'warning')
        return redirect(url_for('backups.backup_management'))

    if frequency == 'weekly' and not week_days:
        flash('No agendamento semanal, informe ao menos um dia da semana (0-6).', 'warning')
        return redirect(url_for('backups.backup_management'))

    schedule = BackupSchedule(
        name=name,
        frequency=frequency,
        runTime=run_time,
        weekDays=week_days if frequency == 'weekly' else None,
        timezone=timezone,
        enabled=enabled,
        nextRunAt=None,
        creationDate=datetime.now(),
        lastUpdate=datetime.now(),
        createdBy=current_user.userId,
        updatedBy=current_user.userId,
    )
    schedule.nextRunAt = calculate_next_run_at(schedule)

    db.session.add(schedule)
    db.session.commit()

    flash('Agendamento de backup criado com sucesso.', 'success')
    return redirect(url_for('backups.backup_management'))


@bp.route('/backups/schedules/<int:schedule_id>/update', methods=['POST'])
@login_required
def update_schedule(schedule_id):
    if not can_edit_backup_screen():
        flash('Acesso negado para editar agendamentos.', 'danger')
        return redirect(url_for('backups.backup_management'))

    schedule = db.session.get(BackupSchedule, schedule_id)
    if not schedule:
        flash('Agendamento não encontrado.', 'warning')
        return redirect(url_for('backups.backup_management'))

    name = (request.form.get('name') or '').strip()
    frequency = (request.form.get('frequency') or '').strip().lower()
    run_time = (request.form.get('runTime') or '').strip()
    week_days = _normalize_week_days(request.form.get('weekDays') or '')
    timezone = (request.form.get('timezone') or 'America/Sao_Paulo').strip() or 'America/Sao_Paulo'
    enabled = _parse_enabled(request.form.get('enabled'))

    if not name:
        flash('Informe o nome do agendamento.', 'warning')
        return redirect(url_for('backups.backup_management'))

    if frequency not in {'daily', 'weekly'}:
        flash('Tipo de frequência inválido.', 'warning')
        return redirect(url_for('backups.backup_management'))

    try:
        datetime.strptime(run_time, '%H:%M')
    except ValueError:
        flash('Horário inválido. Use o formato HH:MM.', 'warning')
        return redirect(url_for('backups.backup_management'))

    if frequency == 'weekly' and not week_days:
        flash('No agendamento semanal, informe ao menos um dia da semana (0-6).', 'warning')
        return redirect(url_for('backups.backup_management'))

    schedule.name = name
    schedule.frequency = frequency
    schedule.runTime = run_time
    schedule.weekDays = week_days if frequency == 'weekly' else None
    schedule.timezone = timezone
    schedule.enabled = enabled
    schedule.nextRunAt = calculate_next_run_at(schedule)
    schedule.lastUpdate = datetime.now()
    schedule.updatedBy = current_user.userId

    db.session.commit()
    flash('Agendamento atualizado com sucesso.', 'success')
    return redirect(url_for('backups.backup_management'))


@bp.route('/backups/schedules/<int:schedule_id>/toggle', methods=['POST'])
@login_required
def toggle_schedule(schedule_id):
    if not can_edit_backup_screen():
        flash('Acesso negado para editar agendamentos.', 'danger')
        return redirect(url_for('backups.backup_management'))

    schedule = db.session.get(BackupSchedule, schedule_id)
    if not schedule:
        flash('Agendamento não encontrado.', 'warning')
        return redirect(url_for('backups.backup_management'))

    schedule.enabled = not bool(schedule.enabled)
    schedule.nextRunAt = calculate_next_run_at(schedule) if schedule.enabled else None
    schedule.lastUpdate = datetime.now()
    schedule.updatedBy = current_user.userId
    db.session.commit()

    flash('Agendamento atualizado.', 'success')
    return redirect(url_for('backups.backup_management'))


@bp.route('/backups/schedules/<int:schedule_id>/delete', methods=['POST'])
@login_required
def delete_schedule(schedule_id):
    if not can_edit_backup_screen():
        flash('Acesso negado para excluir agendamentos.', 'danger')
        return redirect(url_for('backups.backup_management'))

    schedule = db.session.get(BackupSchedule, schedule_id)
    if not schedule:
        flash('Agendamento não encontrado.', 'warning')
        return redirect(url_for('backups.backup_management'))

    db.session.delete(schedule)
    db.session.commit()
    flash('Agendamento removido com sucesso.', 'success')
    return redirect(url_for('backups.backup_management'))


@bp.route('/backups/uploads/process-now', methods=['POST'])
@login_required
def process_uploads_now():
    if not can_edit_backup_screen():
        flash('Acesso negado para processar uploads.', 'danger')
        return redirect(url_for('backups.backup_management'))

    try:
        uploaded = process_pending_drive_uploads_once(limit=20)
        flash(f'Processamento concluído. Uploads realizados: {uploaded}.', 'success')
    except Exception as exc:
        flash(f'Falha ao processar uploads: {exc}', 'danger')

    return redirect(url_for('backups.backup_management'))


@bp.route('/backups/google/connect', methods=['POST'])
@login_required
def google_connect():
    if not can_edit_backup_screen():
        flash('Acesso negado para conectar Google Drive.', 'danger')
        return redirect(url_for('backups.backup_management'))

    callback_url = url_for('backups.google_callback', _external=True)
    state_value = str(uuid4())
    session['backup_google_oauth_state'] = state_value

    try:
        authorize_url = build_google_oauth_authorize_url(state_value=state_value, redirect_uri=callback_url)
    except Exception as exc:
        flash(
            f'Falha ao iniciar OAuth2: {exc}. '
            'Verifique BACKUP_GOOGLE_OAUTH_CLIENT_ID, BACKUP_GOOGLE_OAUTH_CLIENT_SECRET e BACKUP_GOOGLE_OAUTH_REDIRECT_URI.',
            'danger',
        )
        return redirect(url_for('backups.backup_management'))

    return redirect(authorize_url)


@bp.route('/callback', methods=['GET'])
@bp.route('/backups/google/callback', methods=['GET'])
@login_required
def google_callback():
    if not can_edit_backup_screen():
        flash('Acesso negado para concluir OAuth2.', 'danger')
        return redirect(url_for('backups.backup_management'))

    expected_state = session.get('backup_google_oauth_state')
    received_state = (request.args.get('state') or '').strip()
    if not expected_state or expected_state != received_state:
        flash('Estado OAuth2 inválido.', 'danger')
        return redirect(url_for('backups.backup_management'))

    if request.args.get('error'):
        flash(f'Autorização Google negada: {request.args.get("error")}', 'warning')
        return redirect(url_for('backups.backup_management'))

    code = (request.args.get('code') or '').strip()
    if not code:
        flash('Código OAuth2 não recebido.', 'danger')
        return redirect(url_for('backups.backup_management'))

    callback_url = url_for('backups.google_callback', _external=True)

    try:
        exchange_google_oauth_code(code=code, redirect_uri=callback_url, actor_user_id=current_user.userId)
        flash('Google Drive conectado com sucesso.', 'success')
    except Exception as exc:
        flash(f'Falha ao concluir OAuth2: {exc}', 'danger')

    session.pop('backup_google_oauth_state', None)
    return redirect(url_for('backups.backup_management'))


@bp.route('/backups/google/disconnect', methods=['POST'])
@login_required
def google_disconnect():
    if not can_edit_backup_screen():
        flash('Acesso negado para desconectar Google Drive.', 'danger')
        return redirect(url_for('backups.backup_management'))

    disconnect_google_oauth(actor_user_id=current_user.userId)
    flash('Google Drive desconectado.', 'success')
    return redirect(url_for('backups.backup_management'))


@bp.route('/backups/google/credentials', methods=['POST'])
@login_required
def save_google_credentials():
    if not can_edit_backup_screen():
        flash('Acesso negado para configurar credenciais Google.', 'danger')
        return redirect(url_for('backups.backup_management'))

    client_id = (request.form.get('client_id') or '').strip()
    client_secret = (request.form.get('client_secret') or '').strip()
    redirect_uri = (request.form.get('redirect_uri') or '').strip()
    folder_id = (request.form.get('folder_id') or '').strip()
    scopes = (request.form.get('scopes') or '').strip() or 'https://www.googleapis.com/auth/drive.file'

    if not client_id:
        flash('Informe o Client ID do OAuth2 do Google.', 'warning')
        return redirect(url_for('backups.backup_management'))

    if not client_secret:
        flash('Informe o Client Secret do OAuth2 do Google.', 'warning')
        return redirect(url_for('backups.backup_management'))

    upsert_backup_config_value(
        'BACKUP_GOOGLE_OAUTH_CLIENT_ID',
        client_id,
        'Client ID OAuth2 da aplicação Google para envio de backups ao Drive.',
        current_user.userId,
    )
    upsert_backup_config_value(
        'BACKUP_GOOGLE_OAUTH_CLIENT_SECRET',
        client_secret,
        'Client Secret OAuth2 da aplicação Google para envio de backups ao Drive.',
        current_user.userId,
    )
    upsert_backup_config_value(
        'BACKUP_GOOGLE_OAUTH_REDIRECT_URI',
        redirect_uri,
        'URL de callback OAuth2 da aplicação para retorno da autorização Google.',
        current_user.userId,
    )
    upsert_backup_config_value(
        'BACKUP_GOOGLE_DRIVE_FOLDER_ID',
        folder_id,
        'ID da pasta do Google Drive que receberá os backups.',
        current_user.userId,
    )
    upsert_backup_config_value(
        'BACKUP_GOOGLE_OAUTH_SCOPES',
        scopes,
        'Escopos OAuth2 utilizados na integração de backup com Google Drive.',
        current_user.userId,
    )

    flash('Credenciais Google salvas com sucesso. Agora clique em Conectar Google.', 'success')
    return redirect(url_for('backups.backup_management'))
