import unittest

from pysolr import SolrCoreAdmin


class SolrCoreAdminTestCase(unittest.TestCase):
    def setUp(self):
        super(SolrCoreAdminTestCase, self).setUp()
        self.solr_admin = SolrCoreAdmin("http://localhost:8983/solr/admin/cores")

    def test_status(self):
        self.assertIn('name="defaultCoreName"', self.solr_admin.status())
        self.assertIn('<int name="status">', self.solr_admin.status(core="core0"))

    def test_create(self):
        self.assertIn('<int name="status">0</int>', self.solr_admin.create("wheatley"))

    def test_reload(self):
        self.assertIn('<int name="status">0</int>', self.solr_admin.reload("wheatley"))

    def test_rename(self):
        self.solr_admin.create("wheatley")
        self.assertIn(
            '<int name="status">0</int>', self.solr_admin.rename("wheatley", "rick")
        )

    def test_swap(self):
        self.solr_admin.create("wheatley")
        self.solr_admin.create("rick")
        self.assertIn(
            '<int name="status">0</int>', self.solr_admin.swap("wheatley", "rick")
        )

    def test_unload(self):
        self.solr_admin.create("wheatley")
        self.assertIn('<int name="status">0</int>', self.solr_admin.unload("wheatley"))

    def test_load(self):
        self.assertRaises(NotImplementedError, self.solr_admin.load, "wheatley")
