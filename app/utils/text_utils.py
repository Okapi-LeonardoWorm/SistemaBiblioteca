import unicodedata


def split_string_into_list(string):
    if not string:
        return []
    # Backward-compatible helper: now supports comma and semicolon separators.
    normalized = str(string).replace(';', ',')
    return [item.strip().lower() for item in normalized.split(',') if item.strip()]


def normalize_tag(token: str) -> str:
    if not token:
        return ''
    token = unicodedata.normalize('NFC', token.strip())
    up = token.upper()
    allowed = []
    for ch in up:
        if ch.isalpha() or ch.isdigit() or ch in [' ', '-']:
            allowed.append(ch)
    cleaned = ''.join(allowed)
    cleaned = ' '.join(cleaned.split())
    return cleaned.strip()


def parse_normalized_tags(raw: str):
    if not raw:
        return []

    parts = []
    seen = set()
    for token in str(raw).replace(';', ',').split(','):
        normalized = normalize_tag(token)
        if normalized and normalized not in seen:
            parts.append(normalized)
            seen.add(normalized)
    return parts
