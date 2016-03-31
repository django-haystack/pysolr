#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, print_function, unicode_literals

import unittest
import os

from tests import utils as test_utils


def main():
    if os.environ.has_key("PYSOLR_STARTER"):
        test_utils.set_script(os.environ["PYSOLR_STARTER"])
    else:
        test_utils.set_script("./start-solr-test-server.sh")

    test_utils.prepare()
    test_utils.start_solr()

    try:
        unittest.main(module='tests', verbosity=1)
    finally:
        print('Tests complete; halting Solr servers…')
        test_utils.stop_solr()

if __name__ == "__main__":
    main()
