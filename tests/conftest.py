from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
import pytest
from pydantic import SecretStr

from newrelic_mcp.config import Region, Settings
from newrelic_mcp.context import AppContext, build_context


@pytest.fixture
def settings() -> Settings:
    return Settings(
        api_key=SecretStr("NRAK-TESTKEYTESTKEYTESTKEY"),
        account_ids=[1234567],
        region=Region.US,
        max_retries=0,
    )


@pytest.fixture
async def context(settings: Settings) -> AsyncIterator[AppContext]:
    async with build_context(settings, http_client=httpx.AsyncClient()) as ctx:
        yield ctx
