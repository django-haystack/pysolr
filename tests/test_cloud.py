# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import datetime
import unittest
from io import StringIO
from xml.etree import ElementTree

from pysolr import (IS_PY3, Results, Solr, SolrCloud, SolrError, ZooKeeper,
                    clean_xml_string, force_bytes, force_unicode, json,
                    safe_urlencode, sanitize, unescape_html)

from .test_client import SolrTestCase
from .utils import start_solr_cloud

try:
    from urllib.parse import unquote_plus
except ImportError:
    from urllib import unquote_plus

try:
    from kazoo.client import KazooClient
except ImportError:
    KazooClient = None


@unittest.skipUnless(KazooClient is not None, 'kazoo is not installed; skipping SolrCloud tests')
class SolrCloudTestCase(SolrTestCase):
    @classmethod
    def setUpClass(cls):
        start_solr_cloud()

    def setUp(self):
        super(SolrTestCase, self).setUp()
        self.zk = ZooKeeper("localhost:9982")
        self.default_solr = SolrCloud(self.zk, "core0")
        # Short timeouts.
        self.solr = SolrCloud(self.zk, "core0", timeout=2)
        self.docs = [
            {
                'id': 'doc_1',
                'title': 'Example doc 1',
                'price': 12.59,
                'popularity': 10,
            },
            {
                'id': 'doc_2',
                'title': 'Another example ☃ doc 2',
                'price': 13.69,
                'popularity': 7,
            },
            {
                'id': 'doc_3',
                'title': 'Another thing',
                'price': 2.35,
                'popularity': 8,
            },
            {
                'id': 'doc_4',
                'title': 'doc rock',
                'price': 99.99,
                'popularity': 10,
            },
            {
                'id': 'doc_5',
                'title': 'Boring',
                'price': 1.12,
                'popularity': 2,
            },
        ]

        # Clear it.
        self.solr.delete(q='*:*')

        # Index our docs. Yes, this leans on functionality we're going to test
        # later & if it's broken, everything will catastrophically fail.
        # Such is life.
        self.solr.add(self.docs)

    def test_init(self):
        self.assertTrue(self.default_solr.url.endswith('/solr/core0'))
        self.assertTrue(isinstance(self.default_solr.decoder, json.JSONDecoder))
        self.assertEqual(self.default_solr.timeout, 60)

        self.assertTrue(self.solr.url.endswith('/solr/core0'))
        self.assertTrue(isinstance(self.solr.decoder, json.JSONDecoder))
        self.assertEqual(self.solr.timeout, 2)

    def test__create_full_url(self):
        pass # tested within parent SolrTestCase

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
