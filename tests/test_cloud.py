# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest
import time
import requests

from pysolr import SolrCloud, SolrError, ZooKeeper, json

from .test_client import SolrTestCase
from tests import utils as test_utils

try:
    from kazoo.client import KazooClient
except ImportError:
    KazooClient = None


@unittest.skipUnless(KazooClient is not None, 'kazoo is not installed; skipping SolrCloud tests')
class SolrCloudTestCase(SolrTestCase):
    def assertURLStartsWith(self, url, path):
        node_urls = self.zk.getHosts('core0')
        self.assertIn(url, {'%s/%s' % (node_url, path) for node_url in node_urls})

    def get_solr(self, collection, timeout=60):
        # TODO: make self.zk a memoized property:
        if not getattr(self, 'zk', None):
            self.zk = ZooKeeper("localhost:9992")

        return SolrCloud(self.zk, collection, timeout=timeout)

    def test_init(self):
        self.assertTrue(self.solr.url.endswith('/solr/core0'))
        self.assertTrue(isinstance(self.solr.decoder, json.JSONDecoder))
        self.assertEqual(self.solr.timeout, 60)

        custom_solr = self.get_solr("core0", timeout=17)
        self.assertEqual(custom_solr.timeout, 17)

    def test_custom_results_class(self):
        solr = SolrCloud(self.zk, "core0", results_cls=dict)

        results = solr.search(q='*:*')
        assert isinstance(results, dict)
        assert 'responseHeader' in results
        assert 'response' in results

    def test__send_request_to_bad_path(self):
        # This test makes no sense in a SolrCloud world.
        pass

    def test_send_request_to_bad_core(self):
        # This test makes no sense in a SolrCloud world, see test_invalid_collection
        pass

    def test_invalid_collection(self):
        self.assertRaises(SolrError, SolrCloud, self.zk, "core12345")

    def test__create_full_url(self):
        # Nada.
        self.assertRegexpMatches(self.solr._create_full_url(path=''), r"http://localhost:89../solr/core0$")
        # Basic path.
        self.assertRegexpMatches(self.solr._create_full_url(path='pysolr_tests'), r"http://localhost:89../solr/core0/pysolr_tests$")
        # Leading slash (& making sure we don't touch the trailing slash).
        self.assertRegexpMatches(self.solr._create_full_url(path='/pysolr_tests/select/?whatever=/'), r"http://localhost:89../solr/core0/pysolr_tests/select/\?whatever=/")

    def test_failover(self):
        def check_port(port):
            try:
                requests.get("http://localhost:%s" % port, timeout=0.3)
                return True
            except requests.exceptions.Timeout:
                return False

        monkey_process = test_utils.start_chaos_monkey()

        start = time.time()
        RUN_LENGTH=10
        count=0
        now=start
        failures=0
        while now < start + RUN_LENGTH:
            results = self.solr.search('doc')
            self.assertEqual(len(results), 3)
            now=int(time.time())
            if int(time.time()) > now:
                print(":"),
            if not check_port(8993):
                failures+=1
            if not check_port(8994):
                failures+=1
            count+=1
        self.assertGreater(failures, 0, "At least one port request failure recorded")
        test_utils.stop_monkeying(monkey_process)

    # this test shows that Solr will fail if both nodes are down
    def test_failover_falldown(self):
        monkey_process = test_utils.start_disaster_monkey()

        start = time.time()
        RUN_LENGTH=6
        count=0
        before_failure=0
        after_failure=0
        now=start
        failures=0

        solr = SolrCloud(self.zk, "core0", timeout=0.3)
        while now < start + RUN_LENGTH:
            try:
                results = solr.search('doc')
                now=int(time.time())
                if int(time.time()) > now:
                    print(":"),
                if failures == 0:
                    before_failure+=1
                else:
                    after_failure+=1
                count+=1
            except SolrError:
                failures+=1
                now=int(time.time())
                if int(time.time()) > now:
                    print("x"),
        self.assertGreater(failures, 0, "At least one failure recorded")
        self.assertGreater(after_failure, 0, "At least one successful request after failures")
        test_utils.stop_monkeying(monkey_process)
