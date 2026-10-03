from __future__ import annotations

import json

from newrelic_mcp.formatting import finalize, rows_with_limit


def test_rows_are_capped():
    rows, truncated = rows_with_limit([{"i": i} for i in range(10)], 3)
    assert len(rows) == 3
    assert truncated


def test_small_payload_is_passed_through(settings):
    payload = finalize({"results": [{"a": 1}]}, settings)
    assert json.loads(payload) == {"results": [{"a": 1}]}


def test_large_payload_is_truncated_with_an_explanation(settings):
    tight = settings.model_copy(update={"max_response_chars": 2_000})
    rows = [{"message": "x" * 100, "i": i} for i in range(500)]

    payload = json.loads(finalize({"results": rows}, tight))

    assert len(payload["results"]) < len(rows)
    assert "truncated" in payload["_truncated"]


def test_redaction_can_be_disabled(settings):
    off = settings.model_copy(update={"redact_sensitive_values": False})
    body = finalize({"results": [{"token": "NRAK-ABCDEFGHIJKLMNOPQRSTUVWX"}]}, off)
    assert "NRAK-" in body
