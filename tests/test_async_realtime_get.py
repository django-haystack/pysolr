"""Tests for AsyncSolr.realtime_get (the /get handler)."""

import asyncio
import functools

import httpx2
import pytest

from pysolr import AsyncSolr, Solr, SolrError

BASE_URL = "http://localhost:8983/solr/core0"


def async_test(coro_fn):
    """Run an ``async def`` test to completion with asyncio.run.

    Keeps pysolr's test dependencies unchanged (no pytest-asyncio needed).
    """

    @functools.wraps(coro_fn)
    def wrapper(*args, **kwargs):
        return asyncio.run(coro_fn(*args, **kwargs))

    return wrapper


def _mock_client(handler):
    """An httpx2.AsyncClient that answers requests with ``handler`` (no network)."""
    return httpx2.AsyncClient(transport=httpx2.MockTransport(handler))


def _json_response(payload, status_code=200):
    return httpx2.Response(status_code, json=payload)


class TestAsyncRealtimeGetRequest:
    """What realtime_get sends and how it reads the reply. No Solr needed."""

    @async_test
    async def test_sends_ids_to_get_handler(self):
        seen = {}

        def handler(request):
            seen["url"] = str(request.url)
            return _json_response({"response": {"numFound": 0, "docs": []}})

        solr = AsyncSolr(BASE_URL, session=_mock_client(handler))

        await solr.realtime_get(["doc1", "doc2"])

        assert seen["url"].startswith(f"{BASE_URL}/get?")
        assert "ids=doc1%2Cdoc2" in seen["url"] or "ids=doc1,doc2" in seen["url"]

    @async_test
    async def test_sends_fl_when_given(self):
        seen = {}

        def handler(request):
            seen["url"] = str(request.url)
            return _json_response({"response": {"numFound": 0, "docs": []}})

        solr = AsyncSolr(BASE_URL, session=_mock_client(handler))

        await solr.realtime_get(["doc1"], fl="id,title")

        assert "fl=id%2Ctitle" in seen["url"] or "fl=id,title" in seen["url"]

    @async_test
    async def test_returns_docs_from_response(self):
        def handler(request):
            return _json_response(
                {"response": {"numFound": 2, "docs": [{"id": "a"}, {"id": "b"}]}}
            )

        solr = AsyncSolr(BASE_URL, session=_mock_client(handler))

        docs = await solr.realtime_get(["a", "b"])

        assert docs == [{"id": "a"}, {"id": "b"}]

    @async_test
    async def test_missing_ids_return_empty_list(self):
        def handler(request):
            return _json_response({"response": {"numFound": 0, "docs": []}})

        solr = AsyncSolr(BASE_URL, session=_mock_client(handler))

        assert await solr.realtime_get(["nope"]) == []

    @async_test
    async def test_http_error_raises_solr_error(self):
        def handler(request):
            return httpx2.Response(500, text="boom")

        solr = AsyncSolr(BASE_URL, session=_mock_client(handler))

        with pytest.raises(SolrError, match="HTTP 500"):
            await solr.realtime_get(["doc1"])

    @async_test
    async def test_connection_error_raises_solr_error(self):
        def handler(request):
            raise httpx2.ConnectError("refused", request=request)

        solr = AsyncSolr(BASE_URL, session=_mock_client(handler))

        with pytest.raises(SolrError, match="Failed to connect"):
            await solr.realtime_get(["doc1"])

    @async_test
    async def test_timeout_raises_solr_error(self):
        def handler(request):
            raise httpx2.ReadTimeout("slow", request=request)

        solr = AsyncSolr(BASE_URL, session=_mock_client(handler))

        with pytest.raises(SolrError, match="timed out"):
            await solr.realtime_get(["doc1"])

    @async_test
    async def test_context_manager_closes_session(self):
        solr = AsyncSolr(BASE_URL, session=_mock_client(lambda r: _json_response({})))

        async with solr:
            pass

        assert solr.session.is_closed


class TestAsyncRealtimeGetLive:
    """Realtime get sees uncommitted writes on a live Solr (core0)."""

    @async_test
    async def test_finds_uncommitted_doc(self):
        sync = Solr(BASE_URL)
        sync.add([{"id": "rtg-test-1", "title": "uncommitted"}], commit=False)
        try:
            async with AsyncSolr(BASE_URL) as solr:
                docs = await solr.realtime_get(["rtg-test-1"], fl="id,title")
        finally:
            sync.delete(id="rtg-test-1", commit=True)

        # The test schema stores title as multi-valued, so Solr returns a list.
        assert docs == [{"id": "rtg-test-1", "title": ["uncommitted"]}]
