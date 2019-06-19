#!/usr/bin/env python
# encoding: utf-8

from __future__ import absolute_import, print_function, unicode_literals

import faulthandler
import signal
import unittest

from tests import utils as test_utils


def main():
    faulthandler.register(signal.SIGUSR1, all_threads=True)
    print("Installed SIGUSR1 handler to print stack traces: pkill -USR1 -f run-tests")

    test_utils.prepare()
    test_utils.start_solr()

    try:
        unittest.main(module="tests", verbosity=1)
    finally:
        print("Tests complete; halting Solr servers…")
        test_utils.stop_solr()


if __name__ == "__main__":
    main()
