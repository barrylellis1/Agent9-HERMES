"""
Regression test: the data-product-onboarding workflow status endpoint was
echoing plaintext connection credentials (Snowflake/SQL Server passwords,
private keys) back to the caller on every GET .../status poll, because
_create_record() cached the raw request.model_dump() verbatim — found live
2026-07-25 during Brookshire Brothers onboarding (a real password appeared in
the status response's payload.connection_overrides.password).
"""

from src.api.routes.workflows import _redact_secrets


def test_redacts_password_in_connection_overrides():
    payload = {
        "data_product_id": "BB_FI_03",
        "connection_overrides": {
            "username": "BARRYLELLIS1",
            "password": "Debbie_02251961!",
            "account": "VSGHWKW-SI38932",
            "warehouse": "AGENT9_WH",
            "database": "AGENT9_DEMO",
            "role": "",
        },
    }

    redacted = _redact_secrets(payload)

    assert redacted["connection_overrides"]["password"] == "***REDACTED***"
    # Non-secret fields must survive untouched
    assert redacted["connection_overrides"]["username"] == "BARRYLELLIS1"
    assert redacted["connection_overrides"]["account"] == "VSGHWKW-SI38932"
    assert redacted["data_product_id"] == "BB_FI_03"


def test_redacts_private_key_and_token_variants():
    payload = {
        "connection_overrides": {
            "private_key": "-----BEGIN PRIVATE KEY-----...",
            "private_key_path": "/secrets/sf_key.p8",
            "api_key": "sk-abc123",
            "access_token": "eyJhbGciOi...",
        }
    }

    redacted = _redact_secrets(payload)

    for key in ("private_key", "private_key_path", "api_key", "access_token"):
        assert redacted["connection_overrides"][key] == "***REDACTED***"


def test_empty_secret_value_left_as_is_not_redacted_to_placeholder():
    payload = {"connection_overrides": {"password": ""}}
    redacted = _redact_secrets(payload)
    assert redacted["connection_overrides"]["password"] == ""


def test_redacts_within_nested_lists():
    payload = {"items": [{"password": "secret1"}, {"password": "secret2"}]}
    redacted = _redact_secrets(payload)
    assert redacted["items"][0]["password"] == "***REDACTED***"
    assert redacted["items"][1]["password"] == "***REDACTED***"


def test_non_secret_payload_unchanged():
    payload = {"client_id": "brookshire_brothers", "tables": ["A", "B"], "nested": {"count": 3}}
    assert _redact_secrets(payload) == payload
