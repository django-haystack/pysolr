# encoding: utf-8

from __future__ import absolute_import, unicode_literals

import subprocess
import shlex
import time
from pysolr import SolrError


def set_script(script_name):
    global script
    script = script_name


def _process(args):
    params = shlex.split(" ".join((script, args)))
    subprocess.call(params)


def prepare():
    _process("prepare")


def start_solr(name=None, port=None):
    if port:
        _process("start-node %s %s" % (port, name))
    else:
        _process("start")


def stop_solr(port=None):
    if port:
        _process("stop-node %s" % port)
    else:
        _process("stop")


def wait_for_down(zk, node_name):
    while node_name in zk.liveNodes:
        time.sleep(0.5)


def wait_for_up(zk, collection, host):
    if collection:
        while host not in zk.getHosts(collection):
            time.sleep(0.5)
    else:
        while host not in zk.liveNodes:
            time.sleep(0.5)


def wait_for_leader(zk, collection):
    while True:
        try:
            zk.getLeaderURL(collection)
            return  # when we get here (i.e. no SolrError), we have a leader available
        except SolrError as e:
            pass
