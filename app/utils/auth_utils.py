from datetime import datetime

from flask import flash, jsonify, redirect, url_for
from flask_login import current_user

from app import db
from app.models import Configuration, ConfigSpec


USER_TYPE_LEVELS = {
    'aluno': 1,
    'colaborador': 2,
    'bibliotecario': 3,
    'admin': 4,
}


_PERMISSION_CONFIGS_READY = False


PERMISSION_LEVEL_CONFIG_SPECS = {
    'DASHBOARD_SCREEN_MIN_VIEW_LEVEL': {
        'default': 3,
        'minimum': 1,
        'maximum': 4,
        'allowed_values': {2, 3},
        'description': 'Nível mínimo para acessar a tela de dashboard.',
    },
    'BOOKS_BROWSE_MIN_LEVEL': {
        'default': 1,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para listar/buscar/filtrar/ordenar/paginar livros.',
    },
    'BOOKS_MANAGE_MIN_LEVEL': {
        'default': 2,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para criar/editar livros.',
    },
    'BOOKS_DELETE_MIN_LEVEL': {
        'default': 3,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para excluir/reativar livros.',
    },
    'BOOKS_INCLUDE_DELETED_MIN_LEVEL': {
        'default': 3,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para incluir livros excluídos na listagem.',
    },
    'BOOKS_BULK_IMPORT_MIN_LEVEL': {
        'default': 3,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para todo o fluxo de importação em massa de livros.',
    },
    'KEYWORDS_BROWSE_MIN_LEVEL': {
        'default': 1,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para listar/buscar/paginar tags.',
    },
    'KEYWORDS_MANAGE_MIN_LEVEL': {
        'default': 2,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para criar/editar tags.',
    },
    'KEYWORDS_DELETE_MIN_LEVEL': {
        'default': 3,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para excluir tags.',
    },
    'USERS_BROWSE_MIN_LEVEL': {
        'default': 2,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para listar/buscar/filtrar/ordenar/paginar usuários.',
    },
    'USERS_MANAGE_MIN_LEVEL': {
        'default': 2,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para criar/editar usuários.',
    },
    'USERS_DELETE_MIN_LEVEL': {
        'default': 3,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para excluir/reativar usuários.',
    },
    'USERS_BULK_IMPORT_MIN_LEVEL': {
        'default': 3,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para todo o fluxo de importação em massa de usuários.',
    },
    'LOANS_BROWSE_MIN_LEVEL': {
        'default': 2,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para listar/buscar/filtrar/ordenar/paginar empréstimos.',
    },
    'LOANS_MANAGE_MIN_LEVEL': {
        'default': 2,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para criar/editar empréstimos.',
    },
    'LOANS_CANCEL_MIN_LEVEL': {
        'default': 3,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para cancelar empréstimos.',
    },
    'LOANS_RETURN_MIN_LEVEL': {
        'default': 3,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para informar retorno/perda de empréstimos.',
    },
    'CONFIGS_SCREEN_MIN_LEVEL': {
        'default': 4,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para acessar a tela de configurações.',
    },
    'AUDIT_LOGS_SCREEN_MIN_LEVEL': {
        'default': 3,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para acessar logs de auditoria.',
    },
    'ADMIN_SESSIONS_SCREEN_MIN_LEVEL': {
        'default': 3,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para acessar sessões administrativas.',
    },
    'BACKUP_SCREEN_MIN_VIEW_LEVEL': {
        'default': 3,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para visualizar a tela de backups.',
    },
    'BACKUP_SCREEN_MIN_EDIT_LEVEL': {
        'default': 3,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para editar/executar ações operacionais de backup.',
    },
    'BACKUP_GOOGLE_CONNECT_MIN_LEVEL': {
        'default': 3,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para conectar/desconectar Google Drive no backup.',
    },
    'BACKUP_GOOGLE_CREDENTIALS_VIEW_MIN_LEVEL': {
        'default': 4,
        'minimum': 1,
        'maximum': 4,
        'description': 'Nível mínimo para visualizar/editar campos de credenciais Google no backup.',
    },
}


FEATURE_CONFIG_MAP = {
    'dashboard_view': 'DASHBOARD_SCREEN_MIN_VIEW_LEVEL',
    'books_browse': 'BOOKS_BROWSE_MIN_LEVEL',
    'books_manage': 'BOOKS_MANAGE_MIN_LEVEL',
    'books_delete': 'BOOKS_DELETE_MIN_LEVEL',
    'books_include_deleted': 'BOOKS_INCLUDE_DELETED_MIN_LEVEL',
    'books_bulk_import': 'BOOKS_BULK_IMPORT_MIN_LEVEL',
    'keywords_browse': 'KEYWORDS_BROWSE_MIN_LEVEL',
    'keywords_manage': 'KEYWORDS_MANAGE_MIN_LEVEL',
    'keywords_delete': 'KEYWORDS_DELETE_MIN_LEVEL',
    'users_browse': 'USERS_BROWSE_MIN_LEVEL',
    'users_manage': 'USERS_MANAGE_MIN_LEVEL',
    'users_delete': 'USERS_DELETE_MIN_LEVEL',
    'users_bulk_import': 'USERS_BULK_IMPORT_MIN_LEVEL',
    'loans_browse': 'LOANS_BROWSE_MIN_LEVEL',
    'loans_manage': 'LOANS_MANAGE_MIN_LEVEL',
    'loans_cancel': 'LOANS_CANCEL_MIN_LEVEL',
    'loans_return': 'LOANS_RETURN_MIN_LEVEL',
    'configs_screen': 'CONFIGS_SCREEN_MIN_LEVEL',
    'audit_logs_screen': 'AUDIT_LOGS_SCREEN_MIN_LEVEL',
    'admin_sessions_screen': 'ADMIN_SESSIONS_SCREEN_MIN_LEVEL',
    'backup_view': 'BACKUP_SCREEN_MIN_VIEW_LEVEL',
    'backup_edit': 'BACKUP_SCREEN_MIN_EDIT_LEVEL',
    'backup_google_connect': 'BACKUP_GOOGLE_CONNECT_MIN_LEVEL',
    'backup_google_credentials_view': 'BACKUP_GOOGLE_CREDENTIALS_VIEW_MIN_LEVEL',
}


def _get_actor_user_id(actor_user_id: int | None = None) -> int:
    if actor_user_id is not None:
        return int(actor_user_id)
    try:
        if getattr(current_user, 'is_authenticated', False):
            return int(current_user.userId)
    except Exception:
        pass
    return 1


def get_config_bool(key: str) -> bool:
    config_entry = Configuration.query.filter_by(key=key).first()
    if not config_entry or config_entry.value is None:
        return False
    return str(config_entry.value).strip() == '1'


def ensure_permission_level_configs(actor_user_id: int | None = None) -> None:
    actor_id = _get_actor_user_id(actor_user_id)
    now = datetime.now()
    changed = False

    for key, spec in PERMISSION_LEVEL_CONFIG_SPECS.items():
        cfg_spec = ConfigSpec.query.filter_by(key=key).first()
        allowed_values = spec.get('allowed_values')
        allowed_values_text = None
        if allowed_values:
            allowed_values_text = ','.join(str(item) for item in sorted(allowed_values))

        if not cfg_spec:
            cfg_spec = ConfigSpec(
                key=key,
                valueType='integer',
                allowedValues=allowed_values_text,
                minValue=spec['minimum'],
                maxValue=spec['maximum'],
                required=True,
                defaultValue=str(spec['default']),
                description=spec['description'],
                creationDate=now,
                lastUpdate=now,
                createdBy=actor_id,
                updatedBy=actor_id,
            )
            db.session.add(cfg_spec)
            changed = True

        cfg_entry = Configuration.query.filter_by(key=key).first()
        if not cfg_entry:
            cfg_entry = Configuration(
                key=key,
                value=str(spec['default']),
                description=spec['description'],
                creationDate=now,
                lastUpdate=now,
                createdBy=actor_id,
                updatedBy=actor_id,
            )
            db.session.add(cfg_entry)
            changed = True

    if changed:
        db.session.commit()


def _ensure_permission_configs_ready() -> None:
    global _PERMISSION_CONFIGS_READY

    if _PERMISSION_CONFIGS_READY:
        return

    try:
        ensure_permission_level_configs()
        _PERMISSION_CONFIGS_READY = True
    except Exception:
        # Banco ainda pode não estar migrado/criado em bootstrap ou testes.
        # O próximo acesso tentará novamente.
        return


def is_admin_user() -> bool:
    return bool(getattr(current_user, 'is_authenticated', False) and getattr(current_user, 'userType', None) == 'admin')


def can_manage_user_bulk_import() -> bool:
    return can_access_feature('users_bulk_import')


def get_user_level(user_type: str | None = None) -> int:
    resolved_type = user_type or getattr(current_user, 'userType', None)
    return USER_TYPE_LEVELS.get((resolved_type or '').strip().lower(), 0)


def _get_allowed_levels_for_config(config_key: str) -> set[int] | None:
    spec = PERMISSION_LEVEL_CONFIG_SPECS.get(config_key, {})
    allowed = spec.get('allowed_values')
    if not allowed:
        return None
    return {int(item) for item in allowed}


def get_config_int(key: str, default: int, minimum: int | None = None, maximum: int | None = None) -> int:
    entry = Configuration.query.filter_by(key=key).first()
    raw = entry.value if entry and entry.value is not None else default
    try:
        value = int(raw)
    except (TypeError, ValueError):
        value = default

    if minimum is not None and value < minimum:
        value = minimum
    if maximum is not None and value > maximum:
        value = maximum
    return value


def get_configured_min_level(config_key: str) -> int:
    _ensure_permission_configs_ready()
    spec = PERMISSION_LEVEL_CONFIG_SPECS.get(config_key)
    if not spec:
        return 4
    value = get_config_int(
        config_key,
        default=int(spec['default']),
        minimum=int(spec['minimum']),
        maximum=int(spec['maximum']),
    )
    allowed_levels = _get_allowed_levels_for_config(config_key)
    if allowed_levels and value not in allowed_levels:
        return int(spec['default'])
    return value


def can_access_feature(feature: str, user_type: str | None = None) -> bool:
    _ensure_permission_configs_ready()
    config_key = FEATURE_CONFIG_MAP.get(feature)
    if not config_key:
        return False
    min_level = get_configured_min_level(config_key)
    return get_user_level(user_type=user_type) >= min_level


def enforce_feature_access(feature: str, message: str, redirect_endpoint: str = 'navigation.menu'):
    if can_access_feature(feature):
        return None
    flash(message, 'warning')
    return redirect(url_for(redirect_endpoint))


def enforce_api_feature_access(feature: str, message: str = 'Acesso negado.'):
    if can_access_feature(feature):
        return None
    return jsonify({'success': False, 'error': message}), 403


def can_view_backup_screen() -> bool:
    return can_access_feature('backup_view')


def can_edit_backup_screen() -> bool:
    if not can_access_feature('backup_edit'):
        return False
    min_view = get_configured_min_level('BACKUP_SCREEN_MIN_VIEW_LEVEL')
    min_edit = get_configured_min_level('BACKUP_SCREEN_MIN_EDIT_LEVEL')
    if min_edit < min_view:
        min_edit = min_view
    return get_user_level() >= min_edit


def can_connect_backup_google() -> bool:
    return can_access_feature('backup_google_connect')


def can_view_backup_google_credentials() -> bool:
    return can_access_feature('backup_google_credentials_view')


def build_permission_capabilities() -> dict:
    if not getattr(current_user, 'is_authenticated', False):
        return {}

    return {
        'can_access_dashboard': can_access_feature('dashboard_view'),
        'can_view_books': can_access_feature('books_browse'),
        'can_manage_books': can_access_feature('books_manage'),
        'can_delete_books': can_access_feature('books_delete'),
        'can_include_deleted_books': can_access_feature('books_include_deleted'),
        'can_manage_book_bulk_import': can_access_feature('books_bulk_import'),
        'can_view_keywords': can_access_feature('keywords_browse'),
        'can_manage_keywords': can_access_feature('keywords_manage'),
        'can_delete_keywords': can_access_feature('keywords_delete'),
        'can_view_users': can_access_feature('users_browse'),
        'can_manage_users': can_access_feature('users_manage'),
        'can_delete_users': can_access_feature('users_delete'),
        'can_manage_user_bulk_import': can_access_feature('users_bulk_import'),
        'can_view_loans': can_access_feature('loans_browse'),
        'can_manage_loans': can_access_feature('loans_manage'),
        'can_cancel_loans': can_access_feature('loans_cancel'),
        'can_return_loans': can_access_feature('loans_return'),
        'can_view_configs_screen': can_access_feature('configs_screen'),
        'can_view_audit_logs_screen': can_access_feature('audit_logs_screen'),
        'can_view_admin_sessions_screen': can_access_feature('admin_sessions_screen'),
        'can_view_backup_screen': can_view_backup_screen(),
        'can_edit_backup_screen': can_edit_backup_screen(),
        'can_connect_backup_google': can_connect_backup_google(),
        'can_view_backup_google_credentials': can_view_backup_google_credentials(),
    }
