#!/bin/sh
CPTAC_GALAXY=`cat /home/ubuntu/cptac-galaxy/VERSION`
CPTAC_TOOLS=`cat /mnt/galaxy/tools/extratools/VERSION | sed 's/^.*-//'`
CPTAC_DCC=`sh /mnt/galaxy/tools/extratools/lib/cptac3-cdap/cptac-dcc/cptacdcc/cksum.sh --version | awk '{print $3}'`

getversion() {
  KEY="$1"
  ID="$2"
  FILE="$3"
  zfgrep "<$KEY " "$FILE" | fgrep "id=\"$ID\"" | sed -e 's/^.*version="//' -e 's/">$//'
}

getmzmlversion() {
  getversion software $1 $2
}

MZMLGZ="$1"
PWIZ1=`getmzmlversion pwiz $MZMLGZ`
THERMO=`getmzmlversion Xcalibur $MZMLGZ`

echo "CPTAC-Galaxy:" $CPTAC_GALAXY
echo "CPTAC-Tools:" $CPTAC_TOOLS
echo "CPTAC-DCC:" $CPTAC_DCC
echo "msconvert ProteoWizard:" $PWIZ1
