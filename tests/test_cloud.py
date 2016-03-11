# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest
import time
import requests
import threading

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
        return SolrCloud(self.zk, collection, timeout=timeout)

    @classmethod
    def setUpClass(cls):
        cls.zk = ZooKeeper("localhost:9992")

    @classmethod
    def tearDownClass(cls):
        # Clear out Zookeeper to make tests close cleanly
        del cls.zk

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

    # Confirm that we can still serve requests when one, or other node is down
    # (note, we must confirm that a node has recovered before taking the next one down)
    def test_failover(self):

        test_thread = CloudTestThread(self.zk)
        test_thread.start()

        time.sleep(2)

        test_utils.stop_solr(8993)
        test_utils.wait_for_down(self.zk, "localhost:8993_solr")

        time.sleep(2)

        test_utils.start_solr("cloud-node0", 8993)
        test_utils.wait_for_up(self.zk, "core0", "http://localhost:8993/solr")

        test_utils.wait_for_leader(self.zk, "core0")

        test_utils.stop_solr(8994)
        test_utils.wait_for_down(self.zk, "localhost:8994_solr")

        time.sleep(2)

        test_utils.start_solr("cloud-node1", 8994)
        test_utils.wait_for_up(self.zk, "core0", "http://localhost:8994/solr")
        test_utils.wait_for_leader(self.zk, "core0")
        time.sleep(2)

        success, timeouts, exceptions = test_thread.stop()

        self.assertEqual(timeouts, 0)
        self.assertEqual(exceptions, 0)
        self.assertGreater(success, 0)

    # Confirm that we fail when more than both nodes go down, and that we recover when they are back
    def test_falldown(self):
        test_thread = CloudTestThread(self.zk)
        test_thread.start()

        time.sleep(2)

        self.assertEqual(test_thread.exceptions, 0)

        test_utils.stop_solr(8993)
        test_utils.stop_solr(8994)
        test_utils.wait_for_down(self.zk, "localhost:8993_solr")
        test_utils.wait_for_down(self.zk, "localhost:8994_solr")

        time.sleep(2)

        test_utils.start_solr("cloud-node0", 8993)
        test_utils.start_solr("cloud-node1", 8994)
        test_utils.wait_for_up(self.zk, "core0", "http://localhost:8993/solr")
        test_utils.wait_for_up(self.zk, "core0", "http://localhost:8994/solr")
        self.assertGreater(test_thread.exceptions, 0)
        test_thread.exceptions = 0
        test_utils.wait_for_leader(self.zk, "core0")
        time.sleep(2)

        success, timeouts, exceptions = test_thread.stop()

        self.assertEqual(timeouts, 0)
        self.assertEqual(exceptions, 0)
        self.assertGreater(success, 0)

    # Confirm that we survive ZK going down, for reads
    def test_zk_failure(self):
        return

        test_thread = CloudTestThread(self.zk)
        test_thread.start()

        time.sleep(2)

        self.assertEqual(test_thread.exceptions, 0)

        test_utils.stop_solr(8992)
        test_utils.wait_for_down(self.zk, "localhost:8992_solr")
        time.sleep(2)

        test_utils.start_solr("cloud-node0", 8992)
        test_utils.wait_for_up(self.zk, None, "localhost:8992_solr")
        time.sleep(2)

        success, timeouts, exceptions = test_thread.stop()

        self.assertEqual(timeouts, 0)
        self.assertEqual(exceptions, 0)
        self.assertGreater(success, 0)



class CloudTestThread(threading.Thread):
    def __init__(self, zk):
        threading.Thread.__init__(self)
        self.zk = zk
        self.should_stop = False
        self.success = 0
        self.exceptions = 0
        self.timeouts = 0

    def stop(self):
        self.should_stop = True
        return (self.success, self.timeouts, self.exceptions)

    def run(self):
        solr = SolrCloud(self.zk, "core0", timeout=0.3)

        while not self.should_stop:
            try:
                results = solr.search('doc')
                self.success += 1
            except requests.exceptions.Timeout:
                self.timeouts += 1
            except Exception as e:
                self.exceptions += 1
