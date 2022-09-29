#!/bin/env python3

import sys, os, os.path, csv, subprocess

inputfile = sys.argv[1]
samplefile = sys.argv[2]
labeldb = sys.argv[3]
loaderargs = sys.argv[4:-1]
tooldatapath = sys.argv[-1]

tooldir = os.path.split(os.path.abspath(sys.argv[0]))[0]
cptacraw = os.path.abspath(os.path.join(tooldir,'..','cptacdcc','cptacraw.py'))
loader1 = os.path.abspath(os.path.join(tooldir,'..','lib','CPTAC-CDAP-Reports','loader1'))
mksamp = os.path.abspath(os.path.join(tooldir,'..','lib','CPTAC-CDAP-Reports','make_sample'))

credentials = dict()
h = open(os.path.join(tooldatapath,"cptacdcc_login.loc"))
for l in h:
    sl = l.strip().split('\t')
    credentials[sl[0]] = dict(username=sl[0],
			      password=sl[2],
			      transfer=(int(sl[3])==1))

from dfcollection import DatafileCollection

dfc = DatafileCollection(credentials=credentials)
dfc.read(inputfile)

if samplefile and samplefile != "None":
    args = [ mksamp, samplefile, labeldb ] 
    proc = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False)
    files = "\n".join(f['filename'] for f in dfc) + "\n"
    stdout,stderr = proc.communicate(files.encode())
    retcode = proc.wait()
    if stderr.strip():
        print(stderr, file=sys.stderr)
    assert(retcode == 0)
    wh = open('sample.csv','w')
    wh.write(stdout.decode())
    wh.close()

for f in dfc:
    args = [ "python", cptacraw, f['resource'], f['filepath'], 
	     f['filename'], f['md5hash'], f['sha1hash'], f['sizehash'], 
	     f['username'], tooldatapath ]
    retcode = subprocess.call(args, stdin=None, shell=False)
    assert(retcode == 0)
    assert(os.path.exists(f['filename']))

    args = [ loader1, "-d", "output.psm" ] + loaderargs + [ f['filename'] ]
    proc = subprocess.Popen(args, stdin=None, shell=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    buffer = proc.stdout.read(1024)
    while buffer:
        sys.stdout.write(buffer.decode())
        buffer = proc.stdout.read(1024)
    retcode = proc.wait()
    assert(retcode == 0)

    os.unlink(f['filename'])
