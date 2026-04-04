from flask_login import current_user

from app.models import Configuration


USER_TYPE_LEVELS = {
    'aluno': 1,
    'colaborador': 2,
    'bibliotecario': 3,
    'admin': 4,
}


def get_config_bool(key: str) -> bool:
    config_entry = Configuration.query.filter_by(key=key).first()
    if not config_entry or config_entry.value is None:
        return False
    return str(config_entry.value).strip() == '1'


def is_admin_user() -> bool:
    return bool(getattr(current_user, 'is_authenticated', False) and getattr(current_user, 'userType', None) == 'admin')


def can_manage_user_bulk_import() -> bool:
    if not getattr(current_user, 'is_authenticated', False):
        return False
    return getattr(current_user, 'userType', None) in {'admin', 'bibliotecario'}


def get_user_level(user_type: str | None = None) -> int:
    resolved_type = user_type or getattr(current_user, 'userType', None)
    return USER_TYPE_LEVELS.get((resolved_type or '').strip().lower(), 0)


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


def can_view_backup_screen() -> bool:
    if not getattr(current_user, 'is_authenticated', False):
        return False
    min_level = get_config_int('BACKUP_SCREEN_MIN_VIEW_LEVEL', default=3, minimum=1, maximum=4)
    return get_user_level() >= min_level


def can_edit_backup_screen() -> bool:
    if not getattr(current_user, 'is_authenticated', False):
        return False
    min_view = get_config_int('BACKUP_SCREEN_MIN_VIEW_LEVEL', default=3, minimum=1, maximum=4)
    min_edit = get_config_int('BACKUP_SCREEN_MIN_EDIT_LEVEL', default=4, minimum=1, maximum=4)
    if min_edit < min_view:
        min_edit = min_view
    return get_user_level() >= min_edit
