"""Tests for password hashing and JWT authentication mechanisms."""

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)


def test_password_hashing():
    raw_password = "SecureStudentPass123!"
    hashed = get_password_hash(raw_password)
    
    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_creation_and_decoding():
    user_id = "11111111-2222-3333-4444-555555555555"
    token = create_access_token(subject=user_id, claims={"role": "student"})
    
    assert isinstance(token, str)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == user_id
    assert payload["role"] == "student"
    assert "exp" in payload
