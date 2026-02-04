#!/usr/bin/env python

import subprocess


def main():
    try:
        print("→ Starting Solr containers...")
        subprocess.run(["./solr-docker-test-env.sh", "setup"], check=True)

        print("→ Running pytest...")
        subprocess.run(["pytest"], check=True)  # noqa: S607

    finally:
        print("→ Pytest completed.")
        subprocess.run(["./solr-docker-test-env.sh", "destroy"], check=True)


if __name__ == "__main__":
    main()
