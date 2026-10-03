from __future__ import annotations

from newrelic_mcp.security.redaction import REDACTED, redact, redact_text


def test_masks_new_relic_key():
    assert "NRAK" not in redact_text("key=NRAK-ABCDEFGHIJKLMNOPQRSTUVWX")


def test_masks_bearer_token():
    assert redact_text("Authorization: Bearer abcdef0123456789").endswith(REDACTED)


def test_masks_jwt():
    jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dBjftJeZ4CVPmB92K27uhbUJU1p1r"
    assert redact_text(f"token {jwt}") == f"token {REDACTED}"


def test_drops_values_under_sensitive_keys():
    assert redact({"password": "hunter2", "user": "ana"}) == {
        "password": REDACTED,
        "user": "ana",
    }


def test_walks_nested_structures():
    payload = {"results": [{"message": "aws key AKIAIOSFODNN7EXAMPLE"}]}
    assert "AKIA" not in str(redact(payload))


def test_leaves_ordinary_text_untouched():
    assert redact_text("timeout after 30s calling checkout") == (
        "timeout after 30s calling checkout"
    )
