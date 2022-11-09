#!/bin/sh
CPTAC_GALAXY=`cat /home/ubuntu/cptac-galaxy/VERSION`
CPTAC_TOOLS=`cat /mnt/galaxy/tools/extratools/VERSION | sed 's/^.*-//'`
CPTAC_REPORTS=`cat /mnt/galaxy/tools/extratools/lib/CPTAC-CDAP-Reports/VERSION.txt`
CPTAC_DCC=`sh /mnt/galaxy/tools/extratools/lib/cptac3-cdap/cptac-dcc/cptacdcc/cksum.sh --version | awk '{print $3}'`
CPTAC_MZID=`sh /mnt/galaxy/tools/extratools/lib/cptac3-cdap/cptac-mzid/cptacmzid/version.sh`

getversion() {
  KEY="$1"
  ID="$2"
  FILE="$3"
  zfgrep "<$KEY " "$FILE" | fgrep "id=\"$ID\"" | sed -e 's/^.*version="//' -e 's/">$//'
}

getmzmlversion() {
  getversion software $1 $2
}

getmzidversion() {
  getversion AnalysisSoftware $1 $2
}

MZMLGZ="$1"
PWIZ1=`getmzmlversion pwiz $MZMLGZ`
THERMO=`getmzmlversion Xcalibur $MZMLGZ`

MZIDGZ="$2"
MSGF=`getmzidversion "MS-GF+" $MZIDGZ`
CPTAC_CDAP=`getmzidversion "CPTAC-CDAP" $MZIDGZ`
CPTAC_DCC_MZID=`getmzidversion "CPTAC-DCC:mzIdentML" $MZIDGZ`
PWIZ2=`getmzidversion "ProteomeWizard" $MZIDGZ`

MSGFID="$3"
SEQDB=`fgrep '<SearchDatabase ' $MSGFID | sed -e 's/^.*location="//' -e 's/" .*$//' -e 's/^.*\///'`

echo "CPTAC-Galaxy:" $CPTAC_GALAXY
echo "CPTAC-Tools:" $CPTAC_TOOLS
echo "CPTAC-DCC:" $CPTAC_DCC
echo "CPTAC-MZID:" $CPTAC_MZID
echo "CPTAC-DCC mzIdentML:" $CPTAC_DCC_MZID
echo "CPTAC CDAP:" $CPTAC_CDAP
echo "msconvert ProteoWizard:" $PWIZ1
echo "text2psm ProteoWizard:" $PWIZ2
echo "MS-GF+:" $MSGF
echo "Search Database:" $SEQDB