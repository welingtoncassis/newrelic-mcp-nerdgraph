"""Escape hatch for GraphQL that no curated tool covers.

Disabled by default. When enabled it still refuses ``mutation`` documents
unless mutations have been explicitly turned on, so the common case stays
read-only even for an operator who wanted raw access.
"""

from __future__ import annotations

import re
from typing import Annotated, Any

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations
from pydantic import Field

from ..errors import MutationsDisabledError
from ..formatting import finalize
from ._common import ContextProvider, tool_errors

_MUTATION = re.compile(r"^\s*mutation\b", re.IGNORECASE)

# Deliberately not marked read-only: the document is caller-supplied, so the
# client should treat the call as potentially writing.
_RAW_ANNOTATIONS = ToolAnnotations(
    read_only_hint=False,
    destructive_hint=True,
    open_world_hint=True,
)


def register(mcp: MCPServer, get_context: ContextProvider) -> None:
    @mcp.tool(annotations=_RAW_ANNOTATIONS)
    @tool_errors
    async def nerdgraph_query(
        query: Annotated[str, Field(description="A GraphQL document for NerdGraph.")],
        variables: Annotated[dict[str, Any] | None, Field(default=None)] = None,
    ) -> str:
        """Run an arbitrary NerdGraph GraphQL document.

        Only use this when no dedicated tool exposes the field you need; the
        curated tools return smaller, more predictable payloads.
        """
        ctx = get_context()
        if _MUTATION.match(query) and not ctx.settings.enable_mutations:
            raise MutationsDisabledError
        data = await ctx.client.execute(query, variables)
        return finalize({"data": data}, ctx.settings)
