from unittest.mock import Mock
from urllib.parse import unquote_plus

import pytest
import requests

from pysolr import (
    Results,
    SolrError,
    clean_xml_string,
    force_bytes,
    force_unicode,
    safe_urlencode,
    sanitize,
    unescape_html,
)
from tests.base import BaseSolrClientTests, SolrTestCaseMixin


class TestUtils:
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
            == "test=Hello \u2603!&test=Helllo world!"
        )
        assert (
            force_unicode(
                unquote_plus(
                    safe_urlencode({"test": ("Hello ☃!", "Helllo world!")}, True)
                )
            )
            == "test=Hello \u2603!&test=Helllo world!"
        )

    def test_sanitize(self):
        assert (
            sanitize(
                "\x00\x01\x02\x03\x04\x05\x06\x07\x08\x0b\x0c\x0e\x0f\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19h\x1ae\x1bl\x1cl\x1do\x1e\x1f"  # NOQA: E501
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
        assert clean_xml_string("\x00\x0b\x0d\uffff") == "\x0d"


class TestResults:
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


class TestSolr(SolrTestCaseMixin, BaseSolrClientTests):
    """Runs the full Test suite against Solr standalone mode."""

    def test__send_request_to_bad_path(self):
        """
        Verify that a connection failure to an unreachable Solr URL raises
        SolrError and preserves the original requests.exceptions.ConnectionError
        as the chained cause.
        """
        # Test a non-existent URL:
        self.solr.url = "http://127.0.0.1:56789/whatever"

        with pytest.raises(SolrError) as ctx:
            self.solr._send_request("get", "select/?q=doc&wt=json")

        # The raised SolrError should preserve the original
        # requests ConnectionError as its cause
        assert ctx.value.__cause__ is not None
        assert isinstance(ctx.value.__cause__, requests.exceptions.ConnectionError)

    def test_send_request_to_bad_core(self):
        # Test a bad core on a valid URL:
        self.solr.url = "http://localhost:8983/solr/bad_core"
        with pytest.raises(SolrError):
            self.solr._send_request("get", "select/?q=doc&wt=json")


class TestSolrCommitByDefault(SolrTestCaseMixin):
    def setup_method(self):
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
