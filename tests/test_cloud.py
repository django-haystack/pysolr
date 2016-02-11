# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import unittest

from pysolr import SolrCloud, ZooKeeper

from .test_client import SolrTestCase
from .utils import start_solr_cloud

try:
    from kazoo.client import KazooClient
except ImportError:
    KazooClient = None


@unittest.skipUnless(KazooClient is not None, 'kazoo is not installed; skipping SolrCloud tests')
class SolrCloudTestCase(SolrTestCase):
    @classmethod
    def setUpClass(cls):
        start_solr_cloud()

    def get_solr(self, collection, timeout=60):
        # TODO: make self.zk a memoized property:
        if not getattr(self, 'zk', None):
            self.zk = ZooKeeper("localhost:9982")

        return SolrCloud(self.zk, "core0", timeout=timeout)

    def tearDown(self):
        super(SolrCloudTestCase, self).tearDown()
        del self.zk

    def test_init(self):
        self.assertTrue(self.default_solr.url.endswith('/solr/core0'))
        self.assertTrue(isinstance(self.default_solr.decoder, json.JSONDecoder))
        self.assertEqual(self.default_solr.timeout, 60)

        self.assertTrue(self.solr.url.endswith('/solr/core0'))
        self.assertTrue(isinstance(self.solr.decoder, json.JSONDecoder))
        self.assertEqual(self.solr.timeout, 2)

    def test__create_full_url(self):
        pass  # tested within parent SolrTestCase

    # removes test for invalid URL from parent SolrTestCase.test__send_request
    # which is not relevant in SolrCloud
    def test__send_request(self):
        # Test a valid request.
        resp_body = self.solr._send_request('GET', 'select/?q=doc&wt=json')
        self.assertTrue('"numFound":3' in resp_body)

        # Test a lowercase method & a body.
        xml_body = '<add><doc><field name="id">doc_12</field><field name="title">Whee! ☃</field></doc></add>'
        resp_body = self.solr._send_request('POST', 'update/?commit=true', body=xml_body, headers={
            'Content-type': 'text/xml; charset=utf-8',
        })
        self.assertTrue('<int name="status">0</int>' in resp_body)
