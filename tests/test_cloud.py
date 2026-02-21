import contextlib
import re
from typing import ClassVar

import pytest

from pysolr import SolrCloud, SolrError, ZooKeeper, json
from tests.base import BaseSolrClientTests, SolrTestCaseMixin

try:
    from kazoo.exceptions import KazooException
except ImportError:
    KazooException = None


class ProxyZooKeeper(ZooKeeper):
    """
    A ZooKeeper wrapper that rewrites SolrCloud live node URLs so they are
    accessible from the host machine during local development and testing.

    Solr nodes inside Docker register themselves using internal container
    addresses such as:

        solr-node0:8983
        solr-node1:8983

    These are not reachable from the host. We override `getHosts()` and map
    those internal URLs to the published localhost ports:

        solr-node0:8983  →  localhost:8993   (host port)
        solr-node1:8983  →  localhost:8994   (host port)

    (From docker/docker-compose-solr.yml):
        solr-node0 -> "8993:8983"
        solr-node1 -> "8994:8983"

    With this mapping in place, all SolrCloud operations—random node selection,
    leader routing, updates, and extraction—automatically use host-accessible URLs
    without modifying any internals.
    """

    PORT_MAP: ClassVar[dict] = {
        "solr-node0:8983": "localhost:8993",
        "solr-node1:8983": "localhost:8994",
    }

    def getHosts(self, collname, only_leader=False, seen_aliases=None):
        """
        Return host-accessible Solr node URLs by mapping container hostnames
        (solr-node0:8983, solr-node1:8983) to their localhost port bindings.
        """
        hosts = super().getHosts(collname, only_leader, seen_aliases)

        mapped = []
        for h in hosts:
            for original, new in self.PORT_MAP.items():
                h = h.replace(original, new)
            mapped.append(h)
        return mapped


@pytest.mark.skipif(
    KazooException is None,
    reason="kazoo is not installed; skipping SolrCloud tests",
)
class TestSolrCloud(SolrTestCaseMixin, BaseSolrClientTests):
    """Runs the full Test suite against Solr cloud mode."""

    @classmethod
    def setup_class(cls):
        """
        Initialize a shared ProxyZooKeeper instance for all test methods.
        """
        cls.zk = ProxyZooKeeper("localhost:2181", timeout=60, max_retries=15)

    def assertURLStartsWith(self, url, path):
        node_urls = self.zk.getHosts("core0")
        assert url in {"%s/%s" % (node_url, path) for node_url in node_urls}

    def get_solr(self, collection, timeout=60):
        return SolrCloud(self.zk, collection, timeout=timeout)

    def test_init(self):
        assert self.solr.url.endswith("/solr/core0")
        assert isinstance(self.solr.decoder, json.JSONDecoder)
        assert self.solr.timeout == 60

        custom_solr = self.get_solr("core0", timeout=17)
        assert custom_solr.timeout == 17

    def test_custom_results_class(self):
        solr = SolrCloud(self.zk, "core0", results_cls=dict)

        results = solr.search(q="*:*")
        assert isinstance(results, dict)
        assert "responseHeader" in results
        assert "response" in results

    def test_invalid_collection(self):
        with pytest.raises(SolrError):
            SolrCloud(self.zk, "core12345")

    def test__create_full_url(self):
        # Nada.
        assert re.search(
            r"http://localhost:89../solr/core0$", self.solr._create_full_url(path="")
        )
        # Basic path.
        assert re.search(
            r"http://localhost:89../solr/core0/pysolr_tests$",
            self.solr._create_full_url(path="pysolr_tests"),
        )
        # Leading slash (& making sure we don't touch the trailing slash).
        assert re.search(
            r"http://localhost:89../solr/core0/pysolr_tests/select/\?whatever=/",
            self.solr._create_full_url(path="/pysolr_tests/select/?whatever=/"),
        )

    @classmethod
    def teardown_class(cls):
        """
        Cleanly shut down the shared ProxyZooKeeper instance after all tests.
        """
        with contextlib.suppress(KazooException):
            cls.zk.zk.stop()
            cls.zk.zk.close()
