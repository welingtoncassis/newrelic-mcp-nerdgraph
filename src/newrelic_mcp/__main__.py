"""Command line entrypoint: ``newrelic-mcp``."""

from __future__ import annotations

import argparse
import logging
import sys

from pydantic import ValidationError

from .config import get_settings
from .server import create_server
from .version import __version__


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="newrelic-mcp",
        description="MCP server for New Relic, backed by NerdGraph and NRQL.",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "sse", "streamable-http"),
        default="stdio",
        help="MCP transport. Use stdio for local clients such as Cursor or Claude Desktop.",
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Logs go to stderr so they never corrupt the stdio protocol stream.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    logging.basicConfig(
        level=args.log_level,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        settings = get_settings()
    except ValidationError as exc:
        print(
            "Invalid configuration. NEW_RELIC_API_KEY is required, and every other "
            "NEW_RELIC_* variable is documented in the README.\n\n"
            f"{exc}",
            file=sys.stderr,
        )
        return 2

    create_server(settings).run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
