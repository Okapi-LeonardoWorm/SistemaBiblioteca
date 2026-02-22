from datetime import date


def calc_age(birth_date):
    if not birth_date:
        return None
    try:
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    except Exception:
        return None


def parse_date(value: str):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except Exception:
        return None
