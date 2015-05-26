try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name="pysolr",
    version="3.3.2",
    description="Lightweight python wrapper for Apache Solr.",
    author='Daniel Lindsley',
    author_email='daniel@toastdriven.com',
    long_description=open('README.rst', 'r').read(),
    py_modules=[
        'pysolr'
    ],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Indexing/Search',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    url='http://github.com/toastdriven/pysolr/',
    license='BSD',
    install_requires=[
        'requests>=2.0'
    ]
)
