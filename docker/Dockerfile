ARG PY_SOLR_VERSION
FROM solr:${PY_SOLR_VERSION}

ARG PY_SOLR_VERSION

ENV CORES_DIR /opt/solr/server/solr

USER root
COPY ./cores $CORES_DIR

# rewrite solrconfig.xml luceneMatchVersion to match current version and re-chown
RUN perl -p -i -e "s|<luceneMatchVersion>.*</luceneMatchVersion>|<luceneMatchVersion>${SOLR_VERSION}</luceneMatchVersion>|"g ${CORES_DIR}/core0/conf/solrconfig.xml && \
    chown -R solr:solr $CORES_DIR

USER solr
