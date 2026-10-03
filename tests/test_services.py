from __future__ import annotations

import json

import httpx
import pytest
import respx

from .helpers import ENDPOINT


def _nrql_response(results: list[dict[str, object]]) -> httpx.Response:
    return httpx.Response(
        200,
        json={"data": {"actor": {"nrql": {"results": results, "metadata": {}}}}},
    )


@respx.mock
async def test_run_applies_defaults_and_returns_results(context):
    route = respx.post(ENDPOINT).mock(return_value=_nrql_response([{"count": 3}]))
    result = await context.nrql.run("SELECT count(*) FROM Transaction")

    sent = json.loads(route.calls.last.request.content)["variables"]
    assert sent["accounts"] == [1234567]
    assert "SINCE 30 MINUTES AGO" in sent["nrql"]
    assert result["results"] == [{"count": 3}]


async def test_run_without_accounts_is_rejected(context):
    accountless = context.settings.model_copy(update={"account_ids": []})
    with pytest.raises(ValueError, match="No account id provided"):
        accountless.resolve_accounts(None)


async def test_cross_account_limit(context):
    with pytest.raises(ValueError, match="at most 30 accounts"):
        context.settings.resolve_accounts(list(range(31)))


def test_log_query_escapes_input(context):
    query = context.logs.build_query(service_name="checkout' OR 1=1 --", limit=10)
    assert "checkout\\' OR 1=1 --" in query
    assert query.count("SINCE") == 1


def test_log_query_filters_by_trace(context):
    query = context.logs.build_query(trace_id="abc123", level="error")
    assert "`trace.id` = 'abc123'" in query
    assert "`level` = 'ERROR'" in query


@respx.mock
async def test_get_trace_summarises_services(context):
    respx.post(ENDPOINT).mock(
        return_value=_nrql_response(
            [
                {"service.name": "checkout", "name": "POST /order"},
                {"service.name": "payments", "name": "charge"},
                {"service.name": "checkout", "name": "db"},
            ]
        )
    )
    result = await context.traces.get_trace("abc123")
    assert result["span_count"] == 3
    assert result["services"] == ["checkout", "payments"]


@respx.mock
async def test_entity_search_requires_criteria(context):
    with pytest.raises(ValueError, match="at least one search criterion"):
        await context.entities.search()


@respx.mock
async def test_entity_search_builds_query(context):
    route = respx.post(ENDPOINT).mock(
        return_value=httpx.Response(
            200,
            json={
                "data": {
                    "actor": {
                        "entitySearch": {
                            "count": 1,
                            "results": {"entities": [{"guid": "abc"}], "nextCursor": None},
                        }
                    }
                }
            },
        )
    )
    result = await context.entities.search(name="checkout", domain="apm")

    sent = json.loads(route.calls.last.request.content)["variables"]["query"]
    assert sent == "name LIKE 'checkout' AND domain = 'APM'"
    assert result["count"] == 1
