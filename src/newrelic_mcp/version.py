"""Package version, kept in its own module so importing it cannot cycle."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("newrelic-mcp-nerdgraph")
except PackageNotFoundError:  # running from a source checkout
    __version__ = "0.0.0.dev0"

__all__ = ["__version__"]
