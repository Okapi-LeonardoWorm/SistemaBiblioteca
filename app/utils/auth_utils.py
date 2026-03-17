from flask_login import current_user

from app.models import Configuration


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
