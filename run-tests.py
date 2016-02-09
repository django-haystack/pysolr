#!/usr/bin/env python

from __future__ import absolute_import, print_function, unicode_literals

import subprocess
import sys
from tests import *


def main():

    utils.prepare()

    try:
        if sys.version_info >= (3, 3) or sys.version_info >= (2, 7):
            import unittest
            unittest.main()
        else:
            cmd = ['unit2', 'discover', '-s', 'tests', '-p', '[a-z]*.py']
            subprocess.check_call(cmd)
    finally:
        utils.stop_solr()

if __name__ == "__main__":
    main()
