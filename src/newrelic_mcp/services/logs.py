"""Log search expressed as generated NRQL.

New Relic has no dedicated log API in NerdGraph; logs live in the ``Log`` event
type. This service builds the NRQL so callers never interpolate raw user input
into a query string themselves.
"""

from __future__ import annotations

from typing import Any

from ..config import Settings
from ..security.nrql_guard import escape_nrql_string
from .nrql import NrqlService

_DEFAULT_ATTRIBUTES = (
    "timestamp",
    "level",
    "message",
    "entity.name",
    "service.name",
    "trace.id",
    "span.id",
    "error.message",
)


class LogService:
    """Builds and runs log queries."""

    def __init__(self, nrql: NrqlService, settings: Settings) -> None:
        self._nrql = nrql
        self._settings = settings

    def build_query(
        self,
        *,
        service_name: str | None = None,
        entity_guid: str | None = None,
        level: str | None = None,
        trace_id: str | None = None,
        message_contains: str | None = None,
        extra_where: str | None = None,
        since: str | None = None,
        limit: int = 50,
        attributes: tuple[str, ...] = _DEFAULT_ATTRIBUTES,
    ) -> str:
        selected = ", ".join(f"`{attr}`" for attr in attributes)
        clauses: list[str] = []
        if service_name:
            escaped = escape_nrql_string(service_name)
            clauses.append(
                f"(`service.name` = '{escaped}' OR `entity.name` = '{escaped}' "
                f"OR `faas.name` = '{escaped}')"
            )
        if entity_guid:
            clauses.append(f"`entity.guid` = '{escape_nrql_string(entity_guid)}'")
        if level:
            clauses.append(f"`level` = '{escape_nrql_string(level.upper())}'")
        if trace_id:
            clauses.append(f"`trace.id` = '{escape_nrql_string(trace_id)}'")
        if message_contains:
            clauses.append(f"`message` LIKE '%{escape_nrql_string(message_contains)}%'")
        if extra_where:
            clauses.append(f"({extra_where})")

        query = f"SELECT {selected} FROM Log"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += f" SINCE {since or self._settings.default_since}"
        return f"{query} ORDER BY timestamp DESC LIMIT {limit}"

    def build_summary_query(
        self,
        *,
        service_name: str | None = None,
        since: str = "1 HOUR AGO",
        limit: int = 20,
    ) -> str:
        """Build a query that groups error logs by their coarse message pattern.

        Faceting on the first 120 characters collapses messages that differ only
        by ids or payload, which is what makes the result readable.
        """
        clauses = ["`level` IN ('ERROR', 'FATAL', 'CRITICAL')"]
        if service_name:
            escaped = escape_nrql_string(service_name)
            clauses.append(
                f"(`service.name` = '{escaped}' OR `entity.name` = '{escaped}' "
                f"OR `faas.name` = '{escaped}')"
            )
        return (
            "SELECT count(*) AS occurrences, latest(message) AS sample, "
            "latest(`trace.id`) AS sample_trace_id "
            f"FROM Log WHERE {' AND '.join(clauses)} "
            f"FACET substring(message, 0, 120) SINCE {since} LIMIT {limit}"
        )

    async def search(
        self,
        *,
        account_ids: list[int] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Run a log search and return the matching lines, newest first."""
        query = self.build_query(**kwargs)
        return await self._nrql.run(query, account_ids=account_ids)
