import unicodedata


def split_string_into_list(string):
    if not string:
        return []
    return [item.strip().lower() for item in string.split(';') if item.strip()]


def normalize_tag(token: str) -> str:
    if not token:
        return ''
    token = token.strip()
    nfkd = unicodedata.normalize('NFKD', token)
    ascii_only = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    up = ascii_only.upper()
    allowed = []
    for ch in up:
        if ('A' <= ch <= 'Z') or ('0' <= ch <= '9') or ch in [' ', '-']:
            allowed.append(ch)
    cleaned = ''.join(allowed)
    cleaned = ' '.join(cleaned.split())
    return cleaned.strip()
