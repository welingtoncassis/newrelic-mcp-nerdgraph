"""Masking of credential-shaped values found in telemetry payloads.

Log lines and custom attributes routinely contain bearer tokens, API keys and
authorization headers. Those values would otherwise be replayed verbatim into an
LLM context, so they are masked on the way out.
"""

from __future__ import annotations

import re
from typing import Any

REDACTED = "[REDACTED]"

_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"NRAK-[A-Z0-9]{20,}", re.IGNORECASE),
    re.compile(r"NRJS-[A-Za-z0-9]{10,}"),
    re.compile(r"NRII-[A-Za-z0-9_-]{10,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\bey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    re.compile(r"(?i)\b(?:bearer|basic)\s+[A-Za-z0-9._~+/=-]{12,}"),
    re.compile(
        r"(?i)\b(?:api[-_]?key|secret|password|passwd|token|authorization)\b"
        r"\s*[:=]\s*\"?[^\s\"',;]{6,}"
    ),
)

_SENSITIVE_KEY = re.compile(
    r"(?i)(password|passwd|secret|token|api[-_]?key|authorization|credential|private[-_]?key)"
)


def redact_text(value: str) -> str:
    """Replace credential-shaped substrings in ``value``."""
    for pattern in _PATTERNS:
        value = pattern.sub(REDACTED, value)
    return value


def redact(value: Any) -> Any:
    """Recursively redact strings inside dicts, lists and scalars.

    Values whose *key* looks sensitive are dropped entirely rather than
    pattern-matched, since the key alone is enough evidence.
    """
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, dict):
        return {
            key: REDACTED if isinstance(key, str) and _SENSITIVE_KEY.search(key) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [redact(item) for item in value]
    return value
