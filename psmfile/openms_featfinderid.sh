#!/bin/sh

set -x

MZML="$1"
MZID="$2"
INST="$3"
OUT="$4"

DIR=`dirname $0`

case "$MZID" in 
  *.mzid.gz) BASE=`basename "$MZID" .mzid.gz`; gunzip -c "$MZID" > "$BASE.mzid"; MZID="$BASE.mzid";;
  *.mzid) BASE=`basename "$MZID" .mzid`;;
esac

case "$INST" in
  HIRESMS1) FEATFINDER="-extract:mz_window 10  -extract:n_isotopes 3";;
         *) echo "Bad INSTRUMENT parameter" 1>&2; exit 1;;
esac

USER="`id -u`:`id -g`"
DOCKER="docker run -u $USER -v `pwd`:/data/ --rm"

$DOCKER openswath/openswath:latest IDFileConverter -in "$MZID" -out "$BASE.idXML" -mz_file "$MZML"
if [ $? -ne 0 ]; then
  exit 1
fi
$DOCKER openswath/openswath:latest FeatureFinderIdentification -in "$MZML" -id "$BASE.idXML" -out "$BASE.featureXML" $FEATFINDER
if [ $? -ne 0 ]; then
  exit 1
fi

rm -f "$BASE.idXML"

$DIR/../lib/cptac3-cdap/cptac-mzid/cptacmzid/featxml "$BASE.featureXML" | sort -n > "$OUT"
if [ $? -ne 0 ]; then
  exit 1
fi

rm -f "$BASE.featureXML"
