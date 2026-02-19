import unicodedata

def splitStringIntoList(string):
    if not string:
        return []
    string_list = [item.strip().lower() for item in string.split(';') if item.strip()]
    return string_list

def normalize_tag(token: str) -> str:
    if not token:
        return ''
    # remove leading/trailing spaces
    token = token.strip()
    # remove accents
    nfkd = unicodedata.normalize('NFKD', token)
    ascii_only = ''.join([c for c in nfkd if not unicodedata.combining(c)])
    # uppercase
    up = ascii_only.upper()
    # keep only allowed chars: A-Z, 0-9, space, hyphen
    allowed = []
    for ch in up:
        if ('A' <= ch <= 'Z') or ('0' <= ch <= '9') or ch in [' ', '-']:
            allowed.append(ch)
    cleaned = ''.join(allowed)
    # collapse multiple spaces
    cleaned = ' '.join(cleaned.split())
    return cleaned.strip()
