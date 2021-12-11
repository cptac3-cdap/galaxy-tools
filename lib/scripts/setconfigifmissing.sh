#!/bin/sh
FILE="$1"
FIELD="$2"
VALUE="$3"
if [ ! -f "$FILE.orig" ]; then
  cp -f "$FILE" "$FILE.orig"
fi
VALUE1=`echo "$VALUE" | sed "s/\//\\\\\\\\\//g"`
if grep -q -s "^#*$FIELD *=" "$FILE"; then
  if grep -q -s "^##*$FIELD *=" "$FILE"; then
    sed -i "s/^#*$FIELD *=.*\$/$FIELD = $VALUE1/" "$FILE"
  fi
else
  sed -i '/^admin_users/r /dev/stdin' $FILE <<EOF
$FIELD = $VALUE
EOF
fi
