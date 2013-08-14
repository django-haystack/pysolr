# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
from unittest.util import safe_repr

from pysolr import SolrCoreAdmin, json

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class SolrCoreAdminTestCase(unittest.TestCase):
    def assertIn(self, member, container, msg=None):
        """
        Just like self.assertTrue(a in b), but with a nicer default message.
        Backported from Python 2.7 unittest library.
        """
        if member not in container:
            standardMsg = '%s not found in %s' % (safe_repr(member),
                                                  safe_repr(container))
            self.fail(self._formatMessage(msg, standardMsg))


    def setUp(self):
        super(SolrCoreAdminTestCase, self).setUp()
        self.solr_admin = SolrCoreAdmin('http://localhost:8080/solr/admin/cores')

    def create(self, core_name):
        return self.solr_admin.create(core_name, instance_dir=os.path.join(
            os.path.dirname(__file__), 'fixtures'))

    def test_status(self):
        self.assertIn('<int name="status">0</int>', self.solr_admin.status())
        self.assertIn('<int name="status">0</int>', self.solr_admin.status(core='core0'))

    def test_create(self):
        self.assertIn('<int name="status">0</int>', self.create('wheatley'))

    def test_reload(self):
        self.assertIn('<int name="status">0</int>', self.solr_admin.reload('wheatley'))

    def test_rename(self):
        self.create('wheatley')
        self.assertIn('<int name="status">0</int>', self.solr_admin.rename('wheatley', 'rick'))

    def test_swap(self):
        self.create('wheatley')
        self.create('rick')
        self.assertIn('<int name="status">0</int>', self.solr_admin.swap('wheatley', 'rick'))

    def test_unload(self):
        self.create('wheatley')
        self.assertIn('<int name="status">0</int>', self.solr_admin.unload('wheatley'))

    def test_load(self):
        self.assertRaises(NotImplementedError, self.solr_admin.load, 'wheatley')
