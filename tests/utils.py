# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import os
import subprocess  # NOQA: B404
from functools import total_ordering

SOLR_VERSION = os.environ.get('SOLR_VERSION', '4.10.4')


def _process(action):
    subprocess.call(("./start-solr-test-server.sh", action))  # NOQA: B603


def prepare():
    _process("prepare")


def start_solr():
    _process("start")


def stop_solr():
    _process("stop")


def solr_version_to_tuple(version):
    """Given a string, integer, or tuple return a version tuple (x, y, z)"""
    if isinstance(version, str):
        version = version.split('.')
    elif isinstance(version, int):
        version = version,

    if len(version) < 2:
        version += 0,

    if len(version) < 3:
        version += 0,

    return tuple((int(v) for v in version))


@total_ordering
class SolrVersion(object):
    def __init__(self, version=SOLR_VERSION):
        self.version = solr_version_to_tuple(version)

    def __eq__(self, other):
        return self.version == solr_version_to_tuple(other)

    def __lt__(self, other):
        return self.version < solr_version_to_tuple(other)


if __name__ == "__main__":
    solr = SolrVersion('5.5')
    assert(solr < 6)
    assert(solr < '6')
    assert(solr < '6.0')
    assert(solr < '6.0.0')
    assert(solr < (6,))
    assert(solr < (6, 0))
    assert(solr < (6, 0, 0))
    assert(solr > 5)
    assert(solr > '5')
    assert(solr > '5.4')
    assert(solr > '5.4.2')
    assert(solr > (5, 4))
    assert(solr > '4.10.4')
    assert(solr > (4, 10, 4))
    assert(solr > ())
    assert(solr > (0,))
    assert(solr > (0, 0))
    assert(solr > (0, 0, 1))
