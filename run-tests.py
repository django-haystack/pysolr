#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, print_function, unicode_literals

import unittest

from tests import utils as test_utils


def main():
    test_utils.prepare()
    test_utils.start_simple_solr()
    test_utils.start_solr_cloud()

    try:
        unittest.main(module='tests')
    finally:
        print('Tests complete; halting Solr servers…')
        test_utils.stop_solr()

if __name__ == "__main__":
    main()
