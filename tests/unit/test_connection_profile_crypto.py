"""Unit tests for src/api/connection_profile_crypto.py (Infra B — credential encryption)."""

import pytest


# ---------------------------------------------------------------------------
# encrypt / decrypt roundtrip
# ---------------------------------------------------------------------------

def test_encrypt_decrypt_roundtrip(monkeypatch):
    monkeypatch.setenv("CONNECTION_PROFILE_ENCRYPTION_KEY", "test-key-for-encryption-tests!!")
    from importlib import reload
    from src.api import connection_profile_crypto as mod
    reload(mod)

    plaintext = {"password": "s3cr3t", "service_account_json": '{"type":"service_account"}'}
    token = mod.encrypt_credentials(plaintext)

    assert isinstance(token, str)
    assert "s3cr3t" not in token  # encrypted, not plaintext

    recovered = mod.decrypt_credentials(token)
    assert recovered == plaintext


def test_encrypt_produces_different_ciphertext_each_call(monkeypatch):
    monkeypatch.setenv("CONNECTION_PROFILE_ENCRYPTION_KEY", "test-key-for-encryption-tests!!")
    from importlib import reload
    from src.api import connection_profile_crypto as mod
    reload(mod)

    creds = {"password": "same"}
    t1 = mod.encrypt_credentials(creds)
    t2 = mod.encrypt_credentials(creds)
    assert t1 != t2  # Fernet includes a random IV


def test_decrypt_wrong_key_raises(monkeypatch):
    monkeypatch.setenv("CONNECTION_PROFILE_ENCRYPTION_KEY", "key-a-for-encryption-test!!!!!")
    from importlib import reload
    from src.api import connection_profile_crypto as mod
    reload(mod)

    token = mod.encrypt_credentials({"pw": "abc"})

    monkeypatch.setenv("CONNECTION_PROFILE_ENCRYPTION_KEY", "key-b-different-encryption-test!")
    reload(mod)

    with pytest.raises(Exception):
        mod.decrypt_credentials(token)


def test_encrypt_empty_dict(monkeypatch):
    monkeypatch.setenv("CONNECTION_PROFILE_ENCRYPTION_KEY", "test-key-for-encryption-tests!!")
    from importlib import reload
    from src.api import connection_profile_crypto as mod
    reload(mod)

    token = mod.encrypt_credentials({})
    recovered = mod.decrypt_credentials(token)
    assert recovered == {}


def test_fallback_key_warns_and_works(monkeypatch, caplog):
    monkeypatch.delenv("CONNECTION_PROFILE_ENCRYPTION_KEY", raising=False)
    from importlib import reload
    from src.api import connection_profile_crypto as mod
    reload(mod)

    import logging
    with caplog.at_level(logging.WARNING):
        token = mod.encrypt_credentials({"key": "value"})

    assert any("insecure" in r.message.lower() or "not set" in r.message.lower() for r in caplog.records)
    recovered = mod.decrypt_credentials(token)
    assert recovered == {"key": "value"}


# ---------------------------------------------------------------------------
# mask_credentials
# ---------------------------------------------------------------------------

def test_mask_credentials_all_masked():
    from src.api.connection_profile_crypto import mask_credentials, MASKED
    creds = {"password": "s3cr3t", "api_key": "abc123", "service_account": "{}"}
    masked = mask_credentials(creds)
    assert set(masked.values()) == {MASKED}
    assert set(masked.keys()) == set(creds.keys())


def test_mask_credentials_empty():
    from src.api.connection_profile_crypto import mask_credentials
    assert mask_credentials({}) == {}


def test_masked_sentinel_value():
    from src.api.connection_profile_crypto import MASKED
    assert MASKED == "••••••"
