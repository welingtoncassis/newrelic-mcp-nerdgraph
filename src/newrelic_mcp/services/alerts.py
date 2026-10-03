"""Alert policies, NRQL conditions and open issues."""

from __future__ import annotations

from typing import Any

from ..nerdgraph.client import NerdGraphClient
from ..nerdgraph.queries import AI_ISSUES, ALERT_POLICIES, NRQL_CONDITIONS


class AlertService:
    """Read access to the alerting configuration and to active issues."""

    def __init__(self, client: NerdGraphClient) -> None:
        self._client = client

    async def list_policies(self, account_id: int, cursor: str | None = None) -> dict[str, Any]:
        data = await self._client.execute(
            ALERT_POLICIES, {"accountId": account_id, "cursor": cursor}
        )
        search = _alerts_node(data).get("policiesSearch") or {}
        return {
            "policies": search.get("policies") or [],
            "next_cursor": search.get("nextCursor"),
        }

    async def list_nrql_conditions(
        self,
        account_id: int,
        *,
        policy_id: str | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        data = await self._client.execute(
            NRQL_CONDITIONS,
            {"accountId": account_id, "policyId": policy_id, "cursor": cursor},
        )
        search = _alerts_node(data).get("nrqlConditionsSearch") or {}
        return {
            "conditions": search.get("nrqlConditions") or [],
            "next_cursor": search.get("nextCursor"),
        }

    async def list_issues(
        self,
        account_id: int,
        *,
        only_open: bool = True,
        priority: str | None = None,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """List AI issues, defaulting to the ones still activated."""
        filters: dict[str, Any] = {}
        if only_open:
            filters["states"] = ["ACTIVATED"]
        if priority:
            filters["priority"] = priority.upper()

        data = await self._client.execute(
            AI_ISSUES,
            {"accountId": account_id, "filter": filters or None, "cursor": cursor},
        )
        issues_node = (((data.get("actor") or {}).get("account") or {}).get("aiIssues") or {}).get(
            "issues"
        ) or {}
        return {
            "issues": issues_node.get("issues") or [],
            "next_cursor": issues_node.get("nextCursor"),
        }


def _alerts_node(data: dict[str, Any]) -> dict[str, Any]:
    account = (data.get("actor") or {}).get("account") or {}
    return dict(account.get("alerts") or {})
