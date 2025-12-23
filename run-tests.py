#!/usr/bin/env python

import subprocess
import unittest
from pathlib import Path


def main():
    try:
        print("→ Starting Solr containers...")
        subprocess.run(["./solr-docker-test-env.sh", "setup"], check=True)

        print("→ Running unit test suite...")
        old_path = Path("tests/__init__.py")
        new_path = old_path.with_name("z__init__.py")
        old_path.rename(new_path)  # rename tests/__init__.py to avoid duplicate tests
        subprocess.run(["pytest"], check=True)  # noqa: S607
        new_path.rename(old_path)
        unittest.main(module="tests", verbosity=1)

    finally:
        print("→ Unit test suite completed.")
        subprocess.run(["./solr-docker-test-env.sh", "destroy"], check=True)


if __name__ == "__main__":
    main()
