#!/usr/bin/env python

import subprocess
import unittest


def main():
    try:
        print("→ Starting unit test cases...")

        subprocess.run(["./solr-docker-test-env.sh", "setup"], check=True)
        unittest.main(module="tests", verbosity=1)

    finally:
        print("→ Unit test cases completed.")
        subprocess.run(["./solr-docker-test-env.sh", "destroy"], check=True)


if __name__ == "__main__":
    main()
