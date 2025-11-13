import unittest

from pysolr import SolrCloud, SolrError, ZooKeeper, json

from .test_client import SolrTestCase

try:
    from kazoo.client import KazooClient
except ImportError:
    KazooClient = None


@unittest.skipUnless(
    KazooClient is not None, "kazoo is not installed; skipping SolrCloud tests"
)
class SolrCloudTestCase(SolrTestCase):
    def assertURLStartsWith(self, url, path):
        node_urls = self.zk.getHosts("core0")
        self.assertIn(url, {"%s/%s" % (node_url, path) for node_url in node_urls})

    def get_solr(self, collection, timeout=60):
        # TODO: make self.zk a memoized property:
        if not getattr(self, "zk", None):
            self.zk = ZooKeeper("localhost:9992", timeout=timeout, max_retries=15)

        return SolrCloud(self.zk, collection, timeout=timeout)

    def test_init(self):
        self.assertTrue(self.solr.url.endswith("/solr/core0"))
        self.assertIsInstance(self.solr.decoder, json.JSONDecoder)
        self.assertEqual(self.solr.timeout, 60)

        custom_solr = self.get_solr("core0", timeout=17)
        self.assertEqual(custom_solr.timeout, 17)

    def test_custom_results_class(self):
        solr = SolrCloud(self.zk, "core0", results_cls=dict)

        results = solr.search(q="*:*")
        self.assertIsInstance(results, dict)
        self.assertIn("responseHeader", results)
        self.assertIn("response", results)

    def test__send_request_to_bad_path(self):
        unittest.SkipTest("This test makes no sense in a SolrCloud world")

    def test_send_request_to_bad_core(self):
        unittest.SkipTest("This test makes no sense in a SolrCloud world")

    def test_invalid_collection(self):
        self.assertRaises(SolrError, SolrCloud, self.zk, "core12345")

    def test__create_full_url(self):
        # Nada.
        self.assertRegex(
            self.solr._create_full_url(path=""),
            r"http://localhost:89../solr/core0$",
        )
        # Basic path.
        self.assertRegex(
            self.solr._create_full_url(path="pysolr_tests"),
            r"http://localhost:89../solr/core0/pysolr_tests$",
        )
        # Leading slash (& making sure we don't touch the trailing slash).
        self.assertRegex(
            self.solr._create_full_url(path="/pysolr_tests/select/?whatever=/"),
            r"http://localhost:89../solr/core0/pysolr_tests/select/\?whatever=/",
        )
