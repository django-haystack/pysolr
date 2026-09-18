# Solr 9 Config Overlay

`configoverlay.json` is Solr's config overlay, a reserved filename it reads from a
core's `conf/` directory and layers over `solrconfig.xml` at core load. It is the
same file the Config API writes, so shipping it directly sets a core up without
needing a running server to POST to.

`compose.yaml` copies it into the `sample_techproducts_configs` configset before
Solr starts, leaving the upstream `solrconfig.xml` untouched.

Ref: [Config API](https://solr.apache.org/guide/solr/9_0/configuration-guide/config-api.html)

## `/mlt`

`solr.MoreLikeThisHandler` is not registered by default and several test cases query
it.

Ref: [MoreLikeThis](https://solr.apache.org/guide/solr/9_0/query-guide/morelikethis.html)
