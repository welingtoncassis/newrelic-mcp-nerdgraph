"""Entity discovery and inspection."""

from __future__ import annotations

from typing import Any

from ..errors import NerdGraphError
from ..nerdgraph.client import NerdGraphClient
from ..nerdgraph.queries import ENTITY_DETAILS, ENTITY_SEARCH
from ..security.nrql_guard import escape_nrql_string


class EntityService:
    """Wraps ``entitySearch`` and ``entity`` lookups."""

    def __init__(self, client: NerdGraphClient) -> None:
        self._client = client

    async def search(
        self,
        *,
        name: str | None = None,
        domain: str | None = None,
        entity_type: str | None = None,
        account_id: int | None = None,
        tags: dict[str, str] | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """Search entities with the entity-search query language."""
        clauses: list[str] = []
        if name:
            clauses.append(f"name LIKE '{escape_nrql_string(name)}'")
        if domain:
            clauses.append(f"domain = '{escape_nrql_string(domain.upper())}'")
        if entity_type:
            clauses.append(f"type = '{escape_nrql_string(entity_type.upper())}'")
        if account_id is not None:
            clauses.append(f"accountId = {int(account_id)}")
        for key, value in (tags or {}).items():
            clauses.append(f"tags.`{escape_nrql_string(key)}` = '{escape_nrql_string(value)}'")
        if not clauses:
            raise ValueError("Provide at least one search criterion.")

        data = await self._client.execute(
            ENTITY_SEARCH, {"query": " AND ".join(clauses), "cursor": cursor}
        )
        search = (data.get("actor") or {}).get("entitySearch") or {}
        results = search.get("results") or {}
        return {
            "count": search.get("count", 0),
            "entities": results.get("entities") or [],
            "next_cursor": results.get("nextCursor"),
        }

    async def get(self, guid: str) -> dict[str, Any]:
        """Fetch one entity with golden metrics, tags and relationships."""
        data = await self._client.execute(ENTITY_DETAILS, {"guid": guid})
        entity = (data.get("actor") or {}).get("entity")
        if entity is None:
            raise NerdGraphError(f"Entity '{guid}' was not found or is not accessible.")
        return dict(entity)
