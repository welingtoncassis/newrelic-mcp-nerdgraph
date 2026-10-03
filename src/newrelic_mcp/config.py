"""Runtime configuration, loaded from environment variables."""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Region(str, Enum):
    """New Relic data region. Determines the NerdGraph endpoint."""

    US = "US"
    EU = "EU"

    @property
    def nerdgraph_endpoint(self) -> str:
        return {
            Region.US: "https://api.newrelic.com/graphql",
            Region.EU: "https://api.eu.newrelic.com/graphql",
        }[self]

    @property
    def ui_base_url(self) -> str:
        return {
            Region.US: "https://one.newrelic.com",
            Region.EU: "https://one.eu.newrelic.com",
        }[self]


class Settings(BaseSettings):
    """Server settings.

    Every field maps to a ``NEW_RELIC_``-prefixed environment variable, e.g.
    ``NEW_RELIC_API_KEY``. The API key is a :class:`~pydantic.SecretStr` so it is
    never rendered by accident in logs, tracebacks or tool payloads.
    """

    model_config = SettingsConfigDict(
        env_prefix="NEW_RELIC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        frozen=True,
    )

    api_key: SecretStr = Field(description="New Relic User API key (NRAK-...).")
    account_ids: list[int] = Field(
        default_factory=list,
        description="Accounts queried when a tool call omits them. First entry is the default.",
    )
    region: Region = Region.US

    query_timeout_seconds: int = Field(default=30, ge=1, le=120)
    http_timeout_seconds: float = Field(default=35.0, gt=0)
    max_retries: int = Field(default=3, ge=0, le=10)

    default_since: str = Field(
        default="30 MINUTES AGO",
        description="SINCE clause appended to NRQL that does not define its own time window.",
    )
    max_result_rows: int = Field(default=200, ge=1, le=5000)
    max_response_chars: int = Field(
        default=100_000,
        ge=1_000,
        description="Tool payloads larger than this are truncated before reaching the model.",
    )

    enable_mutations: bool = Field(
        default=False,
        description="Opt-in flag for tools that change New Relic configuration.",
    )
    enable_raw_nerdgraph: bool = Field(
        default=False,
        description="Opt-in flag for the escape-hatch tool that runs arbitrary GraphQL.",
    )
    redact_sensitive_values: bool = Field(
        default=True,
        description="Mask token- and credential-looking strings in tool output.",
    )

    @field_validator("account_ids", mode="before")
    @classmethod
    def _split_account_ids(cls, value: object) -> object:
        """Accept the shapes people actually write in an env file.

        ``NEW_RELIC_ACCOUNT_IDS=123,456`` reaches here as a string, but a single
        ``=123`` is JSON-decoded to an int by pydantic-settings before the field
        is validated, so both have to be wrapped into a list.
        """
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        if isinstance(value, int):
            return [value]
        return value

    @property
    def default_account_id(self) -> int | None:
        return self.account_ids[0] if self.account_ids else None

    def resolve_accounts(self, requested: list[int] | None) -> list[int]:
        """Pick the accounts for a query, falling back to the configured defaults."""
        accounts = requested or self.account_ids
        if not accounts:
            raise ValueError(
                "No account id provided and NEW_RELIC_ACCOUNT_IDS is not set. "
                "Pass account_ids explicitly or configure a default."
            )
        if len(accounts) > 30:
            raise ValueError("NerdGraph allows at most 30 accounts per cross-account query.")
        return accounts


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the process-wide settings, loaded once."""
    return Settings()  # type: ignore[call-arg]  # values come from the environment
