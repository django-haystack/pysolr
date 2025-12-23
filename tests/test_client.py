import datetime
import random
import time
import unittest
from io import StringIO
from unittest.mock import Mock
from urllib.parse import unquote_plus
from xml.etree import ElementTree  # noqa: ICN001

import pytest

from pysolr import (
    NESTED_DOC_KEY,
    Results,
    Solr,
    SolrError,
    clean_xml_string,
    force_bytes,
    force_unicode,
    json,
    safe_urlencode,
    sanitize,
    unescape_html,
)


class UtilsTestCase(unittest.TestCase):
    def test_unescape_html(self):
        assert unescape_html("Hello &#149; world") == "Hello \x95 world"
        assert unescape_html("Hello &#x64; world") == "Hello d world"
        assert unescape_html("Hello &amp; ☃") == "Hello & ☃"
        assert (
            unescape_html("Hello &doesnotexist; world") == "Hello &doesnotexist; world"
        )

    def test_safe_urlencode(self):
        assert (
            force_unicode(
                unquote_plus(safe_urlencode({"test": "Hello ☃! Helllo world!"}))
            )
            == "test=Hello ☃! Helllo world!"
        )
        assert (
            force_unicode(
                unquote_plus(
                    safe_urlencode({"test": ["Hello ☃!", "Helllo world!"]}, True)
                )
            )
            == "test=Hello ☃!&test=Helllo world!"
        )
        assert (
            force_unicode(
                unquote_plus(
                    safe_urlencode({"test": ("Hello ☃!", "Helllo world!")}, True)
                )
            )
            == "test=Hello ☃!&test=Helllo world!"
        )

    def test_sanitize(self):
        assert (
            sanitize(
                "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f\x10\x11\x12"
                "\x13\x14\x15\x16\x17\x18\x19h\x1ae\x1bl\x1cl\x1do\x1e\x1f"
            )
            == "hello"
        )

    def test_force_unicode(self):
        assert force_unicode(b"Hello \xe2\x98\x83") == "Hello ☃"
        # Don't mangle, it's already Unicode.
        assert force_unicode("Hello ☃") == "Hello ☃"

        assert force_unicode(1) == "1", "force_unicode() should convert ints"
        assert force_unicode(1.0) == "1.0", "force_unicode() should convert floats"
        assert force_unicode(None) == "None", "force_unicode() should convert None"

    def test_force_bytes(self):
        assert force_bytes("Hello ☃") == b"Hello \xe2\x98\x83"
        # Don't mangle, it's already a bytestring.
        assert force_bytes(b"Hello \xe2\x98\x83") == b"Hello \xe2\x98\x83"

    def test_clean_xml_string(self):
        assert clean_xml_string("\x00\x0b\r\uffff") == "\r"


class ResultsTestCase(unittest.TestCase):
    def test_init(self):
        default_results = Results(
            {"response": {"docs": [{"id": 1}, {"id": 2}], "numFound": 2}}
        )

        assert default_results.docs == [{"id": 1}, {"id": 2}]
        assert default_results.hits == 2
        assert default_results.highlighting == {}
        assert default_results.facets == {}
        assert default_results.spellcheck == {}
        assert default_results.stats == {}
        assert default_results.qtime is None
        assert default_results.debug == {}
        assert default_results.grouped == {}

        full_results = Results(
            {
                "response": {"docs": [{"id": 1}, {"id": 2}, {"id": 3}], "numFound": 3},
                # Fake data just to check assignments.
                "highlighting": "hi",
                "facet_counts": "fa",
                "spellcheck": "sp",
                "stats": "st",
                "responseHeader": {"QTime": "0.001"},
                "debug": True,
                "grouped": ["a"],
            }
        )

        assert full_results.docs == [{"id": 1}, {"id": 2}, {"id": 3}]
        assert full_results.hits == 3
        assert full_results.highlighting == "hi"
        assert full_results.facets == "fa"
        assert full_results.spellcheck == "sp"
        assert full_results.stats == "st"
        assert full_results.qtime == "0.001"
        assert full_results.debug
        assert full_results.grouped == ["a"]

    def test_len(self):
        small_results = Results(
            {"response": {"docs": [{"id": 1}, {"id": 2}], "numFound": 2}}
        )
        assert len(small_results) == 2

        wrong_hits_results = Results(
            {"response": {"docs": [{"id": 1}, {"id": 2}, {"id": 3}], "numFound": 7}}
        )
        assert len(wrong_hits_results) == 3

    def test_iter(self):
        long_results = Results(
            {"response": {"docs": [{"id": 1}, {"id": 2}, {"id": 3}], "numFound": 7}}
        )

        to_iter = list(long_results)
        assert to_iter[0] == {"id": 1}
        assert to_iter[1] == {"id": 2}
        assert to_iter[2] == {"id": 3}


class SolrTestCaseMixin(object):
    def get_solr(self, collection, timeout=60, always_commit=False):
        return Solr(
            "http://localhost:8983/solr/%s" % collection,
            timeout=timeout,
            always_commit=always_commit,
        )


class SolrTestCase(unittest.TestCase, SolrTestCaseMixin):
    def setUp(self):
        self.solr = self.get_solr("core0")
        self.docs = [
            {"id": "doc_1", "title": "Example doc 1", "price": 12.59, "popularity": 10},
            {
                "id": "doc_2",
                "title": "Another example ☃ doc 2",
                "price": 13.69,
                "popularity": 7,
            },
            {"id": "doc_3", "title": "Another thing", "price": 2.35, "popularity": 8},
            {"id": "doc_4", "title": "doc rock", "price": 99.99, "popularity": 10},
            {"id": "doc_5", "title": "Boring", "price": 1.12, "popularity": 2},
            # several with nested docs (not using fields that are used in
            # normal docs so that they don't interfere with their tests)
            {
                "id": "parentdoc_1",
                "type_s": "parent",
                "name_t": "Parent no. 1",
                "pages_i": 5,
                NESTED_DOC_KEY: [
                    {
                        "id": "childdoc_1",
                        "type_s": "child",
                        "name_t": "Child #1",
                        "comment_t": "Hello there",
                    },
                    {
                        "id": "childdoc_2",
                        "type_s": "child",
                        "name_t": "Child #2",
                        "comment_t": "Ehh..",
                    },
                ],
            },
            {
                "id": "parentdoc_2",
                "type_s": "parent",
                "name_t": "Parent no. 2",
                "pages_i": 500,
                NESTED_DOC_KEY: [
                    {
                        "id": "childdoc_3",
                        "type_s": "child",
                        "name_t": "Child of another parent",
                        "comment_t": "Yello",
                        NESTED_DOC_KEY: [
                            {
                                "id": "grandchilddoc_1",
                                "type_s": "grandchild",
                                "name_t": "Grand child of parent",
                                "comment_t": "Blah",
                            }
                        ],
                    }
                ],
            },
        ]

        # Clear it.
        self.solr.delete(q="*:*", commit=True)

        # Index our docs. Yes, this leans on functionality we're going to test
        # later & if it's broken, everything will catastrophically fail.
        # Such is life.
        self.solr.add(self.docs, commit=True)

        # Mock the _send_request method on the solr instance so that we can
        # test that custom handlers are called correctly.
        self.solr._send_request = Mock(wraps=self.solr._send_request)

    def assertURLStartsWith(self, URL, path):
        """
        Assert that the test URL provided starts with a known base and the provided path
        """
        # Note that we do not use urljoin to ensure that any changes in trailing
        # slash handling are caught quickly:
        assert URL == "%s/%s" % (self.solr.url.replace("/core0", ""), path)

    def test_init(self):
        assert self.solr.url == "http://localhost:8983/solr/core0"
        assert isinstance(self.solr.decoder, json.JSONDecoder)
        assert isinstance(self.solr.encoder, json.JSONEncoder)
        assert self.solr.timeout == 60

        custom_solr = self.get_solr("core0", timeout=17, always_commit=True)
        assert custom_solr.timeout == 17
        assert custom_solr.always_commit

    def test_custom_results_class(self):
        solr = Solr("http://localhost:8983/solr/core0", results_cls=dict)

        results = solr.search(q="*:*")
        assert isinstance(results, dict)
        assert "responseHeader" in results
        assert "response" in results

    def test_cursor_traversal(self):
        solr = Solr("http://localhost:8983/solr/core0")

        expected = solr.search(q="*:*", rows=len(self.docs) * 3, sort="id asc").docs
        results = solr.search(q="*:*", cursorMark="*", rows=2, sort="id asc")
        all_docs = list(results)
        assert len(expected) == len(all_docs)
        assert len(results) == len(all_docs)
        assert expected == all_docs

    def test__create_full_url_base(self):
        self.assertURLStartsWith(self.solr._create_full_url(path=""), "core0")

    def test__create_full_url_with_path(self):
        self.assertURLStartsWith(
            self.solr._create_full_url(path="pysolr_tests"), "core0/pysolr_tests"
        )

    def test__create_full_url_with_path_and_querystring(self):
        # Note the use of a querystring parameter including a trailing slash to
        # catch sloppy trimming:
        self.assertURLStartsWith(
            self.solr._create_full_url(path="/pysolr_tests/select/?whatever=/"),
            "core0/pysolr_tests/select/?whatever=/",
        )

    def test__send_request(self):
        # Test a valid request.
        resp_body = self.solr._send_request("GET", "select/?q=doc&wt=json")
        assert '"numFound":3' in resp_body

        # Test a lowercase method & a body.
        xml_body = (
            '<add><doc><field name="id">doc_12</field>'
            '<field name="title">Whee! ☃</field></doc></add>'
        )
        resp_body = self.solr._send_request(
            "POST",
            "update/?commit=true",
            body=xml_body,
            headers={"Content-type": "text/xml; charset=utf-8"},
        )
        assert '<int name="status">0</int>' in resp_body

        # Test JSON Array
        json_body = '[{"id":"doc_13","title":"Whee hoo! ☃"}]'
        resp_body = self.solr._send_request(
            "POST",
            "update/?commit=true",
            body=json_body,
            headers={"Content-type": "application/json; charset=utf-8"},
        )
        assert '"status":0' in resp_body

    def test__send_request_to_bad_path(self):
        # Test a non-existent URL:
        self.solr.url = "http://127.0.0.1:56789/whatever"
        with pytest.raises(SolrError):
            self.solr._send_request("get", "select/?q=doc&wt=json")

    def test_send_request_to_bad_core(self):
        # Test a bad core on a valid URL:
        self.solr.url = "http://localhost:8983/solr/bad_core"
        with pytest.raises(SolrError):
            self.solr._send_request("get", "select/?q=doc&wt=json")

    def test__select(self):
        # Short params.
        resp_body = self.solr._select({"q": "doc"})
        resp_data = json.loads(resp_body)
        assert resp_data["response"]["numFound"] == 3

        # Long params.
        resp_body = self.solr._select({"q": "doc" * 1024})
        resp_data = json.loads(resp_body)
        assert resp_data["response"]["numFound"] == 0
        assert len(resp_data["responseHeader"]["params"]["q"]) == 3 * 1024

        # Test Deep Pagination CursorMark
        resp_body = self.solr._select(
            {"q": "*", "cursorMark": "*", "sort": "id desc", "start": 0, "rows": 2}
        )
        resp_data = json.loads(resp_body)
        assert len(resp_data["response"]["docs"]) == 2
        assert "nextCursorMark" in resp_data

    def test__select_wt_xml(self):
        resp_body = self.solr._select({"q": "doc", "wt": "xml"})
        response = ElementTree.fromstring(resp_body)
        assert int(response.find("result").get("numFound")) == 3

    def test__mlt(self):
        resp_body = self.solr._mlt({"q": "id:doc_1", "mlt.fl": "title"})
        resp_data = json.loads(resp_body)
        assert resp_data["response"]["numFound"] == 0

    def test__suggest_terms(self):
        resp_body = self.solr._select({"terms.fl": "title"})
        resp_data = json.loads(resp_body)
        assert resp_data["response"]["numFound"] == 0

    def test__update(self):
        xml_body = (
            '<add><doc><field name="id">doc_12</field>'
            '<field name="title">Whee!</field></doc></add>'
        )
        resp_body = self.solr._update(xml_body)
        assert '<int name="status">0</int>' in resp_body

    def test__soft_commit(self):
        xml_body = (
            '<add><doc><field name="id">doc_12</field>'
            '<field name="title">Whee!</field></doc></add>'
        )
        resp_body = self.solr._update(xml_body, softCommit=True)
        assert '<int name="status">0</int>' in resp_body

    def test__extract_error(self):
        class RubbishResponse(object):
            def __init__(self, content, headers=None):
                if isinstance(content, bytes):
                    content = content.decode("utf-8")
                self.content = content
                self.headers = headers

                if self.headers is None:
                    self.headers = {}

            def json(self):
                return json.loads(self.content)

        # Just the reason.
        resp_1 = RubbishResponse("We don't care.", {"reason": "Something went wrong."})
        assert self.solr._extract_error(resp_1) == "[Reason: Something went wrong.]"

        # Empty reason.
        resp_2 = RubbishResponse("We don't care.", {"reason": None})
        assert self.solr._extract_error(resp_2) == "[Reason: None]\nWe don't care."

        # No reason. Time to scrape.
        resp_3 = RubbishResponse(
            "<html><body><pre>Something is broke.</pre></body></html>",
            {"server": "jetty"},
        )
        assert self.solr._extract_error(resp_3) == "[Reason: Something is broke.]"

        # No reason. JSON response.
        resp_4 = RubbishResponse(
            b'\n {"error": {"msg": "It happens"}}', {"server": "tomcat"}
        )
        assert self.solr._extract_error(resp_4) == "[Reason: It happens]"

        # No reason. Weird JSON response.
        resp_5 = RubbishResponse(b'{"kinda": "weird"}', {"server": "jetty"})
        assert self.solr._extract_error(resp_5) == '[Reason: None]\n{"kinda": "weird"}'

    def test__scrape_response(self):
        # Jetty.
        resp_1 = self.solr._scrape_response(
            {"server": "jetty"},
            "<html><body><pre>Something is broke.</pre></body></html>",
        )
        assert resp_1 == ("Something is broke.", "")

        # Other.
        resp_2 = self.solr._scrape_response(
            {"server": "crapzilla"},
            "<html><head><title>Wow. Seriously weird.</title></head>"
            "<body><pre>Something is broke.</pre></body></html>",
        )
        assert resp_2 == ("Wow. Seriously weird.", "")

    def test__scrape_response_coyote_xml(self):
        resp_3 = self.solr._scrape_response(
            {"server": "coyote"},
            '<?xml version="1.0"?>\n<response>\n<lst name="responseHeader">'
            '<int name="status">400</int><int name="QTime">0</int></lst>'
            '<lst name="error">'
            "<str name=\"msg\">Invalid Date String:'2015-03-23 10:43:33'</str>"
            '<int name="code">400</int></lst>\n</response>\n',
        )
        assert resp_3 == (
            "Invalid Date String:'2015-03-23 10:43:33'",
            "Invalid Date String:'2015-03-23 10:43:33'",
        )

        # Valid XML with a traceback
        resp_4 = self.solr._scrape_response(
            {"server": "coyote"},
            """<?xml version="1.0"?>
<response>
<lst name="responseHeader"><int name="status">500</int><int name="QTime">138</int></lst>
<lst name="error"><str name="msg">Internal Server Error</str>
<str name="trace">org.apache.solr.common.SolrException: Internal Server Error at java.lang.Thread.run(Thread.java:745)</str><int name="code">500</int></lst>
</response>""",  # noqa: E501
        )
        assert resp_4 == (
            "Internal Server Error",
            (
                "org.apache.solr.common.SolrException: Internal Server Error at "
                "java.lang.Thread.run(Thread.java:745)"
            ),
        )

    def test__scrape_response_tomcat(self):
        """Tests for Tomcat error responses"""

        resp_0 = self.solr._scrape_response(
            {"server": "coyote"},
            "<html><body><h1>Something broke!</h1><pre>gigantic stack trace</pre>"
            "</body></html>",
        )
        assert resp_0 == ("Something broke!", "")

        # Invalid XML
        bogus_xml = (
            '<?xml version="1.0"?>\n<response>\n<lst name="responseHeader">'
            '<int name="status">400</int><int name="QTime">0</int></lst>'
            '<lst name="error">'
            "<str name=\"msg\">Invalid Date String:'2015-03-23 10:43:33'</str>"
            '<int name="code">400</int></lst>'
        )
        reason, full_html = self.solr._scrape_response({"server": "coyote"}, bogus_xml)
        assert reason is None
        assert full_html == bogus_xml.replace("\n", "")

    def test__from_python(self):
        assert self.solr._from_python(True) == "true"
        assert self.solr._from_python(False) == "false"
        assert self.solr._from_python(1) == "1"
        assert self.solr._from_python(1.2) == "1.2"
        assert self.solr._from_python(b"hello") == "hello"
        assert self.solr._from_python("hello ☃") == "hello ☃"
        assert self.solr._from_python("\x01test\x02") == "test"

    def test__from_python_dates(self):
        assert (
            self.solr._from_python(datetime.date(2013, 1, 18)) == "2013-01-18T00:00:00Z"
        )
        assert (
            self.solr._from_python(datetime.datetime(2013, 1, 18, 0, 30, 28))
            == "2013-01-18T00:30:28Z"
        )

        class FakeTimeZone(datetime.tzinfo):
            offset = 0

            def utcoffset(self, dt):
                return datetime.timedelta(minutes=self.offset)

            def dst(self):
                return None

        # Check a UTC timestamp
        assert (
            self.solr._from_python(
                datetime.datetime(2013, 1, 18, 0, 30, 28, tzinfo=FakeTimeZone())
            )
            == "2013-01-18T00:30:28Z"
        )

        # Check a US Eastern Standard Time timestamp
        FakeTimeZone.offset = -(5 * 60)
        assert (
            self.solr._from_python(
                datetime.datetime(2013, 1, 18, 0, 30, 28, tzinfo=FakeTimeZone())
            )
            == "2013-01-18T05:30:28Z"
        )

    def test__to_python(self):
        assert self.solr._to_python("2013-01-18T00:00:00Z") == datetime.datetime(
            2013, 1, 18
        )
        assert self.solr._to_python("2013-01-18T00:30:28Z") == datetime.datetime(
            2013, 1, 18, 0, 30, 28
        )
        assert self.solr._to_python("true")
        assert not self.solr._to_python("false")
        assert self.solr._to_python(1) == 1
        assert self.solr._to_python(1.2) == 1.2
        assert self.solr._to_python(b"hello") == "hello"
        assert self.solr._to_python("hello ☃") == "hello ☃"
        assert self.solr._to_python(["foo", "bar"]) == ["foo", "bar"]
        assert self.solr._to_python(("foo", "bar")) == ("foo", "bar")
        assert self.solr._to_python('tuple("foo", "bar")') == 'tuple("foo", "bar")'

    def test__is_null_value(self):
        assert self.solr._is_null_value(None)
        assert self.solr._is_null_value("")

        assert not self.solr._is_null_value("Hello")
        assert not self.solr._is_null_value(1)

    def test_search(self):
        results = self.solr.search("doc")
        assert len(results) == 3
        # search should default to 'select' handler
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("select/?")

        results = self.solr.search("example")
        assert len(results) == 2

        results = self.solr.search("nothing")
        assert len(results) == 0

        # Advanced options.
        results = self.solr.search(
            "doc",
            **{
                "debug": "true",
                "hl": "true",
                "hl.fragsize": 8,
                "facet": "on",
                "facet.field": "popularity",
                "spellcheck": "true",
                "spellcheck.collate": "true",
                "spellcheck.count": 1,
            },
        )
        assert len(results) == 3
        assert "explain" in results.debug
        assert results.highlighting == {"doc_4": {}, "doc_2": {}, "doc_1": {}}
        assert results.spellcheck == {}

        # Facet counts apply only to documents matching the main query ("q=doc").
        # Only docs with popularity=10 and 7 contain "doc" in their text fields, so the
        # facet output is ["10", 2, "7", 1]. Values like 2 and 8 do not appear because
        # those documents do not match the query and are excluded from facet counts.
        assert results.facets["facet_fields"]["popularity"] == ["10", 2, "7", 1]
        assert results.qtime is not None

        # Nested search #1: find parent where child's comment has 'hello'
        results = self.solr.search("{!parent which=type_s:parent}comment_t:hello")
        assert len(results) == 1
        # Nested search #2: find child with a child
        results = self.solr.search("{!parent which=type_s:child}comment_t:blah")
        assert len(results) == 1

    def test_multiple_search_handlers(self):
        misspelled_words = "anthr thng"
        # By default, the 'select' search handler should be used
        results = self.solr.search(q=misspelled_words)
        assert results.spellcheck == {}
        # spell search handler should return suggestions
        # NB: this test relies on the spell search handler in the
        # solrconfig (see the SOLR_ARCHIVE used by the start-solr-test-server script)
        results = self.solr.search(q=misspelled_words, search_handler="spell")
        assert results.spellcheck != {}

        # search should support custom handlers
        with pytest.raises(SolrError):
            self.solr.search("doc", search_handler="fakehandler")
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("fakehandler")

    def test_more_like_this(self):
        results = self.solr.more_like_this("id:doc_1", "text")
        assert len(results) == 0
        # more_like_this should default to 'mlt' handler
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("mlt/?")

        # more_like_this should support custom handlers
        with pytest.raises(SolrError):
            self.solr.more_like_this("id:doc_1", "text", handler="fakehandler")
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("fakehandler")

    def test_suggest_terms(self):
        results = self.solr.suggest_terms("title", "")
        assert len(results) == 1
        assert results == {
            "title": [
                ("doc", 3),
                ("another", 2),
                ("example", 2),
                ("1", 1),
                ("2", 1),
                ("boring", 1),
                ("rock", 1),
                ("thing", 1),
                ("☃", 1),
            ]
        }
        # suggest_terms should default to 'mlt' handler
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("terms/?")

        # suggest_terms should support custom handlers
        with pytest.raises(SolrError):
            self.solr.suggest_terms("title", "", handler="fakehandler")
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("fakehandler")

    def test__build_xml_doc(self):
        doc = {
            "id": "doc_1",
            "title": "Example doc ☃ 1",
            "price": 12.59,
            "popularity": 10,
        }
        doc_xml = force_unicode(
            ElementTree.tostring(self.solr._build_xml_doc(doc), encoding="utf-8")
        )
        assert '<field name="title">Example doc ☃ 1</field>' in doc_xml
        assert '<field name="id">doc_1</field>' in doc_xml
        assert len(doc_xml) == 152

    def test__build_xml_doc_with_sets(self):
        doc = {"id": "doc_1", "title": "Set test doc", "tags": {"alpha", "beta"}}
        doc_xml = force_unicode(
            ElementTree.tostring(self.solr._build_xml_doc(doc), encoding="utf-8")
        )
        assert '<field name="id">doc_1</field>' in doc_xml
        assert '<field name="title">Set test doc</field>' in doc_xml
        assert '<field name="tags">alpha</field>' in doc_xml
        assert '<field name="tags">beta</field>' in doc_xml
        assert len(doc_xml) == 144

    def test__build_xml_doc_with_sub_docs(self):
        sub_docs = [
            {
                "id": "sub_doc_1",
                "title": "Example sub doc ☃ 1",
                "price": 1.59,
                "popularity": 4,
            },
            {
                "id": "sub_doc_2",
                "title": "Example sub doc ☃ 2",
                "price": 21.13,
                "popularity": 1,
            },
        ]
        doc = {
            "id": "doc_1",
            "title": "Example doc ☃ 1",
            "price": 12.59,
            "popularity": 10,
            "_doc": sub_docs,
        }
        doc_xml = self.solr._build_xml_doc(doc)
        assert doc_xml.find("*[@name='id']").text == doc["id"]

        children_docs = doc_xml.findall("doc")
        assert len(children_docs) == len(sub_docs)

        assert children_docs[0].find("*[@name='id']").text == sub_docs[0]["id"]
        assert children_docs[1].find("*[@name='id']").text == sub_docs[1]["id"]

    def test__build_xml_doc_with_empty_values(self):
        doc = {
            "id": "doc_1",
            "title": "",
            "price": None,
            "tags": [],
        }
        doc_xml = force_unicode(
            ElementTree.tostring(self.solr._build_xml_doc(doc), encoding="utf-8")
        )
        assert '<field name="title" />' not in doc_xml
        assert '<field name="price" />' not in doc_xml
        assert '<field name="tags" />' not in doc_xml
        assert '<field name="id">doc_1</field>' in doc_xml
        assert len(doc_xml) == 41

    def test__build_xml_doc_with_empty_values_and_field_updates(self):
        doc = {
            "id": "doc_1",
            "title": "",
            "price": None,
            "tags": [],
        }
        fieldUpdates = {
            "title": "set",
            "tags": "set",
        }
        doc_xml = force_unicode(
            ElementTree.tostring(
                self.solr._build_xml_doc(doc, fieldUpdates=fieldUpdates),
                encoding="utf-8",
            )
        )
        assert '<field name="title" null="true" update="set" />' in doc_xml
        assert '<field name="price" />' not in doc_xml
        assert '<field name="tags" null="true" update="set" />' in doc_xml
        assert '<field name="id">doc_1</field>' in doc_xml
        assert len(doc_xml) == 134

    def test_build_json_doc_matches_xml(self):
        doc = {"id": "doc_1", "title": "", "price": 12.59, "popularity": 10}

        doc_json = self.solr._build_json_doc(doc)
        doc_xml = self.solr._build_xml_doc(doc)
        assert "title" not in doc_json
        assert doc_xml.find("*[name='title']") is None

    def test__build_docs_plain(self):
        docs = [{"id": "doc_1", "title": "", "price": 12.59, "popularity": 10}]
        solrapi, _m, _len_message = self.solr._build_docs(docs)
        assert solrapi == "JSON"

    def test__build_docs_boost(self):
        docs = [{"id": "doc_1", "title": "", "price": 12.59, "popularity": 10}]
        solrapi, _m, _len_message = self.solr._build_docs(docs, boost={"title": 10.0})
        assert solrapi == "XML"

    def test__build_docs_field_updates(self):
        docs = [{"id": "doc_1", "popularity": 10}]
        solrapi, _m, _len_message = self.solr._build_docs(
            docs, fieldUpdates={"popularity": "inc"}
        )
        assert solrapi == "JSON"

    def test_add(self):
        assert len(self.solr.search("doc")) == 3
        assert len(self.solr.search("example")) == 2

        self.solr.add(
            [
                {"id": "doc_6", "title": "Newly added doc"},
                {"id": "doc_7", "title": "Another example doc"},
            ],
            commit=True,
        )
        # add should default to 'update' handler
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("update/?")

        assert len(self.solr.search("doc")) == 5
        assert len(self.solr.search("example")) == 3

        # add should support custom handlers
        with pytest.raises(SolrError):
            self.solr.add([], handler="fakehandler", commit=True)
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("fakehandler")

    def test_add_with_boost(self):
        assert len(self.solr.search("doc")) == 3

        # Add documents (index-time boost is removed in Solr 8+)
        # Ref: https://solr.apache.org/guide/solr/latest/upgrade-notes/major-changes-in-solr-8.html#indexing-changes-in-8-0
        self.solr.add(
            [{"id": "doc_6", "title": "Important doc"}], boost={"title": 10.0}
        )

        self.solr.add(
            [{"id": "doc_7", "title": "Spam doc doc"}],
            boost={"title": 0},
            commit=True,
        )

        res = self.solr.search("doc")
        assert len(res) == 5

        # Solr 8+ no longer supports index-time boosts.
        # TF/IDF scoring places doc_7 first because "doc" appears twice
        # consecutively in its title ("Spam doc doc").
        assert "doc_7" == res.docs[0]["id"]

    def test_add_with_commit_within(self):
        assert len(self.solr.search("commitWithin")) == 0

        commit_within_ms = 50
        self.solr.add(
            [
                {"id": "doc_6", "title": "commitWithin test"},
            ],
            commitWithin=commit_within_ms,
        )
        # we should not see the doc immediately
        assert len(self.solr.search("commitWithin")) == 0
        # but we should see it after commitWithin period (+ small grace period)
        time.sleep((commit_within_ms / 1000.0) + 0.01)
        assert len(self.solr.search("commitWithin")) == 1

    def test_field_update_inc(self):
        originalDocs = self.solr.search("doc")
        assert len(originalDocs) == 3
        updateList = []
        for doc in originalDocs:
            updateList.append({"id": doc["id"], "popularity": 5})
        self.solr.add(updateList, fieldUpdates={"popularity": "inc"}, commit=True)

        updatedDocs = self.solr.search("doc")
        assert len(updatedDocs) == 3
        for originalDoc, updatedDoc in zip(originalDocs, updatedDocs, strict=True):
            assert len(updatedDoc.keys()) == len(originalDoc.keys())
            assert updatedDoc["popularity"] == originalDoc["popularity"] + 5
            # TODO: change this to use assertSetEqual:
            assert all(
                updatedDoc[k] == originalDoc[k]
                for k in updatedDoc.keys()
                if k not in ["_version_", "popularity"]
            )

    def test_field_update_set(self):
        originalDocs = self.solr.search("doc")
        updated_popularity = 10
        assert len(originalDocs) == 3
        updateList = []
        for doc in originalDocs:
            updateList.append({"id": doc["id"], "popularity": updated_popularity})
        self.solr.add(updateList, fieldUpdates={"popularity": "set"}, commit=True)

        updatedDocs = self.solr.search("doc")
        assert len(updatedDocs) == 3
        for originalDoc, updatedDoc in zip(originalDocs, updatedDocs, strict=True):
            assert len(updatedDoc.keys()) == len(originalDoc.keys())
            assert updatedDoc["popularity"] == updated_popularity
            # TODO: change this to use assertSetEqual:
            assert all(
                updatedDoc[k] == originalDoc[k]
                for k in updatedDoc.keys()
                if k not in ["_version_", "popularity"]
            )

    def test_field_update_add(self):
        self.solr.add(
            [
                {
                    "id": "multivalued_1",
                    "title": "Multivalued doc 1",
                    "word_ss": ["alpha", "beta"],
                },
                {
                    "id": "multivalued_2",
                    "title": "Multivalued doc 2",
                    "word_ss": ["charlie", "delta"],
                },
            ],
            commit=True,
        )

        originalDocs = self.solr.search("multivalued")
        assert len(originalDocs) == 2
        updateList = []
        for doc in originalDocs:
            updateList.append({"id": doc["id"], "word_ss": ["epsilon", "gamma"]})
        self.solr.add(updateList, fieldUpdates={"word_ss": "add"}, commit=True)

        updatedDocs = self.solr.search("multivalued")
        assert len(updatedDocs) == 2
        for originalDoc, updatedDoc in zip(originalDocs, updatedDocs, strict=True):
            assert len(updatedDoc.keys()) == len(originalDoc.keys())
            assert updatedDoc["word_ss"] == originalDoc["word_ss"] + [
                "epsilon",
                "gamma",
            ]
            # TODO: change this to use assertSetEqual:
            assert all(
                updatedDoc[k] == originalDoc[k]
                for k in updatedDoc.keys()
                if k not in ["_version_", "word_ss"]
            )

    def test_delete(self):
        assert len(self.solr.search("doc")) == 3
        self.solr.delete(id="doc_1", commit=True)
        # delete should default to 'update' handler
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("update/?")

        assert len(self.solr.search("doc")) == 2
        assert len(self.solr.search("type_s:parent")) == 2
        assert len(self.solr.search("type_s:child")) == 3
        assert len(self.solr.search("type_s:grandchild")) == 1
        self.solr.delete(q="price:[0 TO 15]")
        self.solr.delete(q="type_s:parent", commit=True)

        # Test a query that would need to be quoted when using the XML API.
        # Ids with a "<" character will give an error using v3.9.0 or earlier
        self.solr.delete(id="cats<dogs")
        # These will delete too much when using v3.9.0 or earlier.
        self.solr.delete(q="id:*</query><query> id:999 AND id:9999")
        self.solr.delete(id="doc_4</id><id>doc_3", commit=True)

        # one simple doc should remain
        # parent documents were also deleted but children remain as orphans
        assert len(self.solr.search("doc")) == 1
        assert len(self.solr.search("type_s:parent")) == 0
        assert len(self.solr.search("type_s:child")) == 3
        self.solr.delete(q="type_s:child OR type_s:grandchild", commit=True)

        assert len(self.solr.search("*:*")) == 1
        self.solr.delete(q="*:*", commit=True)
        assert len(self.solr.search("*:*")) == 0

        # Test delete() with `id' being a list.
        # Solr's ability to delete parent/children docs by id is simply assumed
        # and not what's under test here.
        def leaf_doc(doc):
            return "price" in doc and NESTED_DOC_KEY not in doc

        to_delete_docs = list(filter(leaf_doc, self.docs))
        to_delete_ids = [doc["id"] for doc in to_delete_docs]

        self.solr.add(to_delete_docs)
        self.solr.commit()

        leaf_q = "price:[* TO *]"
        assert len(self.solr.search(leaf_q)) == len(to_delete_docs)
        # Extract a random doc from the list, to later check it wasn't deleted.
        graced_doc_id = to_delete_ids.pop(
            random.randint(0, len(to_delete_ids) - 1)  # NOQA: S311
        )
        self.solr.delete(id=to_delete_ids, commit=True)
        # There should be only one left, our graced id
        assert len(self.solr.search(leaf_q)) == 1
        assert len(self.solr.search("id:%s" % graced_doc_id)) == 1
        # Now we can wipe the graced document too. None should be left.
        self.solr.delete(id=graced_doc_id, commit=True)
        assert len(self.solr.search(leaf_q)) == 0

        # Can't delete when the list of documents is empty
        msg = "The list of documents to delete was empty."
        with pytest.raises(ValueError, match=msg):
            self.solr.delete(id=[None, None, None])
        with pytest.raises(ValueError, match=msg):
            self.solr.delete(id=[None])

        # Need at least one of either `id' or `q'
        msg = 'You must specify "id" or "q".'
        with pytest.raises(ValueError, match=msg):
            self.solr.delete()
        # Can't have both.
        msg = 'You many only specify "id" OR "q", not both.'
        with pytest.raises(ValueError, match=msg):
            self.solr.delete(id="foo", q="bar")

        # delete should support custom handlers
        with pytest.raises(SolrError):
            self.solr.delete(id="doc_1", handler="fakehandler", commit=True)
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("fakehandler")

    def test_delete__accepts_string_and_integer_values(self):
        """
        Ensure self.solr.delete() accepts both string and integer values for `id`
        and `q` parameters without raising XML serialization errors.

        Previously, passing an integer value caused a TypeError because
        `xml.etree.ElementTree` requires element.text to be a string. This test
        verifies that integer inputs are correctly cast to strings before
        building the delete XML payload.

        Regression test for:
        https://github.com/django-haystack/pysolr/issues/489
        """
        self.solr.add([{"id": "101", "title": "Sample doc 101"}], commit=True)
        self.solr.add([{"id": "102", "title": "Sample doc 102"}], commit=True)
        self.solr.add([{"id": "103", "title": "Sample doc 103"}], commit=True)
        self.solr.add([{"id": "104", "title": "Sample doc 104"}], commit=True)

        # Delete using string ID
        self.solr.delete(id="101", commit=True)

        # Delete using integer ID (should not raise TypeError)
        self.solr.delete(id=102, commit=True)

        # Delete using string value with `q`
        self.solr.delete(q="103", commit=True)

        # Delete using integer value with `q` (should not raise TypeError)
        self.solr.delete(q=104, commit=True)

    def test_commit(self):
        assert len(self.solr.search("doc")) == 3
        self.solr.add([{"id": "doc_6", "title": "Newly added doc"}])
        assert len(self.solr.search("doc")) == 3
        self.solr.commit()
        # commit should default to 'update' handler
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("update/?")
        assert len(self.solr.search("doc")) == 4

    def test_can_handles_default_commit_policy(self):
        expected_commits = [False, True, False]
        commit_arg = [False, True, None]

        for expected_commit, arg in zip(expected_commits, commit_arg, strict=True):
            self.solr.add([{"id": "doc_6", "title": "Newly added doc"}], commit=arg)
            args, _ = self.solr._send_request.call_args
            committing_in_url = "commit" in args[1]
            assert expected_commit == committing_in_url

    def test_overwrite(self):
        assert len(self.solr.search("id:doc_overwrite_1")) == 0
        self.solr.add(
            [
                {"id": "doc_overwrite_1", "title": "Kim is awesome."},
                {"id": "doc_overwrite_1", "title": "Kim is more awesome."},
            ],
            overwrite=False,
            commit=True,
        )
        assert len(self.solr.search("id:doc_overwrite_1")) == 2

        # commit should support custom handlers
        with pytest.raises(SolrError):
            self.solr.commit(handler="fakehandler")
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("fakehandler")

    def test_optimize(self):
        # Make sure it doesn't blow up. Side effects are hard to measure. :/
        assert len(self.solr.search("doc")) == 3
        self.solr.add([{"id": "doc_6", "title": "Newly added doc"}], commit=False)
        assert len(self.solr.search("doc")) == 3
        self.solr.optimize()
        # optimize should default to 'update' handler
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("update/?")
        assert len(self.solr.search("doc")) == 4

        # optimize should support custom handlers
        with pytest.raises(SolrError):
            self.solr.optimize(handler="fakehandler")
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("fakehandler")

    def test_extract(self):
        fake_f = StringIO(
            """
            <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="haystack-test" content="test 1234">
                    <title>Test Title ☃&#x2603;</title>
                </head>
                    <body>foobar</body>
            </html>
        """
        )
        fake_f.name = "test.html"
        extracted = self.solr.extract(fake_f)
        # extract should default to 'update/extract' handler
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("update/extract")

        # extract should support custom handlers
        with pytest.raises(SolrError):
            self.solr.extract(fake_f, handler="fakehandler")
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("fakehandler")

        # Verify documented response structure:
        assert "contents" in extracted
        assert "metadata" in extracted

        assert "foobar" in extracted["contents"]

        m = extracted["metadata"]

        assert "file" in m["stream_name"]

        assert "haystack-test" in m, "HTML metadata should have been extracted!"
        assert ["test 1234"] == m["haystack-test"]

        # Note the underhanded use of a double snowman to verify both that Tika
        # correctly decoded entities and that our UTF-8 characters survived the
        # round-trip:
        assert ["Test Title ☃☃"] == m["title"]

    def test_extract_special_char_in_filename(self):
        fake_f = StringIO(
            """
            <html>
                <head>
                    <meta charset="utf-8">
                    <meta name="haystack-test" content="test 1234">
                    <title>Test Title ☃&#x2603;</title>
                </head>
                    <body>foobar</body>
            </html>
        """
        )
        fake_f.name = "test☃.html"
        extracted = self.solr.extract(fake_f)
        # extract should default to 'update/extract' handler
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("update/extract")

        # extract should support custom handlers
        with pytest.raises(SolrError):
            self.solr.extract(fake_f, handler="fakehandler")
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("fakehandler")

        # Verify documented response structure:
        assert "contents" in extracted
        assert "metadata" in extracted

        assert "foobar" in extracted["contents"]

        m = extracted["metadata"]

        assert "file" in m["stream_name"]

        assert "haystack-test" in m, "HTML metadata should have been extracted!"
        assert ["test 1234"] == m["haystack-test"]

        # Note the underhanded use of a double snowman to verify both that Tika
        # correctly decoded entities and that our UTF-8 characters survived the
        # round-trip:
        assert ["Test Title ☃☃"] == m["title"]

    def test_full_url(self):
        self.solr.url = "http://localhost:8983/solr/core0"
        full_url = self.solr._create_full_url(path="/update")

        # Make sure trailing and leading slashes do not collide:
        assert full_url == "http://localhost:8983/solr/core0/update"

    def test_request_handler(self):
        before_test_use_qt_param = self.solr.use_qt_param
        before_test_search_handler = self.solr.search_handler

        self.solr.use_qt_param = True

        self.solr.search("my query")
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("select")

        self.solr.search("my", search_handler="/autocomplete")
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("select")
        assert args[1].find("qt=%2Fautocomplete") >= 0

        self.solr.search_handler = "/autocomplete"

        self.solr.search("my")
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("select")
        assert args[1].find("qt=%2Fautocomplete") >= 0

        self.solr.use_qt_param = False
        # will change the path, so expect a 404
        with pytest.raises(SolrError):
            self.solr.search("my")
        args, _kwargs = self.solr._send_request.call_args
        assert args[1].startswith("/autocomplete")
        assert args[1].find("qt=%2Fautocomplete") < 0

        # reset the values to what they were before the test
        self.solr.use_qt_param = before_test_use_qt_param
        self.solr.search_handler = before_test_search_handler

    def test_ping(self):
        self.solr.ping()
        with pytest.raises(SolrError):
            self.solr.ping(handler="fakehandler")


class SolrCommitByDefaultTestCase(unittest.TestCase, SolrTestCaseMixin):
    def setUp(self):
        self.solr = self.get_solr("core0", always_commit=True)
        self.docs = [
            {"id": "doc_1", "title": "Newly added doc"},
            {"id": "doc_2", "title": "Another example doc"},
        ]

        # Ensure the index is completely reset before each test run
        self.solr.delete(q="*:*", commit=True)

    def test_does_not_require_commit(self):
        # add should not require commit arg
        self.solr.add(self.docs)

        assert len(self.solr.search("doc")) == 2
        assert len(self.solr.search("example")) == 1

        # update should not require commit arg
        self.docs[0]["title"] = "Updated Doc"
        self.docs[1]["title"] = "Another example updated doc"
        self.solr.add(self.docs, fieldUpdates={"title": "set"})
        assert len(self.solr.search("updated")) == 2
        assert len(self.solr.search("example")) == 1

        # delete should not require commit arg
        self.solr.delete(q="*:*")
        assert len(self.solr.search("*")) == 0

    def test_can_handles_default_commit_policy(self):
        self.solr._send_request = Mock(wraps=self.solr._send_request)
        expected_commits = [False, True, True]
        commit_arg = [False, True, None]

        for expected_commit, arg in zip(expected_commits, commit_arg, strict=True):
            self.solr.add(self.docs, commit=arg)
            args, _ = self.solr._send_request.call_args
            committing_in_url = "commit" in args[1]
            assert expected_commit == committing_in_url
