# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import subprocess

SCRIPT="./start-solr-test-server.sh"

def _process(action):
    subprocess.call((SCRIPT, action))


def prepare():
    _process("prepare")


def start_solr():
    _process("start")


def stop_solr():
    _process("stop")


def start_chaos_monkey():
    subprocess.Popen((SCRIPT, 'pause-nodes'))