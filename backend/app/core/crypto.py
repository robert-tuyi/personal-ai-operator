"""Symmetric encryption for secrets at rest (Fernet/AES via `cryptography`).

Currently used to encrypt stored Google OAuth tokens (ADR 0003) — anything else that needs
at-rest encryption should go through here rather than rolling its own.
"""

from functools import lru_cache

from cryptography.fernet import Fernet

from app.config import get_settings


@lru_cache
def _fernet() -> Fernet:
    return Fernet(get_settings().token_encryption_key.encode())


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    return _fernet().decrypt(ciphertext.encode()).decode()
