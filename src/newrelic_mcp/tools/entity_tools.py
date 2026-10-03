"""Tools for discovering and inspecting monitored entities."""

from __future__ import annotations

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

from ..formatting import finalize
from ._common import READ_ONLY, ContextProvider, tool_errors


def register(mcp: MCPServer, get_context: ContextProvider) -> None:
    @mcp.tool(annotations=READ_ONLY)
    @tool_errors
    async def search_entities(
        name: Annotated[
            str | None,
            Field(default=None, description="Name fragment; matched with LIKE."),
        ] = None,
        domain: Annotated[
            str | None,
            Field(default=None, description="APM, BROWSER, INFRA, SYNTH, MOBILE, EXT."),
        ] = None,
        entity_type: Annotated[
            str | None,
            Field(default=None, description="APPLICATION, HOST, CONTAINER, AWSLAMBDAFUNCTION..."),
        ] = None,
        account_id: Annotated[int | None, Field(default=None)] = None,
        tags: Annotated[
            dict[str, str] | None,
            Field(default=None, description="Exact tag matches, e.g. {'env': 'production'}."),
        ] = None,
        cursor: Annotated[str | None, Field(default=None, description="Pagination cursor.")] = None,
    ) -> str:
        """Find entities (services, hosts, lambdas, browsers) by name, type or tag.

        Start here when you only know a service name: the returned GUID is the
        key for get_entity, logs and alert lookups.
        """
        ctx = get_context()
        result = await ctx.entities.search(
            name=name,
            domain=domain,
            entity_type=entity_type,
            account_id=account_id,
            tags=tags,
            cursor=cursor,
        )
        return finalize(result, ctx.settings)

    @mcp.tool(annotations=READ_ONLY)
    @tool_errors
    async def get_entity(
        guid: Annotated[str, Field(description="Entity GUID returned by search_entities.")],
    ) -> str:
        """Get one entity with its tags, golden metrics and relationships.

        The golden metrics include the NRQL New Relic itself uses for that
        entity type, which you can run as-is through run_nrql.
        """
        ctx = get_context()
        result = await ctx.entities.get(guid)
        return finalize(result, ctx.settings)
