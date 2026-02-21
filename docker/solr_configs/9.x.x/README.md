# Solr 9 Config Notes

**Directory:** `docker/solr_configs/9.x.x`

This directory contains Solr configuration files customized specifically for
**pysolr test requirements**.

These files are based on Solr 9 defaults, with a small number of intentional
changes. If this configuration needs to be updated for a future Solr version
(e.g. Solr 10), please make sure the customizations documented below are
preserved.

---

## schema.xml

We do **not** maintain a separate `schema.xml` file here.

Originally, `schema.xml` was just a renamed copy of Solr’s default
`managed-schema.xml`.

Instead of duplicating it, the Docker/compose scripts now **rename**
`<CORE>/conf/managed-schema.xml` to `<CORE>/conf/schema.xml` before Solr starts.

This avoids maintaining two equivalent schema files and keeps the source of
truth aligned with upstream Solr defaults.

---

## solrconfig.xml

There are **two intentional changes** compared to the default Solr configuration:

### 1. ClassicIndexSchemaFactory

```xml
<schemaFactory class="ClassicIndexSchemaFactory" />
```

This tells Solr to use `schema.xml` instead of `managed-schema.xml`.
Using `schema.xml` is preferred because it is **immutable at runtime**.

**Source location:**
[ClassicIndexSchemaFactory configuration](https://github.com/django-haystack/pysolr/blob/fa3457b4b3de44c053128052c9dc61282a2f9021/docker/solr_configs/9.x.x/solrconfig.xml#L37)

**Solr documentation:**
[Solr 9 Schema Factories – ClassicIndexSchemaFactory](https://solr.apache.org/guide/solr/9_9/configuration-guide/schema-factory.html#schema-factories)

---

### 2. MoreLikeThis request handler

```xml
<requestHandler name="/mlt" class="solr.MoreLikeThisHandler" />
```

This request handler is **not enabled by default** in Solr, but several pysolr
test cases depend on it.

**Source location:**
[MoreLikeThis request handler configuration](https://github.com/django-haystack/pysolr/blob/fa3457b4b3de44c053128052c9dc61282a2f9021/docker/solr_configs/9.x.x/solrconfig.xml#L615)

**Solr documentation:**
[Solr 9 MoreLikeThis query handler](https://solr.apache.org/guide/solr/9_9/query-guide/morelikethis.html)

---

## Notes for Future Solr Versions

When upgrading to a new Solr major version (e.g. Solr 10):

- Create a new versioned directory, e.g. `docker/solr_configs/10.x.x`
- Start from the **upstream default `solrconfig.xml`** for that Solr version
- Re-apply the two changes documented above
- Keep schema handling via `schema.xml` + `ClassicIndexSchemaFactory`
- Ensure the `/mlt` request handler remains enabled

This README exists to avoid losing these details during future upgrades.
