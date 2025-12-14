======
pysolr
======

``pysolr`` is a lightweight Python client for `Apache Solr`_. It provides an
interface that queries the server and returns results based on the query.

.. _`Apache Solr`: https://solr.apache.org/


|PyPI version| |Python versions| |Solr versions| |CI Status| |Ruff| |uv| |PyPI downloads| |GitHub stars|

.. |PyPI version| image:: https://img.shields.io/pypi/v/pysolr.svg
   :target: https://pypi.org/project/pysolr/
   :alt: PyPI version

.. |Python versions| image:: https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14%20%7C%203.14t-3776AB?logo=python&logoColor=white
   :target: https://www.python.org/downloads/
   :alt: Python 3.10+

.. |Solr versions| image:: https://img.shields.io/badge/Solr-9+-d9411e?logo=apache&logoColor=white
   :target: https://solr.apache.org/
   :alt: Solr 9+

.. |CI Status| image:: https://github.com/django-haystack/pysolr/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/django-haystack/pysolr/actions
   :alt: CI Status

.. |Ruff| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json
   :target: https://github.com/astral-sh/ruff
   :alt: Ruff

.. |uv| image:: https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json
   :target: https://github.com/astral-sh/uv
   :alt: uv

.. |PyPI downloads| image:: https://img.shields.io/pypi/dm/pysolr.svg
   :target: https://pypi.org/project/pysolr/
   :alt: PyPI downloads

.. |GitHub stars| image:: https://img.shields.io/github/stars/django-haystack/pysolr.svg?style=social
   :target: https://github.com/django-haystack/pysolr/stargazers
   :alt: GitHub stars

----

Status
======

`Changelog <https://github.com/django-haystack/pysolr/blob/master/CHANGELOG.rst>`_

Features
========

* Basic operations such as selecting, updating & deleting.
* Index optimization.
* `"More Like This" <http://wiki.apache.org/solr/MoreLikeThis>`_ support (if set up in Solr).
* `Spelling correction <http://wiki.apache.org/solr/SpellCheckComponent>`_ (if set up in Solr).
* Timeout support.
* SolrCloud awareness

Requirements
============

* Python 3.10+
* Requests 2.32.5+
* **Optional** - ``simplejson``
* **Optional** - ``kazoo`` for SolrCloud mode

Installation
============

pysolr is on PyPI:

.. code-block:: console

   $ pip install pysolr

Or if you want to install directly from the repository:

.. code-block:: console

    $ pip install .

Usage
=====

Basic usage looks like:

.. code-block:: python

    import pysolr

    # Create a client instance. The timeout and authentication options are not required.
    # Solr URL format: http://host:port/solr/<CORE_NAME>
    solr = pysolr.Solr("http://localhost:8983/solr/my_core", always_commit=True, [timeout=10], [auth=<type of authentication>])

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

.. code-block:: python

    # For SolrCloud mode, initialize your Solr like this:

    zookeeper = pysolr.ZooKeeper("zkhost1:2181,zkhost2:2181,zkhost3:2181")
    solr = pysolr.SolrCloud(zookeeper, "collection1", auth=<type of authentication>)


Multicore Index
~~~~~~~~~~~~~~~

Simply point the URL to the index core:

.. code-block:: python

    # Setup a Solr instance. The timeout is optional.
    solr = pysolr.Solr("http://localhost:8983/solr/my_core", timeout=10)


Custom Request Handlers
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Setup a Solr instance. The trailing slash is optional.
    solr = pysolr.Solr("http://localhost:8983/solr/my_core", search_handler="/autocomplete", use_qt_param=False)


If ``use_qt_param`` is ``True`` it is essential that the name of the handler is
exactly what is configured in ``solrconfig.xml``, including the leading slash
if any. If ``use_qt_param`` is ``False`` (default), the leading and trailing
slashes can be omitted.

If ``search_handler`` is not specified, pysolr will default to ``/select``.

The handlers for MoreLikeThis, Update, Terms etc. all default to the values set
in the ``solrconfig.xml`` SOLR ships with: ``mlt``, ``update``, ``terms`` etc.
The specific methods of pysolr's ``Solr`` class (like ``more_like_this``,
``suggest_terms`` etc.) allow for a kwarg ``handler`` to override that value.
This includes the ``search`` method. Setting a handler in ``search`` explicitly
overrides the ``search_handler`` setting (if any).


Custom Authentication
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Setup a Solr instance in a kerborized environment
    from requests_kerberos import HTTPKerberosAuth, OPTIONAL
    kerberos_auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL, sanitize_mutual_error_response=False)

    solr = pysolr.Solr("http://localhost:8983/solr/my_core", auth=kerberos_auth)

.. code-block:: python

    # Setup a CloudSolr instance in a kerborized environment
    from requests_kerberos import HTTPKerberosAuth, OPTIONAL
    kerberos_auth = HTTPKerberosAuth(mutual_authentication=OPTIONAL, sanitize_mutual_error_response=False)

    zookeeper = pysolr.ZooKeeper("zkhost1:2181/solr, zkhost2:2181,...,zkhostN:2181")
    solr = pysolr.SolrCloud(zookeeper, "collection", auth=kerberos_auth)


If your Solr servers run off https
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Setup a Solr instance in an https environment
    solr = pysolr.Solr("http://localhost:8983/solr/my_core", verify="path/to/cert.pem")

.. code-block:: python

    # Setup a CloudSolr instance in a kerborized environment

    zookeeper = pysolr.ZooKeeper("zkhost1:2181/solr, zkhost2:2181,...,zkhostN:2181")
    solr = pysolr.SolrCloud(zookeeper, "collection", verify="path/to/cert.perm")


Custom Commit Policy
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Setup a Solr instance. The trailing slash is optional.
    # All requests to Solr will be immediately committed because `always_commit=True`:
    solr = pysolr.Solr("http://localhost:8983/solr/my_core", search_handler="/autocomplete", always_commit=True)

``always_commit`` signals to the Solr object to either commit or not commit by
default for any solr request. Be sure to change this to ``True`` if you are
upgrading from a version where the default policy was always commit by default.

Functions like ``add`` and ``delete`` also still provide a way to override the
default by passing the ``commit`` kwarg.

It is generally good practice to limit the amount of commits to Solr as
excessive commits risk opening too many searchers or excessive system
resource consumption. See the Solr documentation for more information and
details about the ``autoCommit`` and ``commitWithin`` options:

https://lucene.apache.org/solr/guide/7_7/updatehandlers-in-solrconfig.html#UpdateHandlersinSolrConfig-autoCommit


LICENSE
=======

``pysolr`` is licensed under the New BSD license.

Contributing to pysolr
======================

For consistency, this project uses `pre-commit <https://pre-commit.com/>`_ to manage Git commit hooks:

#. Install the `pre-commit` package: e.g. `brew install pre-commit`,
   `pip install pre-commit`, etc.
#. Run `pre-commit install` each time you check out a new copy of this Git
   repository to ensure that every subsequent commit will be processed by
   running `pre-commit run`, which you may also do as desired. To test the
   entire repository or in a CI scenario, you can check every file rather than
   just the staged ones using `pre-commit run --all`.


Running Tests
=============

The ``run-tests.py`` script will automatically perform the steps below and is
recommended for testing by default unless you need more control.

Running a test Solr instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Downloading, configuring and running Solr 9 looks like this::

    ./solr-docker-test-env.sh setup

To specify a different Solr version::

    export SOLR_VERSION=9.8.0
    ./solr-docker-test-env.sh setup

To stop and remove the Solr test environment::

    ./solr-docker-test-env.sh destroy

Running the tests
~~~~~~~~~~~~~~~~~

.. code-block:: console

    $ python -m unittest tests
