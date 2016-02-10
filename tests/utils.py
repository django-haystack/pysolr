# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import subprocess


def _process(action):
    subprocess.call(('./start-solr-test-server.sh', action))


def prepare():
    _process("prepare")


def start_simple_solr():
    _process("start-simple")


def start_solr_cloud():
    _process("start-cloud")


def stop_solr():
    _process("stop")
