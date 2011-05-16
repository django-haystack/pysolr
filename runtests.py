import unittest
import doctest
import sys
from os.path import dirname, abspath

def load_tests():
    import pysolr

    suite = doctest.DocTestSuite(pysolr)
    return suite

def runtests():
    parent = dirname(abspath(__file__))
    sys.path.insert(0, parent)
    suite = load_tests()
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(bool(result.failures))

if __name__ == '__main__':
    runtests()
