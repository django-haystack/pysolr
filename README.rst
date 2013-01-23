======
pysolr
======

``pysolr`` is a lightweight Python wrapper for Apache Solr. It provides an
interface that queries the server and returns results based on the query.


Features
========

* Basic operations such as selecting, updating & deleting.
* Index optimization.
* "More Like This" support (if setup in Solr).
* Spelling correction (if setup in Solr).
* Timeout support.


Requirements
============

* Python 2.6-3.3
* Requests 1.1.0+
* **Optional** - ``lxml``
* **Optional** - ``simplejson``
* **Optional** - ``cssselect`` for Tomcat error support


Installation
============

``sudo python setup.py install`` or drop the ``pysolr.py`` file anywhere on your
PYTHONPATH.


Usage
=====

Basic usage looks like::

    # If on Python 2.X
    from __future__ import print_function
    import pysolr

    # Setup a Solr instance. The timeout is optional.
    solr = pysolr.Solr('http://localhost:8983/solr/', timeout=10)

    # How you'd index data.
    solr.add([
        {
            "id": "doc_1",
            "title": "A test document",
        },
        {
            "id": "doc_2",
            "title": "The Banana: Tasty or Dangerous?",
        },
    ])

    # You can optimize the index when it gets fragmented, for better speed.
    solr.optimize()

    # Later, searching is easy. In the simple case, just a plain Lucene-style
    # query is fine.
    results = solr.search('bananas')

    # The ``Results`` object stores total results found, by default the top
    # ten most relevant results and any additional data like
    # facets/highlighting/spelling/etc.
    print("Saw {0} result(s).".format(len(results)))

    # Just loop over it to access the results.
    for result in results:
        print("The title is '{0}'.".format(result['title'])

    # For a more advanced query, say involving highlighting, you can pass
    # additional options to Solr.
    results = solr.search('bananas', **{
        'hl': 'true',
        'hl.fragsize': 10,
    })

    # You can also perform More Like This searches, if your Solr is configured
    # correctly.
    similar = solr.more_like_this(q='id:doc_2', mltfl='text')

    # Finally, you can delete either individual documents...
    solr.delete(id='doc_1')

    # ...or all documents.
    solr.delete(q='*:*')


LICENSE
=======

``pysolr`` is licensed under the New BSD license.


Running Tests
=============

Setup looks like::

    curl -O http://apache.osuosl.org/lucene/solr/4.1.0/solr-4.1.0.tgz
    tar xvzf solr-4.1.0.tgz
    cp -r solr-4.1.0/example solr4
    # Used by the content extraction and clustering handlers:
    mv solr-4.1.0/dist solr4/
    mv solr-4.1.0/contrib solr4/
    rm -rf solr-4.1.0*
    cd solr4
    rm -rf example-DIH exampledocs
    mv solr solrsinglecoreanduseless
    mv multicore solr
    cp -r solrsinglecoreanduseless/collection1/conf/* solr/core0/conf/
    cp -r solrsinglecoreanduseless/collection1/conf/* solr/core1/conf/
    # Fix paths for the content extraction handler:
    perl -p -i -e 's|<lib dir="../../../contrib/|<lib dir="../../contrib/|'g solr/*/conf/solrconfig.xml
    perl -p -i -e 's|<lib dir="../../../dist/|<lib dir="../../dist/|'g solr/*/conf/solrconfig.xml
    # Now run Solr.
    java -jar start.jar

Running the tests::

    python -m unittest2 tests
    python3 -m unittest tests
