#!/bin/sh

if [ $# -lt 6 ]; then
  echo "Usage: phosphors.sh <basename> <mgffile> <psmfile> [CID|HCD] <tolerance> <topn> <relintpercent> <outpsmfile>" 1>&2
  exit 1;
fi

BASE=`readlink -f "$0"`
BASE=`dirname "$BASE"`

CONVERTR="$BASE/convert.r"
APPENDR="$BASE/append.r"
PHOSPHORSJAR="$BASE/phosphoRS.jar"
MASSTABLE="$BASE/phosphors.masstable.txt"

# For Edwards lab installation of R and java
export PATH="/tools/bin:$PATH"

RSCRIPT=${RSCRIPT:-Rscript} 
JAVAPROG=${JAVAPROG:-java}

BASENAME="$1"
MGFFILE="$2"
PSMFILE="$3"
FRAGMODE="$4"
TOLERANCE="$5"
TOPN="$6"
RELINT="$7"
OUTPUT="$8"

MGFFILE1="$BASENAME.mgf"
rm -f "$BASENAME".{mgf,xml,phospho.xml,phospho.complete.txt}
ln -s "$MGFFILE" "$MGFFILE1"

date
"$RSCRIPT" "$CONVERTR" "$MGFFILE1" "$PSMFILE" "$MASSTABLE" "$FRAGMODE" "$TOLERANCE" "$TOPN" "$RELINT" || exit 1
date
"$JAVAPROG" -Xmx2048m -jar "$PHOSPHORSJAR" "$BASENAME.xml" "$BASENAME.phospho.xml" || exit 1
date
"$RSCRIPT" "$APPENDR" "$MGFFILE1" "$PSMFILE" || exit 1
date

mv -f "$BASENAME.phospho.complete.txt" "$OUTPUT"
