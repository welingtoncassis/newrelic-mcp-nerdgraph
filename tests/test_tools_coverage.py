"""One call per remaining tool, asserting the NRQL or GraphQL actually sent."""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from mcp.server.mcpserver.exceptions import ToolError

from newrelic_mcp.server import create_server

from .helpers import ENDPOINT, call, graphql_response, nrql_response


@pytest.fixture
def server(settings):
    return create_server(settings)


def sent_nrql(route) -> str:
    return json.loads(route.calls.last.request.content)["variables"]["nrql"]


def alerts_response(payload: dict[str, object]) -> httpx.Response:
    return graphql_response({"actor": {"account": {"alerts": payload}}})


@respx.mock
async def test_get_recent_errors_facets_by_error_class(server):
    route = respx.post(ENDPOINT).mock(return_value=nrql_response([{"occurrences": 4}]))
    await call(server, "get_recent_errors", {"service_name": "checkout"})

    query = sent_nrql(route)
    assert "FROM TransactionError" in query
    assert "FACET `error.class`" in query
    assert "appName = 'checkout'" in query


@respx.mock
async def test_list_deployments_orders_newest_first(server):
    route = respx.post(ENDPOINT).mock(return_value=nrql_response([]))
    await call(server, "list_deployments", {"entity_guid": "GUID1"})

    query = sent_nrql(route)
    assert "FROM Deployment" in query
    assert "ORDER BY timestamp DESC" in query


@respx.mock
async def test_compare_metric_windows_adds_baseline(server):
    route = respx.post(ENDPOINT).mock(return_value=nrql_response([]))
    await call(
        server,
        "compare_metric_windows",
        {"nrql_select": "average(duration)", "event_type": "Transaction"},
    )
    assert "COMPARE WITH 1 DAY AGO" in sent_nrql(route)


@respx.mock
async def test_summarize_log_errors_filters_error_levels(server):
    route = respx.post(ENDPOINT).mock(return_value=nrql_response([]))
    await call(server, "summarize_log_errors", {"service_name": "checkout"})

    query = sent_nrql(route)
    assert "`level` IN ('ERROR', 'FATAL', 'CRITICAL')" in query
    assert "FACET substring(message, 0, 120)" in query


@respx.mock
async def test_search_entities_tool_returns_entities(server):
    respx.post(ENDPOINT).mock(
        return_value=graphql_response(
            {
                "actor": {
                    "entitySearch": {
                        "count": 1,
                        "results": {
                            "entities": [{"guid": "GUID1", "name": "checkout"}],
                            "nextCursor": None,
                        },
                    }
                }
            }
        )
    )
    payload = json.loads(await call(server, "search_entities", {"name": "checkout"}))
    assert payload["entities"][0]["name"] == "checkout"


@respx.mock
async def test_get_entity_tool_returns_entity(server):
    respx.post(ENDPOINT).mock(
        return_value=graphql_response({"actor": {"entity": {"guid": "GUID1", "name": "checkout"}}})
    )
    payload = json.loads(await call(server, "get_entity", {"guid": "GUID1"}))
    assert payload["guid"] == "GUID1"


@respx.mock
async def test_missing_entity_is_a_tool_error(server):
    respx.post(ENDPOINT).mock(return_value=graphql_response({"actor": {}}))
    with pytest.raises(ToolError, match="was not found"):
        await server.call_tool("get_entity", {"guid": "missing"})


@respx.mock
async def test_list_alert_policies_tool(server):
    respx.post(ENDPOINT).mock(
        return_value=alerts_response(
            {"policiesSearch": {"policies": [{"id": "1", "name": "checkout"}], "nextCursor": None}}
        )
    )
    payload = json.loads(await call(server, "list_alert_policies", {}))
    assert payload["policies"][0]["name"] == "checkout"


@respx.mock
async def test_list_nrql_conditions_tool(server):
    respx.post(ENDPOINT).mock(
        return_value=alerts_response(
            {
                "nrqlConditionsSearch": {
                    "nrqlConditions": [{"id": "9", "name": "error rate"}],
                    "nextCursor": None,
                }
            }
        )
    )
    payload = json.loads(await call(server, "list_nrql_conditions", {"policy_id": "1"}))
    assert payload["conditions"][0]["id"] == "9"


@respx.mock
async def test_async_nrql_polls_until_complete(server):
    respx.post(ENDPOINT).mock(
        side_effect=[
            graphql_response(
                {
                    "actor": {
                        "nrql": {
                            "queryProgress": {
                                "queryId": "q-1",
                                "completed": False,
                                "retryAfter": 0,
                            }
                        }
                    }
                }
            ),
            graphql_response(
                {
                    "actor": {
                        "nrqlQueryProgress": {
                            "queryProgress": {"queryId": "q-1", "completed": True},
                            "results": [{"count": 42}],
                        }
                    }
                }
            ),
        ]
    )
    payload = json.loads(
        await call(server, "run_nrql_async", {"query": "SELECT count(*) FROM Log"})
    )
    assert payload["results"] == [{"count": 42}]
    assert payload["polls"] == 1


@respx.mock
async def test_raw_tool_passes_read_queries_through(settings):
    enabled = settings.model_copy(update={"enable_raw_nerdgraph": True})
    respx.post(ENDPOINT).mock(return_value=graphql_response({"actor": {"user": {"name": "ana"}}}))
    payload = json.loads(
        await call(
            create_server(enabled), "nerdgraph_query", {"query": "{ actor { user { name } } }"}
        )
    )
    assert payload["data"]["actor"]["user"]["name"] == "ana"
