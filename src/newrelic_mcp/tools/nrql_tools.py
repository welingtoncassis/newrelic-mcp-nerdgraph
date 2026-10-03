"""Tools that run NRQL directly."""

from __future__ import annotations

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from ..errors import NewRelicMCPError
from ..formatting import finalize
from ._common import READ_ONLY, ContextProvider, tool_errors


def register(mcp: MCPServer, get_context: ContextProvider) -> None:
    @mcp.tool(annotations=READ_ONLY)
    @tool_errors
    async def run_nrql(
        query: Annotated[
            str,
            Field(description="NRQL query. SINCE and LIMIT are added when absent."),
        ],
        account_ids: Annotated[
            list[int] | None,
            Field(default=None, description="Accounts to query. Defaults to the configured ones."),
        ] = None,
        timeout_seconds: Annotated[
            int | None,
            Field(default=None, ge=1, le=120, description="Server-side NRQL timeout."),
        ] = None,
    ) -> str:
        """Run a NRQL query against one or more New Relic accounts.

        This is the general-purpose data tool: anything stored as events,
        metrics, logs or spans can be reached from here. Prefer the dedicated
        tools (search_logs, get_trace, get_recent_errors) when they fit, because
        they return a shape tuned for that use case.
        """
        ctx = get_context()
        result = await ctx.nrql.run(query, account_ids=account_ids, timeout_seconds=timeout_seconds)
        return finalize(result, ctx.settings)

    @mcp.tool(annotations=READ_ONLY)
    @tool_errors
    async def run_nrql_async(
        query: Annotated[str, Field(description="Long-running NRQL query.")],
        account_ids: Annotated[list[int] | None, Field(default=None)] = None,
    ) -> str:
        """Run a NRQL query that exceeds the synchronous timeout, polling until it finishes.

        Use this for wide time windows (days or weeks) or heavy aggregations.
        It is slower than run_nrql, so it is not the default choice.
        """
        ctx = get_context()
        result = await ctx.nrql.run_async_query(query, account_ids=account_ids)
        return finalize(result, ctx.settings)

    @mcp.tool(annotations=READ_ONLY)
    @tool_errors
    async def validate_nrql_query(
        query: Annotated[str, Field(description="NRQL to check without executing it.")],
    ) -> str:
        """Check a NRQL query against the server guardrails without running it.

        Returns the query as it would actually be sent, including the SINCE and
        LIMIT clauses that get appended automatically.
        """
        ctx = get_context()
        try:
            prepared = ctx.nrql.prepare(query)
        except NewRelicMCPError as exc:
            return finalize({"valid": False, "reason": str(exc)}, ctx.settings)
        return finalize({"valid": True, "prepared_query": prepared}, ctx.settings)
