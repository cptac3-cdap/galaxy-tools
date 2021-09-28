#!/bin/sh

#
# Download dependancies from their respective sites...
# Only necessary the first time this is checked out...
# 

# cptac3-cdap downloads are all based here
BASEURL=http://cptac-cdap.georgetown.edu.s3-website-us-east-1.amazonaws.com

set -x

# cptac-mzid
mkdir -p cptac3-cdap
mkdir -p cptac3-cdap/cptac-mzid
wget -O - -q "$BASEURL/cptacmzid.linux-x86_64.tgz" | tar xzf - -C cptac3-cdap/cptac-mzid

# cptac-dcc
mkdir -p cptac3-cdap/cptac-dcc
wget -O - -q "$BASEURL/cptacdcc.linux-x86_64.tgz" | tar xzf - -C cptac3-cdap/cptac-dcc

# peptidescan
mkdir -p python
wget -O - -q "$BASEURL/peptidescan.src.tgz" | tar xzf - -C python

# pandoc
wget -O - -q "$BASEURL/pandoc.tgz" | tar xzf -

