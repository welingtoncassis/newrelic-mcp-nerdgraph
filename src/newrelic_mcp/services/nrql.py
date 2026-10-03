"""NRQL execution, including the asynchronous long-running query flow."""

from __future__ import annotations

import asyncio
from typing import Any

from ..config import Settings
from ..errors import NerdGraphError
from ..nerdgraph.client import NerdGraphClient
from ..nerdgraph.queries import NRQL_QUERY, NRQL_QUERY_ASYNC_POLL, NRQL_QUERY_ASYNC_START
from ..security.nrql_guard import apply_defaults, validate_nrql

_MAX_POLL_ATTEMPTS = 20


class NrqlService:
    """Runs NRQL against one or many accounts."""

    def __init__(self, client: NerdGraphClient, settings: Settings) -> None:
        self._client = client
        self._settings = settings

    def prepare(self, query: str) -> str:
        """Validate the query and add default SINCE/LIMIT clauses."""
        validated = validate_nrql(query)
        return apply_defaults(
            validated,
            default_since=self._settings.default_since,
            max_rows=self._settings.max_result_rows,
        )

    async def run(
        self,
        query: str,
        *,
        account_ids: list[int] | None = None,
        timeout_seconds: int | None = None,
    ) -> dict[str, Any]:
        """Execute a synchronous NRQL query."""
        accounts = self._settings.resolve_accounts(account_ids)
        prepared = self.prepare(query)
        data = await self._client.execute(
            NRQL_QUERY,
            {
                "accounts": accounts,
                "nrql": prepared,
                "timeout": timeout_seconds or self._settings.query_timeout_seconds,
            },
        )
        result = _nrql_node(data)
        return {
            "query": prepared,
            "accounts": accounts,
            "results": result.get("results") or [],
            "metadata": result.get("metadata") or {},
        }

    async def run_async_query(
        self,
        query: str,
        *,
        account_ids: list[int] | None = None,
    ) -> dict[str, Any]:
        """Execute a long-running NRQL query and poll until it completes.

        Use this for wide time windows that exceed the synchronous timeout; the
        trade-off is latency, since completion is polled rather than streamed.
        """
        accounts = self._settings.resolve_accounts(account_ids)
        prepared = self.prepare(query)

        data = await self._client.execute(
            NRQL_QUERY_ASYNC_START, {"accounts": accounts, "nrql": prepared}
        )
        node = _nrql_node(data)
        progress = node.get("queryProgress") or {}

        attempts = 0
        while not progress.get("completed"):
            if attempts >= _MAX_POLL_ATTEMPTS:
                raise NerdGraphError(
                    f"Async NRQL query did not complete after {attempts} polls. "
                    "Narrow the time window or aggregate the data."
                )
            await asyncio.sleep(min(float(progress.get("retryAfter") or 2), 10.0))
            attempts += 1
            polled = await self._client.execute(
                NRQL_QUERY_ASYNC_POLL,
                {"accounts": accounts, "queryId": progress.get("queryId")},
            )
            node = _progress_node(polled)
            progress = node.get("queryProgress") or {}

        return {
            "query": prepared,
            "accounts": accounts,
            "results": node.get("results") or [],
            "polls": attempts,
        }


def _nrql_node(data: dict[str, Any]) -> dict[str, Any]:
    node = (data.get("actor") or {}).get("nrql")
    if node is None:
        raise NerdGraphError("NerdGraph returned no NRQL node; check account access.")
    return dict(node)


def _progress_node(data: dict[str, Any]) -> dict[str, Any]:
    node = (data.get("actor") or {}).get("nrqlQueryProgress")
    if node is None:
        raise NerdGraphError("NerdGraph returned no query progress node.")
    return dict(node)
