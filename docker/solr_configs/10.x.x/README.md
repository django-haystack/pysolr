# Solr 10 Config Notes

**Directory:** `docker/solr_configs/10.x.x`

This directory contains Solr configuration files customized specifically for
**pysolr test requirements**.

These files are based on Solr 10 defaults, with a small number of intentional
changes. If this configuration needs to be updated for a future Solr version
(e.g. Solr 11), please make sure the customizations documented below are
preserved.

______________________________________________________________________

## schema.xml

We do **not** maintain a separate `schema.xml` file here.

Originally, `schema.xml` was just a renamed copy of Solr’s default
`managed-schema.xml`.

Instead of duplicating it, the Docker/compose scripts now **rename**
`<CORE>/conf/managed-schema.xml` to `<CORE>/conf/schema.xml` before Solr starts.

This avoids maintaining two equivalent schema files and keeps the source of
truth aligned with upstream Solr defaults.

______________________________________________________________________

## solrconfig.xml

There are **three intentional changes** compared to the default Solr configuration:

### 1. ClassicIndexSchemaFactory

```xml
<schemaFactory class="ClassicIndexSchemaFactory" />
```

This tells Solr to use `schema.xml` instead of `managed-schema.xml`.
Using `schema.xml` is preferred because it is **immutable at runtime**.

**Source location:**
[ClassicIndexSchemaFactory configuration](https://github.com/django-haystack/pysolr/blob/5c38c7df1af4ac6904faa6289e138812e9909f09/docker/solr_configs/10.x.x/solrconfig.xml#L39)

**Solr documentation:**
[Solr 10 Schema Factories – ClassicIndexSchemaFactory](https://solr.apache.org/guide/solr/latest/configuration-guide/schema-factory.html#schema-factories)

______________________________________________________________________

### 2. MoreLikeThis request handler

```xml
<requestHandler name="/mlt" class="solr.MoreLikeThisHandler" />
```

This request handler is **not enabled by default** in Solr, but several pysolr
test cases depend on it.

**Source location:**
[MoreLikeThis request handler configuration](https://github.com/django-haystack/pysolr/blob/5c38c7df1af4ac6904faa6289e138812e9909f09/docker/solr_configs/10.x.x/solrconfig.xml#L691)

**Solr documentation:**
[Solr 10 MoreLikeThis query handler](https://solr.apache.org/guide/solr/latest/query-guide/morelikethis.html)

______________________________________________________________________

### 3. External Apache Tika server

```xml
<str name="tikaserver.url">http://tika:9998</str>
```

Starting from Solr 10, Apache Tika is no longer embedded inside Solr.
If the `/update/extract` API is used, an **external Tika server** must be
configured.

Solr's default configuration expects the Apache Tika server to run on
`localhost`. However, in our test environment Solr runs inside a Docker
container while Tika runs as a **separate Docker Compose service**.

Because containers communicate using their **service names**, `localhost`
would point to the Solr container itself rather than the Tika container.

Therefore the configuration is changed from:

```xml
<str name="tikaserver.url">http://localhost:9998</str>
```

to:

```xml
<str name="tikaserver.url">http://tika:9998</str>
```

Here `tika` is the **Docker Compose service name** used to reach the Tika
container from the Solr container.

**Source location:**
[Apache tika configuration](https://github.com/django-haystack/pysolr/blob/5c38c7df1af4ac6904faa6289e138812e9909f09/docker/solr_configs/10.x.x/solrconfig.xml#L678)

**Solr documentation:**
[Solr 10 Apache tika server](https://solr.apache.org/guide/solr/latest/indexing-guide/indexing-with-tika.html)

______________________________________________________________________

## Notes for Future Solr Versions

When upgrading to a new Solr major version (e.g. Solr 11):

- Create a new versioned directory, e.g. `docker/solr_configs/11.x.x`
- Start from the **upstream default `solrconfig.xml`** for that Solr version
- Re-apply the changes documented above
- Keep schema handling via `schema.xml` + `ClassicIndexSchemaFactory`
- Ensure the `/mlt` request handler remains enabled
- Ensure the external Tika server is configured with the correct URL

This README exists to avoid losing these details during future upgrades.
