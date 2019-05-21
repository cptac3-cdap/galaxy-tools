#!/bin/env python27

import sys, os, os.path
import subprocess, hashlib, shutil, urllib

base = os.path.split(os.path.split(os.path.abspath(sys.argv[0]))[0])[0]
cptacdccbase = os.path.join(base,'lib','cptacdcc')

input,output,md5hash,sha1hash,sizehash,protocol = sys.argv[1:7]
md5hash = md5hash.strip()
sha1hash = sha1hash.strip()
sizehash = sizehash.strip()

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

def getfile1(path,filename):
    if os.path.exists(filename):
	os.unlink(filename)
    urllib.urlretrieve("https://cptc-xfer.uis.georgetown.edu/publicData/"+path+"/"+filename,filename)
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

dccpath,filename = os.path.split(input)
if protocol != 'http':
    getfile(dccpath,filename)
else:
    getfile1(dccpath,filename)
md5,sha1,size = gethash(filename)
assert(md5hash == "" or md5hash == md5)
assert(sha1hash == "" or sha1hash == sha1)
assert(sizehash == "" or sizehash == size)
shutil.move(filename,output)
