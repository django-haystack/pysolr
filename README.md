# pysolr

`pysolr` is a lightweight Python client for [Apache
Solr](https://solr.apache.org/). It provides an interface that queries
the server and returns results based on the query.

[![PyPI](https://img.shields.io/pypi/v/pysolr.svg)](https://pypi.org/project/pysolr/)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14%20%7C%203.14t-3776AB?logo=python&logoColor=white)](https://www.python.org/downloads/)
[![Solr 9+](https://img.shields.io/badge/Solr-9+-d9411e?logo=apache&logoColor=white)](https://solr.apache.org/)
[![CI Status](https://github.com/django-haystack/pysolr/actions/workflows/ci.yml/badge.svg)](https://github.com/django-haystack/pysolr/actions)
[![PyPI downloads](https://img.shields.io/pypi/dm/pysolr.svg)](https://pypi.org/project/pysolr/)
[![GitHub Stars](https://img.shields.io/github/stars/django-haystack/pysolr.svg?style=social)](https://github.com/django-haystack/pysolr/stargazers)

______________________________________________________________________

## Table of Contents

- [Status](#status)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
  - [For SolrCloud mode](#for-solrcloud-mode-initialize-your-solr-like-this)
  - [Multicore Index](#multicore-index)
  - [Custom Request Handlers](#custom-request-handlers)
  - [Custom Authentication](#custom-authentication)
  - [If your Solr servers run off https](#if-your-solr-servers-run-off-https)
  - [Custom Commit Policy](#custom-commit-policy)
- [License](#license)
- [Contributing](#contributing-to-pysolr)
- [Running Tests](#running-tests)
  - [Running a test Solr instance](#running-a-test-solr-instance)
  - [Running the tests](#running-the-tests)

______________________________________________________________________

## Status

[Changelog](https://github.com/django-haystack/pysolr/blob/master/CHANGELOG.rst)

## Features

- Basic operations such as selecting, updating & deleting.
- Index optimization.
- [More Like This](https://solr.apache.org/guide/solr/latest/query-guide/morelikethis.html)
  support (if set up in Solr).
- [Spelling
  correction](http://wiki.apache.org/solr/SpellCheckComponent) (if set
  up in Solr).
- Timeout support.
- SolrCloud awareness

## Requirements

- Python 3.10+
- Requests 2.32.5+
- **Optional** - `simplejson`
- **Optional** - `kazoo` for SolrCloud mode

## Installation

pysolr is on PyPI:

```bash
pip install pysolr
```

Or if you want to install directly from the repository:

```bash
pip install .
```

## Usage

Basic usage looks like:

```python
import pysolr

# Create a client instance. The timeout and authentication options are not required.
# Solr URL format: http://host:port/solr/<core_name>
solr = pysolr.Solr("http://localhost:8983/solr/<core_name>", always_commit=True, [timeout=10], [auth=<type of authentication>])

# Note that auto_commit defaults to False for performance. You can set
# `auto_commit=True` to have commands always update the index immediately, make
# an update call with `commit=True`, or use Solr's `autoCommit` / `commitWithin`
# to have your data be committed following a particular policy.

# Do a health check.
solr.ping()

# How you'd index data.
solr.add([
    {
        "id": "doc_1",
        "title": "A test document",
    },
    {
        "id": "doc_2",
        "title": "The Banana: Tasty or Dangerous?",
        "_doc": [
            { "id": "child_doc_1", "title": "peel" },
            { "id": "child_doc_2", "title": "seed" },
        ]
    },
])

# You can index a parent/child document relationship by
# associating a list of child documents with the special key '_doc'. This
# is helpful for queries that join together conditions on children and parent
# documents.

# Later, searching is easy. In the simple case, just a plain Lucene-style
# query is fine.
results = solr.search('bananas')

# The ``Results`` object stores total results found, by default the top
# ten most relevant results and any additional data like
# facets/highlighting/spelling/etc.
print("Saw {0} result(s).".format(len(results)))

# Just loop over it to access the results.
for result in results:
    print("The title is '{0}'.".format(result['title']))

# For a more advanced query, say involving highlighting, you can pass
# additional options to Solr.
results = solr.search('bananas', **{
    'hl': 'true',
    'hl.fragsize': 10,
})

# Traverse a cursor using its iterator:
for doc in solr.search('*:*',fl='id',sort='id ASC',cursorMark='*'):
    print(doc['id'])

# You can also perform More Like This searches, if your Solr is configured
# correctly.
similar = solr.more_like_this(q='id:doc_2', mltfl='text')

# Finally, you can delete either individual documents,
solr.delete(id='doc_1')

# also in batches...
solr.delete(id=['doc_1', 'doc_2'])

# ...or all documents.
solr.delete(q='*:*')
```

### For SolrCloud mode, initialize your Solr like this:

```python
zookeeper = pysolr.ZooKeeper("zkhost1:2181,zkhost2:2181,zkhost3:2181")
solr = pysolr.SolrCloud(zookeeper, "collection1", auth=<type of authentication>)
```

### Multicore Index

Simply point the URL to the index core:

```python
# Setup a Solr instance. The timeout is optional.
solr = pysolr.Solr("http://localhost:8983/solr/<core_name>", timeout=10)
```

### Custom Request Handlers

```python
# Setup a Solr instance. The trailing slash is optional.
solr = pysolr.Solr("http://localhost:8983/solr/<core_name>", search_handler="/autocomplete", use_qt_param=False)
```

If `use_qt_param` is `True` it is essential that the name of the handler
is exactly what is configured in `solrconfig.xml`, including the leading
slash if any. If `use_qt_param` is `False` (default), the leading and
trailing slashes can be omitted.

If `search_handler` is not specified, pysolr will default to `/select`.

The handlers for MoreLikeThis, Update, Terms etc. all default to the
values set in the `solrconfig.xml` SOLR ships with: `mlt`, `update`,
`terms` etc. The specific methods of pysolr's `Solr` class (like
`more_like_this`, `suggest_terms` etc.) allow for a kwarg `handler` to
override that value. This includes the `search` method. Setting a
handler in `search` explicitly overrides the `search_handler` setting
(if any).

### Custom Authentication

```python
# Setup a Solr instance in a kerborized environment
from requests_kerberos import HTTPKerberosAuth, OPTIONAL
kerberos_auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL, sanitize_mutual_error_response=False)

solr = pysolr.Solr("http://localhost:8983/solr/<core_name>", auth=kerberos_auth)
```

```python
# Setup a CloudSolr instance in a kerborized environment
from requests_kerberos import HTTPKerberosAuth, OPTIONAL
kerberos_auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL, sanitize_mutual_error_response=False)

zookeeper = pysolr.ZooKeeper("zkhost1:2181/solr, zkhost2:2181,...,zkhostN:2181")
solr = pysolr.SolrCloud(zookeeper, "collection", auth=kerberos_auth)
```

### If your Solr servers run off https

```python
# Setup a Solr instance in an https environment
solr = pysolr.Solr("http://localhost:8983/solr/<core_name>", verify="path/to/cert.pem")
```

```python
# Setup a CloudSolr instance in a kerborized environment

zookeeper = pysolr.ZooKeeper("zkhost1:2181/solr, zkhost2:2181,...,zkhostN:2181")
solr = pysolr.SolrCloud(zookeeper, "collection", verify="path/to/cert.perm")
```

### Custom Commit Policy

```python
# Setup a Solr instance. The trailing slash is optional.
# All requests to Solr will be immediately committed because `always_commit=True`:
solr = pysolr.Solr("http://localhost:8983/solr/<core_name>", search_handler="/autocomplete", always_commit=True)
```

`always_commit` signals to the Solr object to either commit or not
commit by default for any solr request. Be sure to change this to `True`
if you are upgrading from a version where the default policy was always
commit by default.

Functions like `add` and `delete` also still provide a way to override
the default by passing the `commit` kwarg.

It is generally good practice to limit the amount of commits to Solr as
excessive commits risk opening too many searchers or excessive system
resource consumption. See the [Solr documentation for more information](https://solr.apache.org/guide/solr/latest/indexing-guide/indexing-with-update-handlers.html#updaterequesthandler-configuration)
and details about the `autoCommit` and `commitWithin` options.

## LICENSE

`pysolr` is licensed under the New BSD license.

## Contributing to pysolr

For consistency, this project uses [pre-commit](https://pre-commit.com/)
to manage Git commit hooks.

Instead of installing `pre-commit` globally, you can run it directly using
[`uv`](https://docs.astral.sh/uv/):

- Install the Git hooks:

  ```bash
  uv run pre-commit install
  ```

- Run checks manually:

  ```bash
  uv run pre-commit run
  ```

- To check all files (e.g. in CI or full validation):

  ```bash
  uv run pre-commit run --all-files
  ```

## Running Tests

This project uses `pytest` and is typically run via `uv`.

First, install [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
by following the official installation guide.

The `run-tests.py` script automatically performs the steps below and is
recommended for running the tests unless you need more control.

You can run it with:

```bash
uv run --extra=solrcloud run-tests.py
```

### Running a test Solr instance

Downloading, configuring and running Solr 9 looks like this:

```bash
./solr-docker-test-env.sh setup
```

To specify a different Solr version:

```bash
export SOLR_VERSION=10
./solr-docker-test-env.sh setup
```

To stop and remove the Solr test environment:

```bash
./solr-docker-test-env.sh destroy
```

### Running the tests

Run the standard test suite with:

```bash
uv run pytest
```

To run the SolrCloud tests in addition to the standard test suite,
enable the solrcloud extra:

```bash
uv run --extra=solrcloud pytest
```
