#!/bin/env python27

import sys, os, os.path
import subprocess, hashlib, shutil, urllib

base = os.path.split(os.path.split(os.path.abspath(sys.argv[0]))[0])[0]
cptacdccbase = os.path.join(base,'lib','cptacdcc')

input,output,md5hash,sha1hash,sizehash,user,tooldata = sys.argv[1:8]

def getfile(path,filename):
    if os.path.exists(filename):
        os.unlink(filename)
    args = [os.path.join(cptacdccbase,'cptacdcc.sh'),
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

h = open(os.path.join(tooldata,"cptacdcc_login.loc"))
for l in h:
    sl = l.strip().split('\t',2)
    if sl[0] == user:
	password = sl[2]
h.close()
wh = open("cptacdcc.ini",'w')
print >>wh, """
[Portal]
User = %s
Password = %s
"""%(user,password)
wh.close()

dccpath,filename = os.path.split(input)
getfile(dccpath,filename)
md5,sha1,size = gethash(filename)
assert(md5hash == "" or md5hash == md5)
assert(sha1hash == "" or sha1hash == sha1)
assert(sizehash == "" or sizehash == size)
shutil.move(filename,output)
os.unlink("cptacdcc.ini")
