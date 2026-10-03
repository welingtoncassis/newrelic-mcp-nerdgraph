from __future__ import annotations

import pytest
from pydantic import ValidationError

from newrelic_mcp.config import Region, Settings, get_settings


def build(**env: str) -> Settings:
    return Settings(**env)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("123,456", [123, 456]),
        ("123, 456 ,789", [123, 456, 789]),
        (1234567, [1234567]),  # pydantic-settings JSON-decodes a lone number
        ([1, 2], [1, 2]),
    ],
)
def test_account_ids_accept_every_env_shape(raw, expected):
    assert build(api_key="NRAK-x", account_ids=raw).account_ids == expected


def test_api_key_is_required():
    with pytest.raises(ValidationError):
        Settings(account_ids=[1])  # type: ignore[call-arg]


def test_region_selects_the_endpoint():
    assert Region.EU.nerdgraph_endpoint == "https://api.eu.newrelic.com/graphql"
    assert Region.US.ui_base_url == "https://one.newrelic.com"


def test_default_account_is_the_first(settings):
    assert settings.default_account_id == 1234567


def test_explicit_accounts_win_over_defaults(settings):
    assert settings.resolve_accounts([999]) == [999]


def test_settings_are_cached(monkeypatch):
    monkeypatch.setenv("NEW_RELIC_API_KEY", "NRAK-cachedcachedcached")
    get_settings.cache_clear()
    assert get_settings() is get_settings()
    get_settings.cache_clear()
