"""Shared helpers for the test suite."""

from __future__ import annotations

from typing import Any

import httpx

from newrelic_mcp.config import Region

ENDPOINT = Region.US.nerdgraph_endpoint


def nrql_response(results: list[dict[str, Any]]) -> httpx.Response:
    """A NerdGraph response shaped like a successful NRQL query."""
    return httpx.Response(
        200, json={"data": {"actor": {"nrql": {"results": results, "metadata": {}}}}}
    )


def graphql_response(data: dict[str, Any]) -> httpx.Response:
    return httpx.Response(200, json={"data": data})


async def call(server: Any, name: str, arguments: dict[str, Any]) -> str:
    """Call a tool and return its text content."""
    result = await server.call_tool(name, arguments)
    assert not result.is_error, result.content
    return "".join(block.text for block in result.content if block.type == "text")
