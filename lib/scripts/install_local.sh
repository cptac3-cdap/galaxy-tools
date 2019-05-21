#!/bin/sh
set -x 
if [ \! -d config -o \! -d tools ]; then 
  echo "Please make sure you are in the Galaxy root directory" 1>&2 
  exit 1;
fi
export VERSION="${1=-EdwardsLab}"
export BASEURL="http://edwardslab.bmcb.georgetown.edu/software/downloads/Galaxy"
export DOWNLOADURL="$BASEURL/$1"
export GALAXY_ROOT=`pwd`
export GALAXY_APPROOT=${GALAXY_ROOT}
export GALAXY_CONFIG=${GALAXY_ROOT}/config
export GALAXY_TOOLS=${GALAXY_ROOT}/tools
export GALAXY_TOOLDATA=${GALAXY_ROOT}/tool-data
