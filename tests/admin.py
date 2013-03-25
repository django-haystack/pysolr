# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pysolr import SolrCoreAdmin, json

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class SolrCoreAdminTestCase(unittest.TestCase):
    def setUp(self):
        super(SolrCoreAdminTestCase, self).setUp()
        self.solr_admin = SolrCoreAdmin('http://localhost:8983/solr/admin/cores')

    def test_status(self):
        self.assertTrue('name="defaultCoreName"' in self.solr_admin.status())
        self.assertTrue('<int name="status">' in self.solr_admin.status(core='core0'))

    def test_create(self):
        self.assertTrue('<int name="status">0</int>' in self.solr_admin.create('wheatley'))

    def test_reload(self):
        self.assertTrue('<int name="status">0</int>' in self.solr_admin.reload('wheatley'))

    def test_rename(self):
        self.solr_admin.create('wheatley')
        self.assertTrue('<int name="status">0</int>' in self.solr_admin.rename('wheatley', 'rick'))

    def test_swap(self):
        self.solr_admin.create('wheatley')
        self.solr_admin.create('rick')
        self.assertTrue('<int name="status">0</int>' in self.solr_admin.swap('wheatley', 'rick'))

    def test_unload(self):
        self.solr_admin.create('wheatley')
        self.assertTrue('<int name="status">0</int>' in self.solr_admin.unload('wheatley'))

    def test_load(self):
        self.assertRaises(NotImplementedError, self.solr_admin.load, 'wheatley')