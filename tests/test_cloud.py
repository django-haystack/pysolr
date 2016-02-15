# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest

from pysolr import SolrCloud, ZooKeeper, json, SolrError

from .test_client import SolrTestCase

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

        return SolrCloud(self.zk, "core0", timeout=timeout)

    def test_init(self):
        self.assertTrue(self.default_solr.url.endswith('/solr/core0'))
        self.assertTrue(isinstance(self.default_solr.decoder, json.JSONDecoder))
        self.assertEqual(self.default_solr.timeout, 60)

        self.assertTrue(self.solr.url.endswith('/solr/core0'))
        self.assertTrue(isinstance(self.solr.decoder, json.JSONDecoder))
        self.assertEqual(self.solr.timeout, 2)

    @unittest.expectedFailure
    def test__send_request_to_bad_path(self):
        super(SolrCloudTestCase, self).test__send_request_to_bad_path()

    @unittest.expectedFailure
    def test_send_request_to_bad_core(self):
        super(SolrCloudTestCase, self).test_send_request_to_bad_core()
