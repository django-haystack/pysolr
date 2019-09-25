# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import subprocess  # NOQA: B404


def _process(action):
    subprocess.call(("./start-solr-test-server.sh", action))  # NOQA: B603


def prepare():
    _process("prepare")


def start_solr():
    _process("start")


def stop_solr():
    _process("stop")
