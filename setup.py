try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(
    name="pysolr",
    use_scm_version=True,
    description="Lightweight Python client for Apache Solr",
    author="Daniel Lindsley",
    author_email="daniel@toastdriven.com",
    long_description=open("README.rst", "r").read(),
    py_modules=["pysolr"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP :: Indexing/Search",
        "Programming Language :: Python :: 3",
    ],
    url="https://github.com/django-haystack/pysolr/",
    license="BSD",
    install_requires=["requests>=2.32.5", "setuptools"],
    python_requires=">=3.10",
    extras_require={"solrcloud": ["kazoo>=2.5.0"]},
    setup_requires=["setuptools_scm"],
)
