#!/bin/sh

if [ -f /mnt/cm/bounce.txt ]; then
  exit 0;
fi

set -x
exec >/tmp/prestart.log 2>&1

#
# admin server tweaks for cloudman instance
#
# No need for sudo, we are root at this point
#

# Configure SWAP file for the instance...
# if [ ! -f /mnt/10GB.swap ]; then
#   # dd if=/dev/zero of=/mnt/10GB.swap count=1024 bs=10485760
#   fallocate -l 10G /mnt/10GB.swap
#   chmod 600 /mnt/10GB.swap
#   mkswap /mnt/10GB.swap
#   cat >>/etc/fstab <<EOF
# /mnt/10GB.swap  none  swap  sw 0  0
# EOF
# fi
# swapon -a

#
# sshd configuration
#

# Turn off password-based login - key only
sed -i 's/^PasswordAuthentication .*/PasswordAuthentication no/' /etc/ssh/sshd_config

# Remove arcfour ciphers from configuration
if [ `fgrep -w 'ciphers' /etc/ssh/sshd_config | wc -l` -eq 0 ]; then
  /usr/sbin/sshd -T | grep '^ciphers ' >> /etc/ssh/sshd_config
fi
for cipher in arcfour arcfour128 arcfour256 aes192 aes128-gcm aes128-ctr; do
  sed -i "s/^\(ciphers.*\),$cipher,\(.*\)\$/\1,\2/" /etc/ssh/sshd_config
done

# Reload service...
/usr/sbin/service ssh reload

#
# nginx reconfiguration
#

# ssl_prefer_server_ciphers On;
# ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
# ssl_ciphers ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:RSA+AESGCM:RSA+AES:!aNULL:!MD5:!DSS;

# Have to change it here because cloudman over-writes the /etc/nginx version...
# NGINXCONFIG=/mnt/cm/cm/conftemplates/nginx_server_ssl.default
NGINXCONFIG=/mnt/cm/cm/conftemplates/nginx_server_ssl

if [ `fgrep -w 'ssl_ciphers' "$NGINXCONFIG" | wc -l` -eq 0 ]; then
  sed -i '/^ *ssl_certificate_key /a ssl_ciphers ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:RSA+AESGCM:RSA+AES:!aNULL:!MD5:!DSS;' "$NGINXCONFIG"
  sed -i '/^ *ssl_certificate_key /a ssl_protocols TLSv1 TLSv1.1 TLSv1.2;' "$NGINXCONFIG"
  sed -i '/^ *ssl_certificate_key /a ssl_prefer_server_ciphers On;' "$NGINXCONFIG"
fi 

# create self-signed certificate here so that we can increase the key-bits...
if [ ! -f "/root/.ssh/instance_selfsigned_key.pem" ]; then
  yes "" | openssl req -x509 -nodes -days 3650 -newkey rsa:4096 -keyout /root/.ssh/instance_selfsigned_key.pem -out /root/.ssh/instance_selfsigned_cert.pem
  chmod 440 /root/.ssh/instance_selfsigned_key.pem
fi

# No need to reload service...
# /usr/sbin/service nginx reload

# pkill -f apt.systemd.daily
# pkill -f unattended-upgrade
# pkill -f apt.systemd.daily
# pkill -f unattended-upgrade
# pkill -f apt.systemd.daily
# pkill -f unattended-upgrade

# apt-get -y update
# apt-get -y install awscli

#
# Determine the URL for all downloaded resources...
#
URL=`grep "^post_start_script_url: " /mnt/cm/userData.yaml | tr -d "\'" | awk '{print $NF}'`
DOWNLOADURL=`echo "$URL" | sed 's/\/[^/]*$//'`
VERSION=`echo "$DOWNLOADURL" | sed 's/^.*\///'`
BASEURL=`echo "$DOWNLOADURL" | sed 's/\/[^/]*$//'`
cat <<EOF >/home/galaxy/.urls
export DOWNLOADURL="$DOWNLOADURL"
export BASEURL="$BASEURL"
export VERSION="$VERSION"
EOF
chmod a+r /home/galaxy/.urls

# Fix the security group...
( cd /mnt/cm; wget --no-check-certificate -q -O - "$DOWNLOADURL/sg.py" | python )

#
#
#

# Copy AWS credentials from /mnt/cm/??? to awscli config file
#
#
ec2metadata > /home/galaxy/.awsmd
chmod a+r /home/galaxy/.awsmd
# RG=`ec2metadata | grep "^region_name:" | awk '{print $2}'`
RG=`grep "^region_name: " /mnt/cm/userData.yaml | tr -d "\'" | awk '{print $NF}'`
AK=`grep "^access_key: " /mnt/cm/userData.yaml | tr -d "\'" | awk '{print $NF}'`
SK=`grep "^secret_key: " /mnt/cm/userData.yaml | tr -d "\'" | awk '{print $NF}'`
mkdir -p /home/galaxy/.aws
cat >/home/galaxy/.aws/config <<EOF
[default]
region = $RG
aws_access_key_id = $AK
aws_secret_access_key = $SK
EOF
chown -R galaxy.users /home/galaxy/.aws*
chmod -R a+rX /home/galaxy/.aws

# If we are the worker, then make sure we have already installed the necessary dependencies
ROLE=`grep "^role: " /mnt/cm/userData.yaml | tr -d "\'" | awk '{print $NF}'`
if [ "$ROLE" = "worker" ]; then
  
  # Install AWS CLI and NetCDF                                                                                   
  # apt-get -y update
  # apt-get -y install awscli libnetcdf-dev texlive texlive-latex-extra

  # mkdir -p /usr/local/lib/R/site-library
  # wget -q -O - "$DOWNLOADURL/usr.local.lib.R.site-library.tgz" | tar xvzf - -C /usr/local/lib/R/site-library 

  # Install the R libraries we need
  # R --vanilla <<EOF
  # source("http://bioconductor.org/biocLite.R")
  # biocLite("MSnbase")                                                      
  # EOF

  # wget -q -O - "$DOWNLOADURL/usr.local.bin.pandoc.tgz" | tar xvzf - -C /usr/local/bin 
  true

fi
