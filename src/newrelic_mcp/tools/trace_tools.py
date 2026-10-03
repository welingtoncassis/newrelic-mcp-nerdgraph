"""Tools for traces, errors and deployment correlation."""

from __future__ import annotations

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from ..formatting import finalize
from ._common import READ_ONLY, ContextProvider, tool_errors


def register(mcp: MCPServer, get_context: ContextProvider) -> None:
    @mcp.tool(annotations=READ_ONLY)
    @tool_errors
    async def get_trace(
        trace_id: Annotated[str, Field(description="Distributed trace id.")],
        since: Annotated[str, Field(default="3 HOURS AGO")] = "3 HOURS AGO",
        limit: Annotated[int, Field(default=200, ge=1, le=1000)] = 200,
        account_ids: Annotated[list[int] | None, Field(default=None)] = None,
    ) -> str:
        """Get the spans of one distributed trace, in chronological order.

        Pair this with search_logs on the same trace_id to see the request path
        and its log lines together.
        """
        ctx = get_context()
        result = await ctx.traces.get_trace(
            trace_id, account_ids=account_ids, since=since, limit=limit
        )
        return finalize(result, ctx.settings)

    @mcp.tool(annotations=READ_ONLY)
    @tool_errors
    async def get_recent_errors(
        service_name: Annotated[
            str | None,
            Field(default=None, description="APM application name."),
        ] = None,
        since: Annotated[str, Field(default="1 HOUR AGO")] = "1 HOUR AGO",
        limit: Annotated[int, Field(default=20, ge=1, le=100)] = 20,
        account_ids: Annotated[list[int] | None, Field(default=None)] = None,
    ) -> str:
        """Show recent transaction errors grouped by error class."""
        ctx = get_context()
        result = await ctx.traces.recent_errors(
            service_name=service_name, account_ids=account_ids, since=since, limit=limit
        )
        return finalize(result, ctx.settings)

    @mcp.tool(annotations=READ_ONLY)
    @tool_errors
    async def list_deployments(
        entity_guid: Annotated[str | None, Field(default=None)] = None,
        since: Annotated[str, Field(default="7 DAYS AGO")] = "7 DAYS AGO",
        limit: Annotated[int, Field(default=50, ge=1, le=200)] = 50,
        account_ids: Annotated[list[int] | None, Field(default=None)] = None,
    ) -> str:
        """List recent deployments, newest first.

        Use this to check whether an incident lines up with a release before
        digging into traces.
        """
        ctx = get_context()
        result = await ctx.traces.deployments(
            entity_guid=entity_guid, account_ids=account_ids, since=since, limit=limit
        )
        return finalize(result, ctx.settings)

    @mcp.tool(annotations=READ_ONLY)
    @tool_errors
    async def compare_metric_windows(
        nrql_select: Annotated[
            str,
            Field(
                description=(
                    "Aggregations only, e.g. 'percentile(duration, 95)' or "
                    "'rate(count(*), 1 minute)'."
                )
            ),
        ],
        event_type: Annotated[str, Field(description="Event type, e.g. Transaction or Metric.")],
        where: Annotated[str | None, Field(default=None, description="WHERE clause body.")] = None,
        since: Annotated[str, Field(default="1 HOUR AGO")] = "1 HOUR AGO",
        compare_with: Annotated[str, Field(default="1 DAY AGO")] = "1 DAY AGO",
        account_ids: Annotated[list[int] | None, Field(default=None)] = None,
    ) -> str:
        """Compare an aggregate against the same window in the past.

        The baseline makes a regression visible as a delta, which is usually
        more conclusive than an absolute value taken on its own.
        """
        ctx = get_context()
        result = await ctx.traces.compare_window(
            nrql_select=nrql_select,
            event_type=event_type,
            where=where,
            account_ids=account_ids,
            since=since,
            compare_with=compare_with,
        )
        return finalize(result, ctx.settings)
