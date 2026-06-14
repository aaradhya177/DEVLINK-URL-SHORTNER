import uuid

import pytest
from fastapi import HTTPException

from src.auth import security


def test_password_hashing_never_stores_plaintext() -> None:
    """Password hashes should verify but not expose the original password."""
    password_hash = security.hash_password("correct-horse")

    assert password_hash != "correct-horse"
    assert security.verify_password("correct-horse", password_hash) is True
    assert security.verify_password("wrong-password", password_hash) is False
    assert security.verify_password("correct-horse", None) is False


def test_access_and_refresh_tokens_enforce_type() -> None:
    """JWT helpers should reject using refresh tokens as access tokens."""
    user_id = uuid.uuid4()
    access_token, access_expires_at = security.create_access_token(user_id)
    refresh_token, refresh_token_id, refresh_expires_at = security.create_refresh_token(
        user_id
    )

    access_payload = security.decode_token(access_token, expected_type="access")
    refresh_payload = security.decode_token(refresh_token, expected_type="refresh")

    assert access_payload["sub"] == str(user_id)
    assert access_payload["type"] == "access"
    assert refresh_payload["sub"] == str(user_id)
    assert refresh_payload["jti"] == str(refresh_token_id)
    assert refresh_payload["type"] == "refresh"
    assert refresh_expires_at > access_expires_at
    with pytest.raises(HTTPException) as exc_info:
        security.decode_token(refresh_token, expected_type="access")
    assert exc_info.value.status_code == 401


def test_tampered_token_is_rejected() -> None:
    """Modified JWT bytes must fail signature verification."""
    token, _ = security.create_access_token(uuid.uuid4())
    header, payload, signature = token.split(".")
    replacement = "a" if signature[0] != "a" else "b"
    tampered = ".".join((header, payload, replacement + signature[1:]))

    with pytest.raises(HTTPException) as exc_info:
        security.decode_token(tampered, expected_type="access")

    assert exc_info.value.status_code == 401
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


def test_refresh_token_hash_and_secure_compare() -> None:
    """Refresh tokens should be hashed and compared in constant-time helper."""
    digest = security.hash_refresh_token("refresh-token")

    assert digest != "refresh-token"
    assert len(digest) == 64
    assert security.secure_compare(digest, security.hash_refresh_token("refresh-token"))
    assert not security.secure_compare(digest, security.hash_refresh_token("other"))
