"""Exception hierarchy surfaced to MCP clients."""

from __future__ import annotations


class NewRelicMCPError(Exception):
    """Base class for every error raised by this server."""


class ConfigurationError(NewRelicMCPError):
    """Missing or invalid configuration, such as an absent API key."""


class NerdGraphError(NewRelicMCPError):
    """NerdGraph answered with GraphQL-level errors."""

    def __init__(self, message: str, errors: list[dict[str, object]] | None = None) -> None:
        super().__init__(message)
        self.errors = errors or []


class NerdGraphHTTPError(NewRelicMCPError):
    """NerdGraph answered with a non-success HTTP status."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"NerdGraph HTTP {status_code}: {message}")
        self.status_code = status_code


class NrqlValidationError(NewRelicMCPError):
    """The supplied NRQL was rejected before being sent to New Relic."""


class MutationsDisabledError(NewRelicMCPError):
    """A write tool was called while mutations are disabled."""

    def __init__(self) -> None:
        super().__init__(
            "Mutating tools are disabled. Set NEW_RELIC_ENABLE_MUTATIONS=true to allow them."
        )
