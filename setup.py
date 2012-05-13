from distutils.core import setup

setup(
    name = "pysolr",
    version = "2.1.0-beta",
    description = "Lightweight python wrapper for Apache Solr.",
    author = 'Daniel Lindsley',
    author_email = 'daniel@toastdriven.com',
    long_description=open('README.rst', 'r').read(),
    py_modules = ['pysolr'],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search'
    ],
    url = 'http://github.com/toastdriven/pysolr/',
    extra_requires={
        'tomcat': ['BeautifulSoup'],
    }
)
