#!/usr/bin/env python

from __future__ import absolute_import, print_function, unicode_literals

import sys
import unittest

from tests import utils as test_utils


def main():
    test_utils.prepare()

    try:
        unittest.main(module='tests')
    finally:
        test_utils.stop_solr()

if __name__ == "__main__":
    main()
