#!/bin/sh
cd tools
if [ -d extratools ]; then
  $SUDO rm -rf extratools
fi
$SUDO mkdir -p extratools
if [ "$USER1" != "" ]; then
  $SUDO chown ubuntu.ubuntu extratools
fi
cd extratools
wget --no-check-certificate -O - -q "$DOWNLOADURL/extratools.tgz" | tar zxf -
if [ "$USER2" != "" ]; then
  $SUDO chown -R $USER2 .
fi
for f in *.xml */*.xml; do
  sed -i -e "s%XXXXX_GALAXY_TOOLS_XXXXX%$GALAXY_TOOLS%" -e "s%XXXXX_GALAXY_TOOLDATA_XXXXX%$GALAXY_TOOLDATA%" $f
done

LOCALIP=`wget --no-check-certificate -q -O - http://169.254.169.254/latest/meta-data/local-ipv4`
sed -i "s/XXXXX_REPLACEWITHLOCALIP_XXXXX/$LOCALIP/" job_conf.xml

if [ "$USER2" != "" ]; then
  $SUDO chown -R $USER2 .
fi
$SUDO chmod -R a+rX .

$SUDOGALAXY rsync -av galaxy_modules/ $GALAXY_APPROOT
patch $GALAXY_APPROOT/.venv/lib/python2.7/site-packages/pulsar/client/staging/up.py lib/etc/pulsar.client.staging.up.py.patch.txt
if [ ! -d $GALAXY_TOOLDATA/proteome ]; then
  $SUDOGALAXY rsync -av galaxy_tooldata/ $GALAXY_TOOLDATA
fi

for f in $GALAXY_TOOLDATA/*.loc; do
  $SUDOGALAXY sed -i -e "s%XXXXX_GALAXY_TOOLDATA_XXXXX%$GALAXY_TOOLDATA%" $f
done

$SUDOGALAXY rsync -av galaxy_config/ $GALAXY_CONFIG

sh lib/scripts/xmlinsert.sh tool_conf.xml $GALAXY_TOOLS/extratools/tool_conf.xml
sh lib/scripts/xmlinsert.sh job_conf.xml $GALAXY_TOOLS/extratools/job_conf.xml
sh lib/scripts/insert.sh datatypes_conf.xml "/registration" $GALAXY_TOOLS/extratools/datatypes_conf.xml
sh lib/scripts/insert.sh data_manager_conf.xml "/data_managers" $GALAXY_TOOLS/extratools/data_manager_conf.xml
sh lib/scripts/insert.sh tool_data_table_conf.xml "/tables" $GALAXY_TOOLS/extratools/tool_data_table_conf.xml

for t in all_proteome_species all_proteome msgfplus_index compress_seq cptacdcc_login pulsar_nodes pulsar_nodes.ip pulsar_nodes.aws amqp_url; do
  $SUDOGALAXY touch $GALAXY_TOOLDATA/$t.loc
done

$SUDOGALAXY sh lib/scripts/setconfig.sh "$GALAXY_CONFIG/galaxy.ini" data_manager_config_file "$GALAXY_CONFIG/data_manager_conf.xml"
$SUDOGALAXY sh lib/scripts/setconfig.sh "$GALAXY_CONFIG/galaxy.ini" use_interactive False
$SUDOGALAXY sh lib/scripts/setconfigifmissing.sh "$GALAXY_CONFIG/galaxy.ini" id_secret `python -c 'import time; print time.time()' | md5sum | cut -f 1 -d ' '`
$SUDOGALAXY sh lib/scripts/setconfig.sh "$GALAXY_CONFIG/galaxy.ini" require_login True
$SUDOGALAXY sh lib/scripts/setconfig.sh "$GALAXY_CONFIG/galaxy.ini" show_welcome_with_login True
$SUDOGALAXY sh lib/scripts/setconfig.sh "$GALAXY_CONFIG/galaxy.ini" allow_user_creation False
$SUDOGALAXY sh lib/scripts/setconfig.sh "$GALAXY_CONFIG/galaxy.ini" new_user_dataset_access_role_default_private True
$SUDOGALAXY sh lib/scripts/setconfig.sh "$GALAXY_CONFIG/galaxy.ini" use_tasked_jobs True
$SUDOGALAXY sh lib/scripts/setconfig.sh "$GALAXY_CONFIG/galaxy.ini" sanitize_whitelist_file "$GALAXY_CONFIG/sanitize_whitelist.txt"
# $SUDOGALAXY sh lib/scripts/setconfig.sh "$GALAXY_CONFIG/galaxy.ini" dynamic_proxy_external_proxy True
# $SUDOGALAXY sh lib/scripts/setconfig.sh "$GALAXY_CONFIG/galaxy.ini" dynamic_proxy_debug True
# $SUDOGALAXY sh lib/scripts/setconfig.sh "$GALAXY_CONFIG/galaxy.ini" dynamic_proxy_prefix galaxy/gie_proxy

AD=`sed -n "s/^admin_users *=\(.*\)$/\1/p" "$GALAXY_CONFIG/galaxy.ini" | awk '{print $1}'`
if [ -f /mnt/cm/userData.yaml ]; then
  PW=`grep "^password: " /mnt/cm/userData.yaml | tr -d "\'" | awk '{print $NF}'`
  KY=`echo "${PW}" | md5sum | cut -f 1 -d ' '`
else
  PW="$AD"
  KY=""
fi
( cd $GALAXY_APPROOT; $SUDOGALAXY $GALAXY_APPROOT/.venv/bin/python $GALAXY_TOOLS/extratools/lib/scripts/adduser.py "$AD" "$PW" $KY) 
( cd $GALAXY_APPROOT; $SUDOGALAXY ./rolling_restart.sh  ) 
