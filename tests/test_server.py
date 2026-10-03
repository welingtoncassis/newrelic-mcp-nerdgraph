from __future__ import annotations

from collections.abc import Iterable
from typing import cast

from mcp.server.lowlevel.helper_types import ReadResourceContents

from newrelic_mcp.server import create_server

EXPECTED_TOOLS = {
    "run_nrql",
    "run_nrql_async",
    "validate_nrql_query",
    "search_entities",
    "get_entity",
    "list_open_issues",
    "list_alert_policies",
    "list_nrql_conditions",
    "search_logs",
    "summarize_log_errors",
    "get_trace",
    "get_recent_errors",
    "list_deployments",
    "compare_metric_windows",
}


async def _tool_names(server):
    return {tool.name for tool in await server.list_tools()}


async def test_registers_the_documented_tools(settings):
    assert await _tool_names(create_server(settings)) == EXPECTED_TOOLS


async def test_raw_tool_is_opt_in(settings):
    assert "nerdgraph_query" not in await _tool_names(create_server(settings))

    enabled = settings.model_copy(update={"enable_raw_nerdgraph": True})
    assert "nerdgraph_query" in await _tool_names(create_server(enabled))


async def test_every_tool_is_described(settings):
    for tool in await create_server(settings).list_tools():
        assert tool.description, f"{tool.name} has no description"


async def test_resources_are_exposed(settings):
    uris = {str(resource.uri) for resource in await create_server(settings).list_resources()}
    assert "newrelic://nrql/cheatsheet" in uris
    assert "newrelic://playbook/investigation" in uris


async def test_config_resource_hides_the_api_key(settings):
    server = create_server(settings)
    contents = cast(
        "Iterable[ReadResourceContents]", await server.read_resource("newrelic://config")
    )
    body = str(next(iter(contents)).content)
    assert settings.api_key.get_secret_value() not in body
    assert "account_ids" in body
