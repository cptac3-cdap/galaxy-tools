#!/bin/sh

#
# Download dependancies from their respective sites...
# Only necessary the first time this is checked out...
# 

# cptac3-cdap downloads are all based here
BASEURL=http://cptac-cdap.georgetown.edu.s3-website-us-east-1.amazonaws.com

if [ -d ../cptac-galaxy ]; then
  echo "Please check out cptac3-cdap/cptac-galaxy in the parent directory"
  exit 1;
fi

if [ -d ../qc-reports ]; then
  echo "Please check out cptac3-cdap/qc-reports in the parent directory"
  exit 1;
fi

if [ -d ../winpulsar-tools ]; then
  echo "Please check out cptac3-cdap/winpulsar-tools in the parent directory"
  exit 1;
fi

set -x

# usr.local.bin.pandoc
wget -O usr.local.bin.pandoc.tgz -q "$BASEURL/usr.local.bin.pandoc.tgz"

# usr.local.lib.R.site-library
wget -O usr.local.lib.R.site-library.tgz -q "$BASEURL/usr.local.lib.R.site-library.tgz"

# links to files in other cptac3-cdap repositories
( cd cptacdcc; ln -s ../../cptac-galaxy/PDC.py )
( cd cdapreports; ln -s ../../cptac-galaxy/dfcollection.py )
for f in ../../winplusar-tools/aws-cf/winpulsar/*.template; do 
  ( cd data_manager_pulsar_nodes; ln -s $f )
done
for f in ../../qc-reports/metrics/*.{R,sh,r,Rmd}; do
  ( cd qcmetrics; ln -s $f )
done
for f in ../../qc-reports/reports/*.{R,sh,r,Rmd}; do
  ( cd qcreport; ln -s $f )
done

echo "Also run \"cd lib; ./dldeps.sh\""
