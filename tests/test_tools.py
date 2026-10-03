"""End-to-end tool calls through the MCP server, with NerdGraph mocked."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from mcp.server.mcpserver.exceptions import ToolError

from newrelic_mcp.server import create_server

from .helpers import ENDPOINT, call, nrql_response


@pytest.fixture
def server(settings):
    return create_server(settings)


@respx.mock
async def test_run_nrql_returns_results(server):
    respx.post(ENDPOINT).mock(return_value=nrql_response([{"count": 7}]))
    payload = json.loads(await call(server, "run_nrql", {"query": "SELECT count(*) FROM Log"}))
    assert payload["results"] == [{"count": 7}]
    assert payload["accounts"] == [1234567]


async def test_validate_nrql_reports_rejection(server):
    payload = json.loads(
        await call(server, "validate_nrql_query", {"query": "DROP TABLE Transaction"})
    )
    assert payload["valid"] is False


async def test_validate_nrql_shows_added_clauses(server):
    payload = json.loads(
        await call(server, "validate_nrql_query", {"query": "SELECT count(*) FROM Log"})
    )
    assert payload["prepared_query"] == "SELECT count(*) FROM Log SINCE 30 MINUTES AGO LIMIT 200"


@respx.mock
async def test_search_logs_masks_credentials(server):
    respx.post(ENDPOINT).mock(
        return_value=nrql_response(
            [{"message": "auth failed for token NRAK-ABCDEFGHIJKLMNOPQRSTUVWX"}]
        )
    )
    body = await call(server, "search_logs", {"service_name": "checkout", "level": "ERROR"})
    assert "NRAK-ABCDEFGHIJKLMNOPQRSTUVWX" not in body
    assert "[REDACTED]" in body


@respx.mock
async def test_get_trace_groups_services(server):
    respx.post(ENDPOINT).mock(
        return_value=nrql_response([{"service.name": "checkout"}, {"service.name": "payments"}])
    )
    payload = json.loads(await call(server, "get_trace", {"trace_id": "abc123"}))
    assert payload["services"] == ["checkout", "payments"]


@respx.mock
async def test_list_open_issues_filters_activated(server):
    route = respx.post(ENDPOINT).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "actor": {
                        "account": {
                            "aiIssues": {
                                "issues": {
                                    "issues": [{"issueId": "i-1", "title": "High error rate"}],
                                    "nextCursor": None,
                                }
                            }
                        }
                    }
                }
            },
        )
    )
    payload = json.loads(await call(server, "list_open_issues", {}))

    sent = json.loads(route.calls.last.request.content)["variables"]
    assert sent["filter"] == {"states": ["ACTIVATED"]}
    assert payload["issues"][0]["issueId"] == "i-1"


@respx.mock
async def test_nerdgraph_errors_reach_the_client_with_their_message(server):
    respx.post(ENDPOINT).mock(
        return_value=httpx.Response(200, json={"errors": [{"message": "Not authorized"}]})
    )
    with pytest.raises(ToolError, match="Not authorized"):
        await server.call_tool("run_nrql", {"query": "SELECT count(*) FROM Log"})


async def test_invalid_nrql_is_reported_as_a_tool_error(server):
    with pytest.raises(ToolError, match="SELECT, FROM or SHOW"):
        await server.call_tool("run_nrql", {"query": "DELETE FROM Transaction"})


async def test_raw_tool_refuses_mutations_when_disabled(settings):
    enabled = settings.model_copy(update={"enable_raw_nerdgraph": True})
    with pytest.raises(ToolError, match="NEW_RELIC_ENABLE_MUTATIONS"):
        await create_server(enabled).call_tool(
            "nerdgraph_query", {"query": "mutation { alertsPolicyDelete(id: 1) { id } }"}
        )
