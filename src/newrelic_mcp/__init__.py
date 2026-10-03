"""Open source MCP server for New Relic, built on NerdGraph and NRQL."""

from __future__ import annotations

from .config import Region, Settings, get_settings
from .server import create_server
from .version import __version__

__all__ = ["Region", "Settings", "__version__", "create_server", "get_settings"]
