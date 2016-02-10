#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, print_function, unicode_literals

import sys
import unittest

from tests import utils as test_utils


def main():
    print('Preparing Solr')
    test_utils.prepare()

    print('Running unittest.main()')
    try:
        unittest.main(module='tests')
    finally:
        print('Halting Solr servers…')
        test_utils.stop_solr()
        print('Done')

if __name__ == "__main__":
    main()
