from __future__ import annotations

import pytest

from newrelic_mcp.errors import NrqlValidationError
from newrelic_mcp.security.nrql_guard import apply_defaults, escape_nrql_string, validate_nrql


@pytest.mark.parametrize(
    "query",
    [
        "SELECT count(*) FROM Transaction",
        "  select average(duration) from Transaction since 1 hour ago  ",
        "FROM Log SELECT message",
        "SHOW EVENT TYPES",
    ],
)
def test_accepts_read_queries(query):
    assert validate_nrql(query)


@pytest.mark.parametrize(
    "query",
    [
        "",
        "DELETE FROM Transaction",
        "SELECT count(*) FROM Transaction; SELECT 1 FROM Log",
        "SELECT count(*) FROM Transaction -- comment",
        "SELECT count(*) FROM Transaction /* x */",
    ],
)
def test_rejects_unsafe_queries(query):
    with pytest.raises(NrqlValidationError):
        validate_nrql(query)


def test_trailing_semicolon_is_normalised():
    assert validate_nrql("SELECT count(*) FROM Log;") == "SELECT count(*) FROM Log"


def test_semicolon_inside_literal_is_allowed():
    query = "SELECT count(*) FROM Log WHERE message = 'a; b'"
    assert validate_nrql(query) == query


def test_defaults_add_since_and_limit():
    result = apply_defaults("SELECT * FROM Log", default_since="30 MINUTES AGO", max_rows=100)
    assert "SINCE 30 MINUTES AGO" in result
    assert result.endswith("LIMIT 100")


def test_defaults_respect_explicit_clauses():
    query = "SELECT * FROM Log SINCE 1 DAY AGO LIMIT 5"
    assert apply_defaults(query, default_since="30 MINUTES AGO", max_rows=100) == query


def test_timeseries_is_not_limited():
    result = apply_defaults(
        "SELECT count(*) FROM Log SINCE 1 HOUR AGO TIMESERIES",
        default_since="30 MINUTES AGO",
        max_rows=100,
    )
    assert "LIMIT" not in result


def test_escape_closes_injection_vector():
    assert escape_nrql_string("a' OR 1=1 --") == "a\\' OR 1=1 --"
