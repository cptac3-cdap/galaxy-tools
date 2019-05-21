#!/bin/env python27

import sys, os, os.path
import subprocess, hashlib, shutil

base = os.path.split(os.path.split(os.path.abspath(sys.argv[0]))[0])[0]
cptacdccbase = os.path.join(base,'lib','cptacdcc')

input,output,md5hash,sha1hash,sizehash = sys.argv[1:6]

cksumbase,cksumfile = os.path.split(sys.argv[1])
cksumfilebase,cksumextn = cksumfile.rsplit('.',1)
assert(cksumextn == 'cksum')

if cksumfilebase == os.path.split(cksumbase)[1]:
    downloaddir = cksumbase
else:
    downloaddir = os.path.join(cksumbase,cksumfilebase)

outfile = sys.argv[2]

def getfile(path,filename):
    if os.path.exists(filename):
        os.unlink(filename)
    args = [os.path.join(cptacdccbase,'cptacpublic.sh'),
	    '--accept',
	    '-q',
	    'get',
	    os.path.join(path,filename)
	    ]
    retcode = subprocess.call(args,stdin=None,shell=False)
    assert(retcode == 0)
    assert(os.path.exists(filename))

def gethash(filename):
    md5hash = hashlib.md5()
    sha1hash = hashlib.sha1()
    h = open(filename)
    while True:
	buffer = h.read(8192)
	if not buffer:
	    break
	md5hash.update(buffer)
	sha1hash.update(buffer)
    h.close()
    size = os.path.getsize(filename)
    md5hash = md5hash.hexdigest().lower()
    sha1hash = sha1hash.hexdigest().lower()
    return md5hash,sha1hash,str(size)

def rmminusrf(top):
    if os.path.isdir(top):
        shutil.rmtree(top)

getfile(cksumbase,cksumfile)
rmminusrf('downloads')
os.makedirs('downloads')
for l in open(cksumfile):
    md5,sha1,size,filename = l.strip().split('\t',3)
    getfile(downloaddir,filename)
    assert gethash(filename) == (md5,sha1,size)
    shutil.move(filename,os.path.join('downloads',filename))

shutil.copyfile(cksumfile,outfile)
