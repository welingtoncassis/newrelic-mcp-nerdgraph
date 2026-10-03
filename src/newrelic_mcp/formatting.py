"""Shaping of tool payloads so they stay useful inside a model context."""

from __future__ import annotations

import json
from typing import Any

from .config import Settings
from .security.redaction import redact

_TRUNCATION_NOTE = "_truncated"


def rows_with_limit(rows: list[dict[str, Any]], max_rows: int) -> tuple[list[dict[str, Any]], bool]:
    """Cut ``rows`` to ``max_rows`` and report whether anything was dropped."""
    if len(rows) <= max_rows:
        return rows, False
    return rows[:max_rows], True


def finalize(payload: dict[str, Any], settings: Settings) -> str:
    """Redact, serialise and size-cap a tool result.

    Tools return JSON strings rather than objects because that keeps the exact
    byte budget visible here, in one place, instead of at every call site.
    """
    body = redact(payload) if settings.redact_sensitive_values else payload
    text = json.dumps(body, ensure_ascii=False, default=str, indent=2)

    if len(text) <= settings.max_response_chars:
        return text

    trimmed = _shrink(body, settings.max_response_chars)
    return json.dumps(trimmed, ensure_ascii=False, default=str, indent=2)


def _shrink(payload: Any, budget: int) -> Any:
    """Drop rows from the largest list in the payload until it fits the budget."""
    if not isinstance(payload, dict):
        return payload

    shrunk = dict(payload)
    list_keys = [key for key, value in shrunk.items() if isinstance(value, list)]
    if not list_keys:
        return {**shrunk, _TRUNCATION_NOTE: "Payload exceeded the response budget."}

    target = max(list_keys, key=lambda key: len(json.dumps(shrunk[key], default=str)))
    rows: list[Any] = list(shrunk[target])
    while rows and len(json.dumps(shrunk | {target: rows}, default=str)) > budget:
        rows = rows[: max(1, len(rows) // 2)]
        if len(rows) == 1:
            break

    shrunk[target] = rows
    shrunk[_TRUNCATION_NOTE] = (
        f"'{target}' was truncated to {len(rows)} items to fit the response budget. "
        "Narrow the time window, add a WHERE clause, or aggregate instead."
    )
    return shrunk
