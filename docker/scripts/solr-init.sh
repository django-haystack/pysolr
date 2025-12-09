#!/bin/bash
set -e

echo "Solr init starting ..."

echo "Preparing sitecore_configset..."
cp -r "$TECHPRODUCTS_CONFIGSET" "$SITECORE_CONFIGSET"
cp -r "$PYSOLR_CONFIGSET"/. "$SITECORE_CONFIGSET/conf"

echo "Uploading sitecore_configset to Zookeeper..."
solr zk upconfig -n sitecore_configset -d "$SITECORE_CONFIGSET"
echo "Configset uploaded successfully."

echo "Creating collection '$SOLR_COLLECTION_NAME'..."
curl -fsS \
    "http://solr-node0:8983/solr/admin/collections?action=CREATE&name=$SOLR_COLLECTION_NAME&numShards=1&replicationFactor=2&collection.configName=sitecore_configset&createNodeSet=solr-node0:8983_solr,solr-node1:8983_solr"

echo "Collection '$SOLR_COLLECTION_NAME' created successfully."
echo "Solr init completed."
