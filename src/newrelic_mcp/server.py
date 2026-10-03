"""MCP server definition: tools, resources and prompts."""

from __future__ import annotations

import logging
from importlib import resources as importlib_resources

from mcp.server.mcpserver import MCPServer

from .config import Settings, get_settings
from .context import AppContext, build_context
from .tools import register_all
from .version import __version__

logger = logging.getLogger(__name__)

INSTRUCTIONS = """\
This server exposes New Relic observability data through NerdGraph and NRQL.

Start from a dedicated tool when one fits the question (search_logs, get_trace,
get_recent_errors, list_open_issues) and fall back to run_nrql for anything
else. Read the `newrelic://playbook/investigation` resource before a multi-step
incident investigation, and `newrelic://nrql/cheatsheet` when writing NRQL.

All tools are read-only unless the operator enabled mutations explicitly.
"""


def _read_resource(filename: str) -> str:
    return importlib_resources.files("newrelic_mcp.resources").joinpath(filename).read_text("utf-8")


def create_server(settings: Settings | None = None) -> MCPServer:
    """Build the MCP server.

    The context is created lazily on first tool call so that importing this
    module never requires an API key, which keeps tests and ``--help`` cheap.
    """
    resolved = settings or get_settings()
    mcp = MCPServer(
        "newrelic-mcp-nerdgraph",
        title="New Relic (NerdGraph)",
        version=__version__,
        instructions=INSTRUCTIONS,
    )

    context: AppContext | None = None

    def get_context() -> AppContext:
        nonlocal context
        if context is None:
            context = build_context(resolved)
        return context

    register_all(mcp, get_context, enable_raw=resolved.enable_raw_nerdgraph)

    @mcp.resource("newrelic://nrql/cheatsheet", mime_type="text/markdown")
    def nrql_cheatsheet() -> str:
        """NRQL syntax, common event types and query patterns."""
        return _read_resource("nrql_cheatsheet.md")

    @mcp.resource("newrelic://playbook/investigation", mime_type="text/markdown")
    def investigation_playbook() -> str:
        """Step-by-step incident investigation flow using this server's tools."""
        return _read_resource("investigation_playbook.md")

    @mcp.resource("newrelic://config", mime_type="application/json")
    def server_config() -> str:
        """Non-sensitive view of the active configuration."""
        return resolved.model_dump_json(exclude={"api_key"}, indent=2)

    @mcp.prompt()
    def investigate_incident(
        subject: str,
        time_window: str = "1 HOUR AGO",
    ) -> str:
        """Guide an end-to-end investigation of an alert, service or trace id."""
        return (
            f"Investigate '{subject}' in New Relic over the window SINCE {time_window}.\n\n"
            "Follow the newrelic://playbook/investigation resource. For each step, state "
            "the tool you used and what it showed. Finish with: blast radius, first "
            "symptom timestamp, the most likely cause, and the evidence that supports it. "
            "If a step returns no data, say so instead of inferring a cause from its absence."
        )

    @mcp.prompt()
    def write_nrql(question: str) -> str:
        """Turn a plain-language question into a validated NRQL query."""
        return (
            f"Write a NRQL query that answers: {question}\n\n"
            "Consult the newrelic://nrql/cheatsheet resource for event types and syntax. "
            "Check the query with validate_nrql_query first, then run it with run_nrql and "
            "explain what the result shows."
        )

    return mcp
