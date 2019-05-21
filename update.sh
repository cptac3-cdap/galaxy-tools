#!/bin/sh                                                                                                    
set -x                                                                                                       
. /home/galaxy/.urls                                                                                         
wget --no-check-certificate -q -O - $DOWNLOADURL/extratools.tgz | sudo tar zxf -
