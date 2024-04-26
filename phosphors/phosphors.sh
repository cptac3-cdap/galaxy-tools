#!/bin/sh

# set -x
if [ $# -lt 6 ]; then
  echo "Usage: phosphors.sh <basename> <mzmlfile> <psmfile> [CID|HCD] <tolerance> <topn> <relintpercent> <outpsmfile>" 1>&2
  exit 1;
fi

BASE=`readlink -f "$0"`
BASE=`dirname "$BASE"`

# CONVERTR="$BASE/convert.r"
MZML="$BASE/../lib/cptac3-cdap/cptac-mzid/cptacmzid/mzml"
APPENDR="$BASE/append.r"
PHOSPHORSJAR="$BASE/phosphoRS.jar"
MASSTABLE="$BASE/phosphors.masstable.txt"

# For Edwards lab installation of R and java
export PATH="/tools/bin:$PATH"

RSCRIPT=${RSCRIPT:-Rscript} 
JAVAPROG=${JAVAPROG:-java}

BASENAME="$1"
MZMLFILE="$2"
PSMFILE="$3"
FRAGMODE="$4"
TOLERANCE="$5"
TOPN="$6"
RELINT="$7"
OUTPUT="$8"

date
"$MZML" write_phosphors "$MZMLFILE" "$PSMFILE" "$MASSTABLE" "$TOLERANCE" "$FRAGMODE" "$TOPN" "$RELINT" > "$BASENAME.xml" || exit 1
date
"$JAVAPROG" -Xmx2048m -jar "$PHOSPHORSJAR" "$BASENAME.xml" "$BASENAME.phospho.xml" || exit 1
date
"$RSCRIPT" "$APPENDR" "$BASENAME" "$PSMFILE" || exit 1
date

mv -f "$BASENAME.phospho.complete.txt" "$OUTPUT"
