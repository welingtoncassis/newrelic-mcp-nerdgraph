"""Distributed traces, error analysis and deployment correlation.

All of these are NRQL over the ``Span``, ``TransactionError`` and
``Deployment`` event types rather than dedicated NerdGraph fields, which keeps
them usable with a plain User API key.
"""

from __future__ import annotations

from typing import Any

from ..config import Settings
from ..security.nrql_guard import escape_nrql_string
from .nrql import NrqlService


class TraceService:
    """Trace lookup and error/deployment correlation helpers."""

    def __init__(self, nrql: NrqlService, settings: Settings) -> None:
        self._nrql = nrql
        self._settings = settings

    async def get_trace(
        self,
        trace_id: str,
        *,
        account_ids: list[int] | None = None,
        since: str = "3 HOURS AGO",
        limit: int = 200,
    ) -> dict[str, Any]:
        """Return the spans of one trace, ordered by start time."""
        escaped = escape_nrql_string(trace_id)
        query = (
            "SELECT timestamp, `name`, `service.name`, `duration.ms`, `span.kind`, "
            "`parent.id`, `id`, `otel.status_code`, `error.message` "
            f"FROM Span WHERE `trace.id` = '{escaped}' "
            f"SINCE {since} ORDER BY timestamp ASC LIMIT {limit}"
        )
        result = await self._nrql.run(query, account_ids=account_ids)
        spans = result["results"]
        result["span_count"] = len(spans)
        result["services"] = sorted(
            {str(span.get("service.name")) for span in spans if span.get("service.name")}
        )
        return result

    async def recent_errors(
        self,
        *,
        service_name: str | None = None,
        account_ids: list[int] | None = None,
        since: str = "1 HOUR AGO",
        limit: int = 20,
    ) -> dict[str, Any]:
        """Group recent transaction errors by class and message."""
        where = ""
        if service_name:
            where = f"WHERE appName = '{escape_nrql_string(service_name)}' "
        query = (
            "SELECT count(*) AS occurrences, latest(error.message) AS sample_message, "
            "latest(transactionName) AS transaction "
            f"FROM TransactionError {where}"
            f"FACET `error.class` SINCE {since} LIMIT {limit}"
        )
        return await self._nrql.run(query, account_ids=account_ids)

    async def deployments(
        self,
        *,
        entity_guid: str | None = None,
        account_ids: list[int] | None = None,
        since: str = "7 DAYS AGO",
        limit: int = 50,
    ) -> dict[str, Any]:
        """List recent deployments and change-tracking events."""
        where = ""
        if entity_guid:
            where = f"WHERE entity.guid = '{escape_nrql_string(entity_guid)}' "
        query = (
            "SELECT timestamp, entity.name, version, user, description, commit "
            f"FROM Deployment {where}"
            f"SINCE {since} ORDER BY timestamp DESC LIMIT {limit}"
        )
        return await self._nrql.run(query, account_ids=account_ids)

    async def compare_window(
        self,
        *,
        nrql_select: str,
        event_type: str,
        where: str | None = None,
        account_ids: list[int] | None = None,
        since: str = "1 HOUR AGO",
        compare_with: str = "1 DAY AGO",
    ) -> dict[str, Any]:
        """Compare an aggregate against the same window in the past.

        Useful right after a deploy: the second series is the baseline, so a
        regression shows up as a difference rather than an absolute number the
        model has to judge on its own.
        """
        clause = f"WHERE {where} " if where else ""
        query = (
            f"SELECT {nrql_select} FROM {event_type} {clause}"
            f"SINCE {since} COMPARE WITH {compare_with}"
        )
        return await self._nrql.run(query, account_ids=account_ids)
