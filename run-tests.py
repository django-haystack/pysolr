#!/usr/bin/env python

import subprocess
import unittest


def main():
    try:
        print("→ Starting Solr containers...")
        subprocess.run(["./solr-docker-test-env.sh", "setup"], check=True)

        print("→ Running unit test suite...")
        unittest.main(module="tests", verbosity=1)

    finally:
        print("→ Unit test suite completed.")
        subprocess.run(["./solr-docker-test-env.sh", "destroy"], check=True)


if __name__ == "__main__":
    main()
