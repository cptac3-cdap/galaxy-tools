#!/bin/sh
# ( cd galaxy_tooldata; rsync -a --include '*/' --include '**/seq/*.fasta' --exclude '*' --prune-empty-dirs ~/projects/CPTAC-Galaxy/GalaxyCode/galaxy/tool-data/proteome/ proteome )
VERSION=`cat VERSION`
VERSION1=`echo "$VERSION" | sed 's/\.[^.]*$//'`
VERSION2=`echo "$VERSION" | sed 's/^.*-//'`
DIR=/data/www/html/software/downloads/Galaxy/$VERSION
FORCE=0
LINK=0
while true; do
  if [ "$1" = "-F" ]; then
    FORCE=1
    shift
  elif [ "$1" = "-L" ]; then
    LINK=1
    shift
  else
    break
  fi
done
if [ -d "$DIR" -a "$FORCE" = "0" ]; then
  echo "Version $VERSION already exported, please increment version..."
  exit 1
fi
if [ -d "$DIR" ]; then
  # Avoid removing WinPulsar folder
  rm -f "$DIR"/*.{sh,py,tgz}
fi

( cd lib/cptac3-cdap/cptac-dcc/cptacdcc; ./update.sh )
( cd lib/cptac3-cdap/cptac-mzid/cptacmzid; ./update.sh )
( cd lib/CPTAC-CDAP-Reports; ./update.sh )

mkdir -p "$DIR"
tar chzf "$DIR/extratools.tgz" `find -L . -maxdepth 1 -type d | grep -v '^\.$'` *_conf.xml update.sh VERSION
cat lib/scripts/install_local.sh lib/scripts/dltools.sh lib/scripts/install_local_post.sh > "$DIR/install_local.sh"
cat lib/scripts/install_cloudman.sh lib/scripts/dltools.sh lib/scripts/install_cloudman_post.sh > "$DIR/install.sh"
cat lib/scripts/install_cloudman_worker.sh lib/scripts/install_cloudman_post.sh > "$DIR/install_worker.sh"
cp prestartcmd.sh sg.py usr.local.lib.R.site-library.tgz usr.local.bin.pandoc.tgz "$DIR"
chmod +r "$DIR"/*
chmod +x "$DIR"/*.sh
if [ "$LINK" = "1" ]; then
  (cd $DIR/..; rm -f $VERSION1; ln -s $VERSION $VERSION1)
fi
rclone copy -v $DIR cptac-s3:cptac-cdap.georgetown.edu/$VERSION
gh release delete "Galaxy-Tools-$VERSION2" -y
git push --delete origin "refs/tags/Galaxy-Tools-$VERSION2"
git tag --delete "Galaxy-Tools-$VERSION2"
gh release create "Galaxy-Tools-$VERSION2" -t "Galaxy-Tools-$VERSION2" --notes "" $DIR/*.{sh,tgz,py}

echo "Folder: $DIR"
ls -l "$DIR"
