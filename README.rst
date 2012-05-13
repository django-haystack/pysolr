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
