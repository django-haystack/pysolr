from distutils.core import setup

setup(
    name = "pysolr",
    version = "2.0.0",
    description = "Lightweight python wrapper for Apache Solr.",
    author = 'Joseph Kocherhans',
    author_email = 'jkocherhans@gmail.com',
    py_modules = ['pysolr'],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search'
    ]
)