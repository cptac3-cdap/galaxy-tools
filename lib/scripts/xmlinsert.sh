#!/bin/sh
set -x
ABSPATH=`readlink -f $0`
BINDIR=`dirname "$ABSPATH"`
BASEFILE="$1"
INSFILE="$2"
# SUDO="sudo"
if [ ! -d ${GALAXY_CONFIG} ]; then
  exit 0;
fi
cd ${GALAXY_CONFIG}
if [ ! -f $BASEFILE ]; then
  if [ -f $BASEFILE.sample ]; then
    $SUDOGALAXY cp -f $BASEFILE.sample $BASEFILE
  else
    exit 0;
  fi
fi
if [ ! -f $BASEFILE.orig ]; then
  $SUDOGALAXY cp $BASEFILE $BASEFILE.orig
fi
python $BINDIR/xmlinsert.py $BASEFILE.orig $INSFILE /tmp/$BASEFILE.new
$SUDOGALAXY cp -f /tmp/$BASEFILE.new $BASEFILE
