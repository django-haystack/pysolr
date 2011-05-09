#!/usr/bin/env python

try:
    from setuptools import setup, find_packages
    from setuptools.command.test import test
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages
    from setuptools.command.test import test

setup(
    name = "pysolr",
    version = "2.0.14-beta",
    description = "Lightweight python wrapper for Apache Solr.",
    author = 'Daniel Lindsley',
    author_email = 'daniel@toastdriven.com',
    py_modules = ['pysolr'],
    test_suite='runtests.runtests',
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search'
    ],
    url = 'http://github.com/toastdriven/pysolr/'
)