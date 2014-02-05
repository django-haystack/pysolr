# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from pysolr import SolrCoreAdmin, json
import re

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class SolrCoreAdminTestCase(unittest.TestCase):
    def setUp(self):
        super(SolrCoreAdminTestCase, self).setUp()
        self.solr_admin = SolrCoreAdmin('http://localhost:8983')
        self.solr_admin.create('test_core', instance_dir="collection1")

    def tearDown(self):
        try:
            self.solr_admin.unload('test_core')
        except:
            # already cleaned up
            pass

    def test_status(self):
        self.assertTrue('name="defaultCoreName"' in self.solr_admin.status())
        self.assertTrue('<int name="status">' in self.solr_admin.status(core='test_core'))

    def test_create(self):
        result = self.solr_admin.create('wheatley', instance_dir="collection1")
        self.assertTrue('<int name="status">0</int>' in result)
        self.assertTrue('<str name="core">wheatley</str>' in result)
        # cleanup
        self.solr_admin.unload('wheatley')

    def test_reload(self):
        self.assertTrue('<int name="status">0</int>' in self.solr_admin.reload('test_core'))

    def test_rename(self):
        self.assertTrue('<int name="status">0</int>' in self.solr_admin.rename('test_core', 'rick'))
        res = self.solr_admin.status()
        self.assertTrue('<lst name="rick">' in res)
        self.assertFalse('<lst name="test_core">' in res)

    def _get_uptime(self, core):
        self.solr_admin.status(core)
        uptime_pattern = r'<long name="uptime">(?P<uptime>\d+)</long>'
        res = re.search(
            uptime_pattern,
            self.solr_admin.status(core)
        ).groupdict()
        if res:
            return int(res['uptime'])
        else:
            None
    
    def test_swap(self):
        self.solr_admin.create('rick', instance_dir="collection1")
        #TODO find a better way to assert the swap than uptime
        test_up = self._get_uptime('test_core')
        rick_up = self._get_uptime('rick')
        self.assertTrue(test_up > rick_up)
        self.assertTrue('<int name="status">0</int>' in self.solr_admin.swap('test_core', 'rick'))
        res = self.solr_admin.status()
        self.assertTrue('<lst name="rick">' in res)
        self.assertTrue('<lst name="test_core">' in res)
        test_up = self._get_uptime('test_core')
        rick_up = self._get_uptime('rick')
        self.assertTrue(test_up < rick_up)

        # cleanup
        self.solr_admin.unload('rick')

    def test_unload(self):
        self.solr_admin.create('wheatley', instance_dir="collection1")
        self.assertTrue('<int name="status">0</int>' in self.solr_admin.unload('wheatley'))

    def test_load(self):
        self.assertRaises(NotImplementedError, self.solr_admin.load, 'wheatley')

if __name__ == '__main__':
    unittest.main()
