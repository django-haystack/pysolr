======
pysolr
======

``pysolr`` is a lightweight Python wrapper for `Apache Solr`_. It provides an
interface that queries the server and returns results based on the query.


Features
========

* Basic operations such as selecting, updating & deleting.
* Index optimization.
* `"More Like This" <http://wiki.apache.org/solr/MoreLikeThis>`_ support (if set up in Solr).
* `Spelling correction <http://wiki.apache.org/solr/SpellCheckComponent>`_ (if set up in Solr).
* Timeout support.


Requirements
============

* Python 2.4+ (tested under Python 2.6+)
* **Optional** - ``lxml`` (Python 2.4.X and below)
* **Optional** - ``simplejson`` (Python 2.5.X and below)
* **Optional** - ``httplib2`` for timeout support
* **Optional** - ``BeautifulSoup`` for Tomcat error support
* **Optional** - ``poster`` for Solr rich content extraction


Installation
============

``sudo python setup.py install`` or drop the ``pysolr.py`` file anywhere on your
PYTHONPATH.


LICENSE
=======

``pysolr`` is licensed under the New BSD license.


.. _`Apache Solr`: http://lucene.apache.org/solr/
