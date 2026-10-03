"""Shared plumbing for tool modules."""

from __future__ import annotations

import functools
from collections.abc import Awaitable, Callable
from typing import ParamSpec, TypeVar

from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations

from ..context import AppContext
from ..errors import NewRelicMCPError

ContextProvider = Callable[[], AppContext]

P = ParamSpec("P")
R = TypeVar("R")

READ_ONLY = ToolAnnotations(
    read_only_hint=True,
    destructive_hint=False,
    idempotent_hint=True,
    open_world_hint=True,
)
"""Annotations for tools that only read from New Relic.

Clients use these hints to decide whether a call needs user confirmation, so
every tool here declares them rather than relying on the default.
"""


def tool_errors(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    """Translate known failures into ``ToolError``.

    The SDK only forwards the message of a ``ToolError`` to the client; any
    other exception is reported as a generic crash. Our failures are actionable
    ("that NRQL is invalid", "no account configured"), so the agent needs to
    read them to correct itself.
    """

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return await func(*args, **kwargs)
        except (NewRelicMCPError, ValueError) as exc:
            raise ToolError(str(exc)) from exc

    return wrapper
