"""Validation applied to every NRQL string before it reaches NerdGraph.

NRQL itself has no write statements, so the guard is not a security boundary
against data modification. It exists to stop two concrete failure modes:
injection of a second statement through a user-supplied fragment, and unbounded
queries that return far more data than an LLM context can hold.
"""

from __future__ import annotations

import re

from ..errors import NrqlValidationError

_MAX_LENGTH = 8_000

_ALLOWED_START = re.compile(r"^\s*(SELECT|FROM|SHOW)\b", re.IGNORECASE)
_TIME_WINDOW = re.compile(r"\b(SINCE|UNTIL)\b", re.IGNORECASE)
_LIMIT_CLAUSE = re.compile(r"\bLIMIT\s+(MAX|\d+)\b", re.IGNORECASE)
_COMMENT = re.compile(r"(--|/\*|\*/)")
_STATEMENT_BREAK = re.compile(r";\s*\S")


def _strip_literals(query: str) -> str:
    """Blank out quoted literals so clause detection ignores their content."""
    return re.sub(r"'[^']*'|\"[^\"]*\"", "''", query)


def validate_nrql(query: str) -> str:
    """Return a normalised copy of ``query`` or raise :class:`NrqlValidationError`."""
    normalised = query.strip().rstrip(";").strip()
    if not normalised:
        raise NrqlValidationError("NRQL query is empty.")
    if len(normalised) > _MAX_LENGTH:
        raise NrqlValidationError(f"NRQL query exceeds {_MAX_LENGTH} characters.")

    bare = _strip_literals(normalised)
    if _STATEMENT_BREAK.search(bare):
        raise NrqlValidationError("Multiple statements are not allowed in a single query.")
    if _COMMENT.search(bare):
        raise NrqlValidationError("Comment markers are not allowed in NRQL queries.")
    if not _ALLOWED_START.match(bare):
        raise NrqlValidationError("NRQL queries must start with SELECT, FROM or SHOW.")
    return normalised


def apply_defaults(query: str, *, default_since: str, max_rows: int) -> str:
    """Append a time window and row limit when the query does not set its own.

    An unbounded ``SELECT * FROM Log`` is the single most common way to blow up a
    tool response, so both clauses are enforced rather than merely suggested.
    """
    bare = _strip_literals(query)
    result = query
    if not _TIME_WINDOW.search(bare):
        result = f"{result} SINCE {default_since}"
    if not _LIMIT_CLAUSE.search(bare) and re.match(r"^\s*SELECT", bare, re.IGNORECASE):
        if not re.search(r"\b(TIMESERIES|COMPARE\s+WITH)\b", bare, re.IGNORECASE):
            result = f"{result} LIMIT {max_rows}"
    return result


def escape_nrql_string(value: str) -> str:
    """Escape a value for safe interpolation into a single-quoted NRQL literal."""
    return value.replace("\\", "\\\\").replace("'", "\\'")
