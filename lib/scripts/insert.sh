#!/bin/sh
set -x
BASEFILE="$1"
MARKER="$2"
INSFILE="$3"
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
sed -e "s%^\(.*$MARKER.*\)%INSERTHERE\n\1%" $BASEFILE.orig | sed -e "/INSERTHERE/r $INSFILE" | sed -e "/INSERTHERE/d" > /tmp/$BASEFILE.new
$SUDOGALAXY cp -f /tmp/$BASEFILE.new $BASEFILE
rm -f /tmp/$BASEFILE.new
