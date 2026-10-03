from __future__ import annotations

import pytest

from newrelic_mcp.__main__ import _parse_args, main


def test_defaults_to_stdio():
    assert _parse_args([]).transport == "stdio"


def test_transport_is_configurable():
    assert _parse_args(["--transport", "streamable-http"]).transport == "streamable-http"


def test_version_flag_exits_cleanly():
    with pytest.raises(SystemExit) as excinfo:
        _parse_args(["--version"])
    assert excinfo.value.code == 0


def test_missing_api_key_exits_with_guidance(monkeypatch, capsys):
    monkeypatch.delenv("NEW_RELIC_API_KEY", raising=False)
    monkeypatch.chdir("/tmp")  # avoid picking up a developer .env  # noqa: S108
    from newrelic_mcp import config

    config.get_settings.cache_clear()

    assert main([]) == 2
    assert "NEW_RELIC_API_KEY is required" in capsys.readouterr().err
    config.get_settings.cache_clear()
