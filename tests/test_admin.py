# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import unittest

from pysolr import SolrCoreAdmin
from distutils.dir_util import copy_tree
import os
import shutil
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

def create_core(solr_admin, name):
    # to create new core:
    # step 1: mkdir new_core_path
    # step 2: copy schema.xml to new_core_path/conf/
    # step 3: call create API
    tree = ET.ElementTree(ET.fromstring(solr_admin.status())) # get xml tree
    root = tree.getroot()
    core_zero_name = 'core0'
    core_zero_path = root.find('lst[@name="status"]/lst[@name="'+core_zero_name+'"]/str[@name="instanceDir"]').text
    core_zero_conf = os.path.join(core_zero_path, 'conf')
    new_core_path = os.path.join( os.path.abspath(os.path.join(core_zero_path, os.pardir)), name)
    new_core_conf = os.path.join(new_core_path, 'conf')
    os.makedirs(new_core_path) # mkdir
    copy_tree(core_zero_conf, new_core_conf) # copy solrconfig.xml and schema.xml to new_core_path/conf/
    return solr_admin.create(name) # call create API

class SolrCoreAdminTestCase(unittest.TestCase):
    def setUp(self):
        super(SolrCoreAdminTestCase, self).setUp()
        self.solr_admin = SolrCoreAdmin('http://localhost:8983/solr/admin/cores')

    def test_status(self):
        self.assertTrue('name="defaultCoreName"' in self.solr_admin.status())
        self.assertTrue('<int name="status">' in self.solr_admin.status(core='core0'))

    def test_create(self):
        self.assertTrue('<int name="status">0</int>' in create_core(self.solr_admin, 'wheatley'))

    def test_reload(self):
        self.assertTrue('<int name="status">0</int>' in self.solr_admin.reload('wheatley'))

    def test_rename(self):
        self.assertTrue('<int name="status">0</int>' in self.solr_admin.rename('wheatley', 'rick'))

    def test_swap(self):
        self.solr_admin.rename('rick', 'wheatley')
        create_core(self.solr_admin, 'rick')
        self.assertTrue('<int name="status">0</int>' in self.solr_admin.swap('wheatley', 'rick'))

    def test_unload(self):
        self.assertTrue('<int name="status">0</int>' in self.solr_admin.unload('wheatley'))

    def test_load(self):
        self.assertRaises(NotImplementedError, self.solr_admin.load, 'wheatley')
