import subprocess


def _process(action):

    subprocess.call(("./start-solr-test-server.sh", action))
                                 #stdout=open("test-solr.stdout.log", "wb"),
                                 #stderr=open("test-solr.stderr.log", "wb"))


def prepare():
    _process("prepare")


def start_simple_solr():
    _process("start-simple")


def start_solr_cloud():
    _process("start-cloud")


def stop_solr():
    _process("stop")
