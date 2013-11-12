#!/bin/sh

set -e

if [ ! -f solr-4.1.0.tgz ]; then
    curl -O http://archive.apache.org/dist/lucene/solr/4.1.0/solr-4.1.0.tgz
fi

echo "Extracting Solr 4.1.0 to solr4/"
rm -rf solr4
mkdir solr4
tar -C solr4 -xf solr-4.1.0.tgz --strip-components 2 solr-4.1.0/example
tar -C solr4 -xf solr-4.1.0.tgz --strip-components 1 solr-4.1.0/dist solr-4.1.0/contrib

echo "Configuring Solr"
cd solr4
rm -rf example-DIH exampledocs
mv solr solrsinglecoreanduseless
mv multicore solr
cp -r solrsinglecoreanduseless/collection1/conf/* solr/core0/conf/
cp -r solrsinglecoreanduseless/collection1/conf/* solr/core1/conf/

# Fix paths for the content extraction handler:
perl -p -i -e 's|<lib dir="../../../contrib/|<lib dir="../../contrib/|'g solr/*/conf/solrconfig.xml
perl -p -i -e 's|<lib dir="../../../dist/|<lib dir="../../dist/|'g solr/*/conf/solrconfig.xml

# Add MoreLikeThis handler
perl -p -i -e 's|<!-- A Robust Example|<!-- More like this request handler -->\n  <requestHandler name="/mlt" class="solr.MoreLikeThisHandler" />\n\n\n  <!-- A Robust Example|'g solr/*/conf/solrconfig.xml

echo 'Starting server'
# We use exec to allow process monitors like run-tests.py to correctly kill the
# actual Java process rather than this launcher script:
exec java -Djava.awt.headless=true -Dapple.awt.UIElement=true -jar start.jar
