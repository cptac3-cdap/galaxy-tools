#!/usr/bin/env python

import sys
import os, os.path, csv
import tempfile
import shutil
import optparse
from urllib import urlencode
import urllib2
import datetime
import tarfile
import zipfile
import gzip
import zlib
import bz2
import time
import traceback
import subprocess
from operator import itemgetter
from lockfile import FileLock
import urllib

from galaxy.util.json import from_json_string, to_json_string

import util

def main():
    parser = optparse.OptionParser()
    (options, args) = parser.parse_args()
    filename = args[0]

    params = from_json_string( open( filename ).read() )['param_dict']
    
    tooldir = params['__tool_directory__']
    tooldata = params['GALAXY_DATA_INDEX_DIR']

    mininst = int(params['min'])
    maxinst = int(params['max'])

    startdelay = datetime.timedelta(minutes=15)
    stopdelay = datetime.timedelta(minutes=5)
    now = datetime.datetime.now()

    nodes = util.read_pulsar_nodes(tooldata,readyonly=False)
    
    jobfile,joblock = util.lock_jobs(tooldata)
    try:
        jobdata = util.read_jobs(jobfile)
        toremove = util.toremove(jobdata)
        running = util.running(jobdata)
        waiting = util.waiting(jobdata)
        # util.update_jobs(jobfile,toremove=toremove)
    except:
        print traceback.print_exc()
    finally:
        joblock.release()

    newinstance = False
    delinstance = False

    ready = 0
    notatcap = 0
    idle = set()
    runstr = []
    for n in nodes.values():
        if n['state'] != 'ready':
            continue
        if running[n['ip']] < n['cpus']:
            notatcap += 1
        if running[n['ip']] == 0:
            idle.add(n['ip'])
        runstr.append((running[n['ip']],n['cpus']))
        ready += 1

    runstr = ",".join(map(lambda t: "%d/%d"%t,sorted(runstr, reverse=True)))
    laststart = (now-2*startdelay)
    laststop = (now-2*stopdelay)

    for n in nodes.values():
        if n['state'] == 'pending' and n['timestamp'] > laststart:
            laststart = n['timestamp']
        if n['state'] == 'terminated' and n['timestamp'] > laststop:
            laststop = n['timestamp']

    if notatcap == 0 and ready < maxinst and laststart < (now-startdelay):
        newinstance = True

    if len(idle) > 0 and ready > mininst and laststop < (now-stopdelay):
        delinstance = True

    print ready,runstr,len(waiting),laststart,laststop,newinstance,delinstance

    if delinstance:
        cmd = "%s %s/data_manager_pulsar_nodes.py stop aws %s &"%(sys.executable,tooldir,nodes[idle.pop()]['awsname'])
        print cmd
        # os.system(cmd)

    elif newinstance:
        cmd = "%s %s/data_manager_pulsar_nodes.py start aws &"%(sys.executable,tooldir)
        print cmd
        # os.system(cmd)

    raise RuntimeError("just to make it happen")

if __name__ == '__main__':
    main()
