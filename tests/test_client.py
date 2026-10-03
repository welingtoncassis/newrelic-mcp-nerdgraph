from __future__ import annotations

import httpx
import pytest
import respx

from newrelic_mcp.errors import NerdGraphError, NerdGraphHTTPError
from newrelic_mcp.nerdgraph.client import NerdGraphClient

from .helpers import ENDPOINT


@respx.mock
async def test_sends_api_key_header(settings):
    route = respx.post(ENDPOINT).mock(return_value=httpx.Response(200, json={"data": {"ok": 1}}))
    async with NerdGraphClient(settings) as client:
        assert await client.execute("{ actor { user { name } } }") == {"ok": 1}
    assert route.calls.last.request.headers["API-Key"] == settings.api_key.get_secret_value()


@respx.mock
async def test_graphql_errors_become_exceptions(settings):
    respx.post(ENDPOINT).mock(
        return_value=httpx.Response(200, json={"errors": [{"message": "Not authorized"}]})
    )
    async with NerdGraphClient(settings) as client:
        with pytest.raises(NerdGraphError, match="Not authorized"):
            await client.execute("{ actor { user { name } } }")


@respx.mock
async def test_http_error_is_wrapped(settings):
    respx.post(ENDPOINT).mock(return_value=httpx.Response(401, text="unauthorized"))
    async with NerdGraphClient(settings) as client:
        with pytest.raises(NerdGraphHTTPError) as excinfo:
            await client.execute("{ actor { user { name } } }")
    assert excinfo.value.status_code == 401


@respx.mock
async def test_retries_transient_status(settings):
    retrying = settings.model_copy(update={"max_retries": 1})
    route = respx.post(ENDPOINT).mock(
        side_effect=[
            httpx.Response(503, text="try later"),
            httpx.Response(200, json={"data": {"ok": True}}),
        ]
    )
    async with NerdGraphClient(retrying) as client:
        assert await client.execute("{ actor { user { name } } }") == {"ok": True}
    assert route.call_count == 2


def test_api_key_is_not_in_repr(settings):
    assert settings.api_key.get_secret_value() not in repr(settings)
