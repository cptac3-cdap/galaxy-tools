#!/bin/sh
set -x 
exec >/tmp/install.log 2>&1
cd /mnt/galaxy
if [ \! -d galaxy-app/config -o \! -d tools ]; then 
  echo "Please make sure you are in the Galaxy root directory" 1>&2 
  exit 1;
fi
. /home/galaxy/.urls
export GALAXY_ROOT=`pwd`
export GALAXY_APPROOT=${GALAXY_ROOT}/galaxy-app
export GALAXY_CONFIG=${GALAXY_ROOT}/galaxy-app/config
export GALAXY_TOOLS=${GALAXY_ROOT}/tools
export GALAXY_TOOLDATA=${GALAXY_ROOT}/galaxy-app/tool-data
export SUDO=sudo
export SUDOGALAXY="sudo -u galaxy -g galaxy"
export USER1=ubuntu.ubuntu
export USER2=galaxy.users
export USER3=galaxy.galaxy

