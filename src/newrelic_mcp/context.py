"""Composition root wiring settings, the HTTP client and the services."""

from __future__ import annotations

from dataclasses import dataclass
from types import TracebackType

import httpx

from .config import Settings, get_settings
from .nerdgraph.client import NerdGraphClient
from .services import AlertService, EntityService, LogService, NrqlService, TraceService


@dataclass(frozen=True)
class AppContext:
    """Everything a tool needs, assembled once per server process."""

    settings: Settings
    client: NerdGraphClient
    nrql: NrqlService
    entities: EntityService
    alerts: AlertService
    logs: LogService
    traces: TraceService

    async def __aenter__(self) -> AppContext:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.client.aclose()

    def account_or_default(self, account_id: int | None) -> int:
        """Resolve a single account id, falling back to the configured default."""
        return self.settings.resolve_accounts([account_id] if account_id else None)[0]


def build_context(
    settings: Settings | None = None,
    *,
    http_client: httpx.AsyncClient | None = None,
) -> AppContext:
    """Create an :class:`AppContext`.

    Tests pass an ``http_client`` backed by a transport mock; production leaves
    it as ``None`` so the NerdGraph client owns its own connection pool.
    """
    resolved = settings or get_settings()
    client = NerdGraphClient(resolved, client=http_client)
    nrql = NrqlService(client, resolved)
    return AppContext(
        settings=resolved,
        client=client,
        nrql=nrql,
        entities=EntityService(client),
        alerts=AlertService(client),
        logs=LogService(nrql, resolved),
        traces=TraceService(nrql, resolved),
    )
