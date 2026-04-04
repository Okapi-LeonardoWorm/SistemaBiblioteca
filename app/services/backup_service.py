import hashlib
import json
import os
import shutil
import subprocess
import zipfile
from datetime import datetime, timedelta
from urllib.parse import urlencode
from zoneinfo import ZoneInfo

import requests
from flask import current_app
from sqlalchemy.engine.url import make_url

from app import db
from app.models import BackupRun, BackupSchedule, BackupUpload, Configuration, OAuthCredential
from app.utils.crypto_utils import decrypt_secret, encrypt_secret


BACKUP_FILE_PREFIX = 'BkpBiblioteca'
GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_DRIVE_UPLOAD_URL = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart'


class PgDumpCommandNotFoundError(RuntimeError):
    pass


def _requests_verify_bundle():
    try:
        import certifi
        return certifi.where()
    except Exception:
        return True


def _now():
    return datetime.now()


def _get_config_value(key: str, default: str | None = None) -> str | None:
    entry = Configuration.query.filter_by(key=key).first()
    if not entry or entry.value is None:
        return default
    return str(entry.value)


def _get_config_bool(key: str, default: bool = False) -> bool:
    raw = (_get_config_value(key, '1' if default else '0') or '').strip().lower()
    return raw in {'1', 'true', 'yes', 'sim', 'on'}


def _get_backup_directory() -> str:
    configured = (_get_config_value('BACKUP_LOCAL_DIRECTORY', '') or '').strip()
    if configured:
        return configured
    return os.path.join(current_app.instance_path, 'backups')


def _ensure_directory(path: str):
    os.makedirs(path, exist_ok=True)


def _build_backup_filename(extension: str = 'zip') -> str:
    timestamp = _now().strftime('%d-%m-%Y_%H-%M-%S')
    return f'{BACKUP_FILE_PREFIX}_{timestamp}.{extension}'


def _compute_file_sha256(file_path: str) -> str:
    digest = hashlib.sha256()
    with open(file_path, 'rb') as file_obj:
        for chunk in iter(lambda: file_obj.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _resolve_pg_dump_command() -> str:
    configured = (_get_config_value('BACKUP_PG_DUMP_COMMAND', '') or '').strip()
    if configured:
        return configured

    # Primeiro tenta resolver via PATH.
    from_path = shutil.which('pg_dump')
    if from_path:
        return from_path

    # Fallback para caminhos comuns no Windows (instalação padrão PostgreSQL).
    candidate_paths = []
    for base in (os.environ.get('ProgramFiles'), os.environ.get('ProgramFiles(x86)')):
        if not base:
            continue
        postgres_root = os.path.join(base, 'PostgreSQL')
        if not os.path.isdir(postgres_root):
            continue

        try:
            versions = sorted(os.listdir(postgres_root), reverse=True)
        except OSError:
            versions = []

        for version in versions:
            candidate_paths.append(os.path.join(postgres_root, version, 'bin', 'pg_dump.exe'))

    for candidate in candidate_paths:
        if os.path.isfile(candidate):
            return candidate

    return 'pg_dump'


def _get_dump_strategy() -> str:
    raw = (_get_config_value('BACKUP_DUMP_STRATEGY', 'auto') or 'auto').strip().lower()
    if raw in {'local', 'local_cli'}:
        return 'local_cli'
    if raw in {'docker', 'docker_exec'}:
        return 'docker_exec'
    return 'auto'


def _get_docker_binary() -> str:
    return (_get_config_value('BACKUP_DOCKER_BINARY', 'docker') or 'docker').strip()


def _get_docker_container_name() -> str:
    return (_get_config_value('BACKUP_DOCKER_CONTAINER_NAME', 'sistema_biblioteca_postgres') or 'sistema_biblioteca_postgres').strip()


def _get_docker_temp_dir() -> str:
    return (_get_config_value('BACKUP_DOCKER_TEMP_DIR', '/tmp') or '/tmp').strip().rstrip('/')


def _run_pg_dump_custom_local(output_file: str):
    database_url = current_app.config.get('SQLALCHEMY_DATABASE_URI')
    if not database_url:
        raise RuntimeError('SQLALCHEMY_DATABASE_URI não configurado.')

    url = make_url(database_url)
    command = [_resolve_pg_dump_command(), '--format=custom', f'--file={output_file}']

    if url.host:
        command.append(f'--host={url.host}')
    if url.port:
        command.append(f'--port={url.port}')
    if url.username:
        command.append(f'--username={url.username}')
    if url.database:
        command.append(url.database)

    env = os.environ.copy()
    if url.password:
        env['PGPASSWORD'] = str(url.password)

    try:
        result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=600, check=False)
    except FileNotFoundError as exc:
        raise PgDumpCommandNotFoundError(
            'Comando pg_dump não encontrado no sistema. '
            'Instale o PostgreSQL client tools ou configure BACKUP_PG_DUMP_COMMAND com o caminho completo '
            '(ex.: C:/Program Files/PostgreSQL/16/bin/pg_dump.exe).'
        ) from exc
    except Exception as exc:
        raise RuntimeError(f'Falha ao executar pg_dump: {exc}') from exc

    if result.returncode != 0:
        stderr = (result.stderr or '').strip()
        raise RuntimeError(f'pg_dump retornou erro: {stderr or "sem detalhes"}')


def _run_docker_command(command: list[str], timeout: int = 600):
    result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=False)
    if result.returncode != 0:
        stderr = (result.stderr or '').strip()
        raise RuntimeError(f'Erro ao executar comando docker: {stderr or "sem detalhes"}')


def _run_pg_dump_custom_docker(output_file: str):
    database_url = current_app.config.get('SQLALCHEMY_DATABASE_URI')
    if not database_url:
        raise RuntimeError('SQLALCHEMY_DATABASE_URI não configurado.')

    url = make_url(database_url)
    docker_bin = _get_docker_binary()
    container_name = _get_docker_container_name()
    temp_dir = _get_docker_temp_dir()
    remote_file_name = os.path.basename(output_file)
    remote_path = f'{temp_dir}/{remote_file_name}'

    command = [docker_bin, 'exec']
    if url.password:
        command.extend(['-e', f'PGPASSWORD={url.password}'])
    command.extend([
        container_name,
        'pg_dump',
        '--format=custom',
        f'--file={remote_path}',
    ])
    if url.username:
        command.append(f'--username={url.username}')
    if url.database:
        command.append(url.database)

    try:
        _run_docker_command(command)
        _run_docker_command([docker_bin, 'cp', f'{container_name}:{remote_path}', output_file])
    finally:
        try:
            _run_docker_command([docker_bin, 'exec', container_name, 'rm', '-f', remote_path], timeout=120)
        except Exception:
            pass


def _run_pg_dump_custom(output_file: str):
    strategy = _get_dump_strategy()

    if strategy == 'local_cli':
        _run_pg_dump_custom_local(output_file)
        return

    if strategy == 'docker_exec':
        _run_pg_dump_custom_docker(output_file)
        return

    try:
        _run_pg_dump_custom_local(output_file)
    except PgDumpCommandNotFoundError:
        _run_pg_dump_custom_docker(output_file)


def _zip_single_file(source_file: str, zip_file: str):
    with zipfile.ZipFile(zip_file, mode='w', compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(source_file, arcname=os.path.basename(source_file))


def create_local_backup_now(schedule_id: int | None = None, requested_by: int | None = None) -> BackupRun:
    run = BackupRun(
        scheduleId=schedule_id,
        status='running',
        startedAt=_now(),
        creationDate=_now(),
        lastUpdate=_now(),
        createdBy=requested_by,
        updatedBy=requested_by,
    )
    db.session.add(run)
    db.session.commit()

    backup_dir = _get_backup_directory()
    _ensure_directory(backup_dir)

    dump_file_name = _build_backup_filename('dump')
    dump_path = os.path.join(backup_dir, dump_file_name)
    zip_file_name = _build_backup_filename('zip')
    zip_path = os.path.join(backup_dir, zip_file_name)

    try:
        _run_pg_dump_custom(dump_path)
        _zip_single_file(dump_path, zip_path)

        file_size = os.path.getsize(zip_path)
        file_hash = _compute_file_sha256(zip_path)

        run.status = 'success'
        run.fileName = zip_file_name
        run.localPath = zip_path
        run.fileHash = file_hash
        run.fileSizeBytes = file_size
        run.finishedAt = _now()
        run.lastUpdate = _now()
        run.updatedBy = requested_by

        upload = BackupUpload(
            runId=run.runId,
            provider='google_drive',
            status='pending',
            retryCount=0,
            nextRetryAt=_now(),
            creationDate=_now(),
            lastUpdate=_now(),
        )
        db.session.add(upload)
        db.session.commit()

    except Exception as exc:
        run.status = 'failed'
        run.errorMessage = str(exc)
        run.finishedAt = _now()
        run.lastUpdate = _now()
        run.updatedBy = requested_by
        db.session.commit()
        raise

    finally:
        if os.path.exists(dump_path):
            try:
                os.remove(dump_path)
            except OSError:
                pass

    return run


def _get_retention_days(default: int = 30) -> int:
    raw = _get_config_value('BACKUP_RETENTION_DAYS', str(default))
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = default
    return max(1, value)


def cleanup_expired_local_backups() -> int:
    retention_days = _get_retention_days()
    threshold = _now() - timedelta(days=retention_days)

    candidates = (
        BackupRun.query
        .filter(BackupRun.status == 'success', BackupRun.finishedAt.isnot(None), BackupRun.finishedAt < threshold)
        .all()
    )

    removed = 0
    for run in candidates:
        local_path = (run.localPath or '').strip()
        if not local_path:
            continue
        if not os.path.isfile(local_path):
            continue
        try:
            os.remove(local_path)
            removed += 1
        except OSError:
            continue

    return removed


def has_pending_drive_uploads() -> bool:
    return db.session.query(BackupUpload.uploadId).filter(BackupUpload.status.in_(['pending', 'failed'])).first() is not None


def next_retry_delay_minutes(retry_count: int) -> int:
    base_minutes_raw = _get_config_value('BACKUP_RETRY_BASE_MINUTES', '10')
    max_minutes_raw = _get_config_value('BACKUP_RETRY_MAX_MINUTES', '1440')

    try:
        base_minutes = max(1, int(base_minutes_raw))
    except (TypeError, ValueError):
        base_minutes = 10

    try:
        max_minutes = max(base_minutes, int(max_minutes_raw))
    except (TypeError, ValueError):
        max_minutes = 1440

    delay = base_minutes * (2 ** max(0, retry_count))
    return min(delay, max_minutes)


def _get_schedule_timezone(schedule: BackupSchedule) -> ZoneInfo:
    tz_name = (schedule.timezone or 'America/Sao_Paulo').strip()
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return ZoneInfo('America/Sao_Paulo')


def _parse_run_time(run_time: str) -> tuple[int, int]:
    hour, minute = str(run_time).split(':', 1)
    return int(hour), int(minute)


def _parse_week_days(raw_value: str | None) -> list[int]:
    week_days = []
    for item in (raw_value or '').split(','):
        value = item.strip()
        if not value:
            continue
        try:
            day = int(value)
        except (TypeError, ValueError):
            continue
        if 0 <= day <= 6 and day not in week_days:
            week_days.append(day)
    return sorted(week_days)


def calculate_next_run_at(schedule: BackupSchedule, reference_dt: datetime | None = None) -> datetime | None:
    if not schedule.enabled:
        return None

    tz = _get_schedule_timezone(schedule)
    now_local = (reference_dt or datetime.now()).astimezone(tz)

    try:
        hour, minute = _parse_run_time(schedule.runTime)
    except Exception:
        return None

    if schedule.frequency == 'daily':
        candidate = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now_local:
            candidate = candidate + timedelta(days=1)
        return candidate.replace(tzinfo=None)

    if schedule.frequency == 'weekly':
        week_days = _parse_week_days(schedule.weekDays)
        if not week_days:
            return None

        for delta in range(0, 8):
            base_day = now_local + timedelta(days=delta)
            candidate = base_day.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if candidate.weekday() not in week_days:
                continue
            if candidate <= now_local:
                continue
            return candidate.replace(tzinfo=None)

    return None


def process_due_schedules_once(now_value: datetime | None = None) -> int:
    now_dt = now_value or datetime.now()

    schedules = BackupSchedule.query.filter_by(enabled=True).all()
    for schedule in schedules:
        if schedule.nextRunAt is None:
            schedule.nextRunAt = calculate_next_run_at(schedule, reference_dt=now_dt)
            schedule.lastUpdate = now_dt
    db.session.commit()

    due_schedules = (
        BackupSchedule.query
        .filter(
            BackupSchedule.enabled.is_(True),
            BackupSchedule.nextRunAt.isnot(None),
            BackupSchedule.nextRunAt <= now_dt,
        )
        .order_by(BackupSchedule.nextRunAt.asc())
        .all()
    )

    executed = 0
    for schedule in due_schedules:
        create_local_backup_now(schedule_id=schedule.scheduleId, requested_by=schedule.updatedBy)
        schedule.nextRunAt = calculate_next_run_at(schedule, reference_dt=now_dt + timedelta(seconds=1))
        schedule.lastUpdate = datetime.now()
        db.session.commit()
        executed += 1

    return executed


def _get_google_client_id() -> str:
    return (_get_config_value('BACKUP_GOOGLE_OAUTH_CLIENT_ID', '') or '').strip()


def _get_google_client_secret() -> str:
    return (_get_config_value('BACKUP_GOOGLE_OAUTH_CLIENT_SECRET', '') or '').strip()


def _get_google_redirect_uri(default_value: str = '') -> str:
    configured = (_get_config_value('BACKUP_GOOGLE_OAUTH_REDIRECT_URI', None) or '').strip()
    if configured:
        return configured
    return (default_value or '').strip()


def _get_google_scopes() -> str:
    configured = (_get_config_value('BACKUP_GOOGLE_OAUTH_SCOPES', '') or '').strip()
    if configured:
        return configured
    return 'https://www.googleapis.com/auth/drive.file'


def build_google_oauth_authorize_url(state_value: str, redirect_uri: str) -> str:
    client_id = _get_google_client_id()
    if not client_id:
        raise RuntimeError('BACKUP_GOOGLE_OAUTH_CLIENT_ID não configurado.')

    resolved_redirect_uri = _get_google_redirect_uri(redirect_uri)
    if not resolved_redirect_uri:
        raise RuntimeError('BACKUP_GOOGLE_OAUTH_REDIRECT_URI não configurado e callback automático indisponível.')

    params = {
        'client_id': client_id,
        'redirect_uri': resolved_redirect_uri,
        'response_type': 'code',
        'scope': _get_google_scopes(),
        'access_type': 'offline',
        'prompt': 'consent',
        'include_granted_scopes': 'true',
        'state': state_value,
    }
    return f'{GOOGLE_AUTH_URL}?{urlencode(params)}'


def _get_or_create_google_credential(actor_user_id: int | None = None) -> OAuthCredential:
    credential = OAuthCredential.query.filter_by(provider='google_drive').first()
    if credential:
        return credential

    now_dt = datetime.now()
    credential = OAuthCredential(
        provider='google_drive',
        creationDate=now_dt,
        lastUpdate=now_dt,
        createdBy=actor_user_id,
        updatedBy=actor_user_id,
        isEncrypted=True,
    )
    db.session.add(credential)
    db.session.flush()
    return credential


def exchange_google_oauth_code(code: str, redirect_uri: str, actor_user_id: int | None = None):
    client_id = _get_google_client_id()
    client_secret = _get_google_client_secret()
    resolved_redirect_uri = _get_google_redirect_uri(redirect_uri)
    if not client_id or not client_secret or not resolved_redirect_uri:
        raise RuntimeError('Configurações OAuth2 do Google incompletas (client_id/client_secret/redirect_uri).')

    payload = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': resolved_redirect_uri,
        'grant_type': 'authorization_code',
    }

    response = requests.post(GOOGLE_TOKEN_URL, data=payload, timeout=30, verify=_requests_verify_bundle())
    if response.status_code >= 400:
        raise RuntimeError(f'Falha no token endpoint Google: {response.text}')

    data = response.json()
    access_token = data.get('access_token')
    refresh_token = data.get('refresh_token')
    token_type = data.get('token_type')
    scope = data.get('scope')
    expires_in = data.get('expires_in')

    if not access_token:
        raise RuntimeError('OAuth2 sem access_token na resposta do Google.')

    credential = _get_or_create_google_credential(actor_user_id=actor_user_id)
    credential.accessToken = encrypt_secret(access_token)
    if refresh_token:
        credential.refreshToken = encrypt_secret(refresh_token)
    credential.tokenType = token_type
    credential.scope = scope
    credential.isEncrypted = True
    credential.expiresAt = datetime.now() + timedelta(seconds=int(expires_in or 0))
    credential.lastUpdate = datetime.now()
    credential.updatedBy = actor_user_id
    db.session.commit()

    return credential


def disconnect_google_oauth(actor_user_id: int | None = None):
    credential = OAuthCredential.query.filter_by(provider='google_drive').first()
    if not credential:
        return
    credential.accessToken = None
    credential.refreshToken = None
    credential.tokenType = None
    credential.scope = None
    credential.expiresAt = None
    credential.lastUpdate = datetime.now()
    credential.updatedBy = actor_user_id
    db.session.commit()


def _get_google_access_token(credential: OAuthCredential) -> str:
    access_token = decrypt_secret(credential.accessToken) if credential.accessToken else ''
    if not access_token:
        raise RuntimeError('Token de acesso Google não configurado.')

    expiry = credential.expiresAt
    if expiry and expiry > datetime.now() + timedelta(seconds=45):
        return access_token

    refresh_token = decrypt_secret(credential.refreshToken) if credential.refreshToken else ''
    if not refresh_token:
        return access_token

    payload = {
        'client_id': _get_google_client_id(),
        'client_secret': _get_google_client_secret(),
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
    }
    response = requests.post(GOOGLE_TOKEN_URL, data=payload, timeout=30, verify=_requests_verify_bundle())
    if response.status_code >= 400:
        raise RuntimeError(f'Falha ao renovar token Google: {response.text}')

    data = response.json()
    new_access_token = data.get('access_token')
    if not new_access_token:
        raise RuntimeError('Refresh token não retornou novo access_token.')

    credential.accessToken = encrypt_secret(new_access_token)
    credential.tokenType = data.get('token_type') or credential.tokenType
    credential.scope = data.get('scope') or credential.scope
    expires_in = int(data.get('expires_in') or 3600)
    credential.expiresAt = datetime.now() + timedelta(seconds=expires_in)
    credential.lastUpdate = datetime.now()
    db.session.commit()

    return new_access_token


def _upload_file_to_google_drive(local_path: str, file_name: str, folder_id: str, access_token: str) -> str:
    metadata = {'name': file_name}
    if folder_id:
        metadata['parents'] = [folder_id]

    headers = {'Authorization': f'Bearer {access_token}'}
    with open(local_path, 'rb') as file_obj:
        files = {
            'metadata': ('metadata', json.dumps(metadata), 'application/json; charset=UTF-8'),
            'file': (file_name, file_obj, 'application/zip'),
        }
        response = requests.post(
            GOOGLE_DRIVE_UPLOAD_URL,
            headers=headers,
            files=files,
            timeout=120,
            verify=_requests_verify_bundle(),
        )

    if response.status_code >= 400:
        raise RuntimeError(f'Falha no upload Google Drive: {response.text}')

    payload = response.json()
    file_id = payload.get('id')
    if not file_id:
        raise RuntimeError('Upload ao Drive sem id de arquivo retornado.')
    return file_id


def process_pending_drive_uploads_once(limit: int = 10) -> int:
    now_dt = datetime.now()
    pending_items = (
        BackupUpload.query
        .filter(
            BackupUpload.provider == 'google_drive',
            BackupUpload.status.in_(['pending', 'failed']),
            (BackupUpload.nextRetryAt.is_(None)) | (BackupUpload.nextRetryAt <= now_dt),
        )
        .order_by(BackupUpload.creationDate.asc())
        .limit(max(1, limit))
        .all()
    )

    if not pending_items:
        return 0

    credential = OAuthCredential.query.filter_by(provider='google_drive').first()
    if not credential or not credential.accessToken:
        return 0

    folder_id = (_get_config_value('BACKUP_GOOGLE_DRIVE_FOLDER_ID', '') or '').strip()
    uploaded_count = 0

    for item in pending_items:
        run = db.session.get(BackupRun, item.runId)
        if not run or run.status != 'success' or not run.localPath or not os.path.isfile(run.localPath):
            item.status = 'failed'
            item.retryCount = int(item.retryCount or 0) + 1
            wait_minutes = next_retry_delay_minutes(item.retryCount)
            item.nextRetryAt = datetime.now() + timedelta(minutes=wait_minutes)
            item.lastError = 'Arquivo local indisponível para upload.'
            item.lastUpdate = datetime.now()
            db.session.commit()
            continue

        item.status = 'uploading'
        item.lastUpdate = datetime.now()
        db.session.commit()

        try:
            access_token = _get_google_access_token(credential)
            remote_id = _upload_file_to_google_drive(run.localPath, run.fileName or os.path.basename(run.localPath), folder_id, access_token)
            item.status = 'uploaded'
            item.remoteFileId = remote_id
            item.uploadedAt = datetime.now()
            item.lastError = None
            item.nextRetryAt = None
            item.lastUpdate = datetime.now()
            db.session.commit()
            uploaded_count += 1
        except Exception as exc:
            item.status = 'failed'
            item.retryCount = int(item.retryCount or 0) + 1
            wait_minutes = next_retry_delay_minutes(item.retryCount)
            item.nextRetryAt = datetime.now() + timedelta(minutes=wait_minutes)
            item.lastError = str(exc)
            item.lastUpdate = datetime.now()
            db.session.commit()

    return uploaded_count
