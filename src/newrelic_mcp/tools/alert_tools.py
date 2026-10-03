"""Tools covering alert policies, conditions and open issues."""

from __future__ import annotations

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from ..formatting import finalize
from ._common import READ_ONLY, ContextProvider, tool_errors


def register(mcp: MCPServer, get_context: ContextProvider) -> None:
    @mcp.tool(annotations=READ_ONLY)
    @tool_errors
    async def list_open_issues(
        account_id: Annotated[int | None, Field(default=None)] = None,
        only_open: Annotated[
            bool,
            Field(default=True, description="Set to false to include closed issues."),
        ] = True,
        priority: Annotated[
            str | None,
            Field(default=None, description="CRITICAL, HIGH, MEDIUM or LOW."),
        ] = None,
        cursor: Annotated[str | None, Field(default=None)] = None,
    ) -> str:
        """List alert issues, by default the ones currently active.

        Each issue carries the entity GUIDs involved, which is the usual entry
        point for an on-call investigation.
        """
        ctx = get_context()
        result = await ctx.alerts.list_issues(
            ctx.account_or_default(account_id),
            only_open=only_open,
            priority=priority,
            cursor=cursor,
        )
        return finalize(result, ctx.settings)

    @mcp.tool(annotations=READ_ONLY)
    @tool_errors
    async def list_alert_policies(
        account_id: Annotated[int | None, Field(default=None)] = None,
        cursor: Annotated[str | None, Field(default=None)] = None,
    ) -> str:
        """List alert policies for an account."""
        ctx = get_context()
        result = await ctx.alerts.list_policies(ctx.account_or_default(account_id), cursor=cursor)
        return finalize(result, ctx.settings)

    @mcp.tool(annotations=READ_ONLY)
    @tool_errors
    async def list_nrql_conditions(
        account_id: Annotated[int | None, Field(default=None)] = None,
        policy_id: Annotated[
            str | None,
            Field(default=None, description="Restrict to one policy."),
        ] = None,
        cursor: Annotated[str | None, Field(default=None)] = None,
    ) -> str:
        """List NRQL alert conditions, including their queries and thresholds.

        Reading the condition's own NRQL is the fastest way to reproduce what
        an alert saw at the time it fired.
        """
        ctx = get_context()
        result = await ctx.alerts.list_nrql_conditions(
            ctx.account_or_default(account_id), policy_id=policy_id, cursor=cursor
        )
        return finalize(result, ctx.settings)
