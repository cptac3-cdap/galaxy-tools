#!/bin/sh
# set -x
echo "$1"
exit 0
SEQPATH="$1"
SEQFILE="`basename $1`"
CMD="$2"
BASE="/dev/shm"
FASTA="$BASE/$SEQFILE"
LOCKFILE="$BASE/.$SEQFILE.lock"

# Makes sure we exit if flock fails.
set -e

(
    flock -n 200

    if [ ! -f "$FASTA" ]; then
	( cp "$SEQPATH" "$FASTA" && $CMD -d "$FASTA" $3 ) || rm -f $FASTA*
    fi

) 200>$LOCKFILE

echo "$FASTA"
