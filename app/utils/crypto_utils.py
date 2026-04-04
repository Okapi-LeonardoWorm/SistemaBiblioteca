import base64
import hashlib

from flask import current_app


def _normalize_secret(raw_secret: str) -> bytes:
    digest = hashlib.sha256((raw_secret or '').encode('utf-8')).digest()
    return base64.urlsafe_b64encode(digest)


def _get_fernet_key() -> bytes:
    explicit_key = (current_app.config.get('BACKUP_TOKEN_ENCRYPTION_KEY') or '').strip()
    if explicit_key:
        return explicit_key.encode('utf-8')

    fallback_secret = (current_app.config.get('SECRET_KEY') or '').strip()
    if not fallback_secret:
        raise RuntimeError('SECRET_KEY ausente para derivar chave de criptografia de token.')
    return _normalize_secret(fallback_secret)


def encrypt_secret(plain_text: str | None) -> str | None:
    if plain_text is None:
        return None

    try:
        from cryptography.fernet import Fernet
    except Exception as exc:
        raise RuntimeError('Pacote cryptography não disponível para criptografia de tokens.') from exc

    key = _get_fernet_key()
    token = Fernet(key).encrypt(plain_text.encode('utf-8'))
    return token.decode('utf-8')


def decrypt_secret(cipher_text: str | None) -> str | None:
    if cipher_text is None:
        return None

    try:
        from cryptography.fernet import Fernet
    except Exception as exc:
        raise RuntimeError('Pacote cryptography não disponível para descriptografia de tokens.') from exc

    key = _get_fernet_key()
    plain = Fernet(key).decrypt(cipher_text.encode('utf-8'))
    return plain.decode('utf-8')
