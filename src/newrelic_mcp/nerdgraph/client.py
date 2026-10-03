"""Async HTTP client for the NerdGraph GraphQL endpoint."""

from __future__ import annotations

import asyncio
import logging
import random
from types import TracebackType
from typing import Any

import httpx

from ..config import Settings
from ..errors import NerdGraphError, NerdGraphHTTPError

logger = logging.getLogger(__name__)

_RETRY_STATUS = frozenset({408, 429, 500, 502, 503, 504})
_USER_AGENT = "newrelic-mcp-nerdgraph"


class NerdGraphClient:
    """Thin GraphQL client with retry, backoff and error normalisation.

    The API key is attached per request from :class:`Settings` and is never
    stored in a mutable attribute, so it cannot leak through ``repr``.
    """

    def __init__(self, settings: Settings, *, client: httpx.AsyncClient | None = None) -> None:
        self._settings = settings
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(settings.http_timeout_seconds),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )

    @property
    def endpoint(self) -> str:
        return self._settings.region.nerdgraph_endpoint

    async def __aenter__(self) -> NerdGraphClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def execute(
        self,
        query: str,
        variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Run a GraphQL document and return the ``data`` object.

        Raises:
            NerdGraphHTTPError: transport or status failures after all retries.
            NerdGraphError: the response carried GraphQL ``errors``.
        """
        payload = {"query": query, "variables": variables or {}}
        headers = {
            "Content-Type": "application/json",
            "API-Key": self._settings.api_key.get_secret_value(),
            "User-Agent": _USER_AGENT,
        }

        last_error: Exception | None = None
        for attempt in range(self._settings.max_retries + 1):
            try:
                response = await self._client.post(self.endpoint, json=payload, headers=headers)
            except httpx.HTTPError as exc:  # network-level failure
                last_error = NerdGraphHTTPError(0, str(exc))
                if attempt == self._settings.max_retries:
                    raise last_error from exc
                await self._sleep_before_retry(attempt)
                continue

            if response.status_code in _RETRY_STATUS and attempt < self._settings.max_retries:
                logger.warning(
                    "NerdGraph returned %s, retrying (attempt %s)",
                    response.status_code,
                    attempt + 1,
                )
                await self._sleep_before_retry(attempt, response)
                continue

            if response.status_code >= 400:
                raise NerdGraphHTTPError(response.status_code, _safe_body(response))

            return self._unwrap(response.json())

        raise last_error or NerdGraphHTTPError(0, "NerdGraph request failed.")

    @staticmethod
    def _unwrap(body: dict[str, Any]) -> dict[str, Any]:
        errors = body.get("errors")
        if errors:
            messages = "; ".join(str(err.get("message", err)) for err in errors)
            raise NerdGraphError(messages, errors)
        data = body.get("data")
        if data is None:
            raise NerdGraphError("NerdGraph response contained no data.")
        return dict(data)

    async def _sleep_before_retry(
        self, attempt: int, response: httpx.Response | None = None
    ) -> None:
        retry_after = response.headers.get("Retry-After") if response else None
        if retry_after and retry_after.isdigit():
            await asyncio.sleep(min(int(retry_after), 30))
            return
        backoff = min(2**attempt, 8) + random.uniform(0, 0.5)  # noqa: S311 - jitter, not crypto
        await asyncio.sleep(backoff)


def _safe_body(response: httpx.Response) -> str:
    """Return a short, non-sensitive excerpt of an error body."""
    text = response.text or ""
    return text[:500]
