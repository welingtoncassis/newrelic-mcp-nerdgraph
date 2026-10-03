"""Tools for searching logs."""

from __future__ import annotations

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from ..formatting import finalize
from ._common import READ_ONLY, ContextProvider, tool_errors


def register(mcp: MCPServer, get_context: ContextProvider) -> None:
    @mcp.tool(annotations=READ_ONLY)
    @tool_errors
    async def search_logs(
        service_name: Annotated[
            str | None,
            Field(
                default=None, description="Matched against service.name, entity.name, faas.name."
            ),
        ] = None,
        entity_guid: Annotated[str | None, Field(default=None)] = None,
        level: Annotated[
            str | None,
            Field(default=None, description="ERROR, WARN, INFO, DEBUG."),
        ] = None,
        trace_id: Annotated[
            str | None,
            Field(default=None, description="Correlate logs with one distributed trace."),
        ] = None,
        message_contains: Annotated[
            str | None,
            Field(default=None, description="Substring match on the log message."),
        ] = None,
        since: Annotated[
            str | None,
            Field(default=None, description="NRQL time window, e.g. '30 MINUTES AGO'."),
        ] = None,
        limit: Annotated[int, Field(default=50, ge=1, le=500)] = 50,
        account_ids: Annotated[list[int] | None, Field(default=None)] = None,
    ) -> str:
        """Search logs by service, level, trace id or message content.

        Returns the newest matches first. Credential-shaped values in log
        messages are masked before the result leaves the server.
        """
        ctx = get_context()
        result = await ctx.logs.search(
            account_ids=account_ids,
            service_name=service_name,
            entity_guid=entity_guid,
            level=level,
            trace_id=trace_id,
            message_contains=message_contains,
            since=since,
            limit=limit,
        )
        return finalize(result, ctx.settings)

    @mcp.tool(annotations=READ_ONLY)
    @tool_errors
    async def summarize_log_errors(
        service_name: Annotated[str | None, Field(default=None)] = None,
        since: Annotated[str, Field(default="1 HOUR AGO")] = "1 HOUR AGO",
        limit: Annotated[int, Field(default=20, ge=1, le=100)] = 20,
        account_ids: Annotated[list[int] | None, Field(default=None)] = None,
    ) -> str:
        """Group error logs by message pattern to show what is failing most.

        Prefer this over search_logs when the question is "what is broken"
        rather than "show me this specific request".
        """
        ctx = get_context()
        query = ctx.logs.build_summary_query(service_name=service_name, since=since, limit=limit)
        result = await ctx.nrql.run(query, account_ids=account_ids)
        return finalize(result, ctx.settings)
