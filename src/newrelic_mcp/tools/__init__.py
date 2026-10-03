"""Tool registration."""

from __future__ import annotations

from mcp.server.mcpserver import MCPServer

from . import alert_tools, entity_tools, log_tools, nrql_tools, raw_tools, trace_tools
from ._common import ContextProvider


def register_all(mcp: MCPServer, get_context: ContextProvider, *, enable_raw: bool) -> None:
    """Attach every enabled tool to ``mcp``."""
    nrql_tools.register(mcp, get_context)
    entity_tools.register(mcp, get_context)
    alert_tools.register(mcp, get_context)
    log_tools.register(mcp, get_context)
    trace_tools.register(mcp, get_context)
    if enable_raw:
        raw_tools.register(mcp, get_context)


__all__ = ["ContextProvider", "register_all"]
