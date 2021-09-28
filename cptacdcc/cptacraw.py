#!/bin/env python27

import sys, os, os.path
import subprocess, hashlib, shutil, urllib, time, traceback


base = os.path.split(os.path.split(os.path.abspath(sys.argv[0]))[0])[0]
cptacdccbase = os.path.join(base,'lib','cptac3-cdap','cptac-dcc','cptacdcc')
# cptacdccbase = os.path.join(base,'lib','cptacdcc')
rclonebase = os.path.join(base,'lib','cptac3-cdap','cptac-dcc','cptacdcc','rclone')
# rclonebase = os.path.join(base,'lib','cptacdcc','rclone')

resource,input,output,md5hash,sha1hash,sizehash,user,tooldata = sys.argv[1:9]

# assert(input.lower().endswith('.raw'))

maxattempts = 5

def getdccfile(path,filename):
    if os.path.exists(filename):
        os.unlink(filename)
    args = [os.path.join(cptacdccbase,'cptacdcc.sh'),
	    '-q',
	    'get',
	    os.path.join(path,filename)
	    ]
    attempt = 0
    while attempt < maxattempts:
        attempt += 1
        retcode = subprocess.call(args,stdin=None,shell=False)
        if retcode == 0 and os.path.exists(filename):
            break
        print >>sys.stderr, "DCC Path: %s, Failed Attempt: %d"%(os.path.join(path,filename),attempt)
        time.sleep(10)
    if retcode != 0 or not os.path.exists(filename):
        print >>sys.stderr, "DCC Path: %s, Download Failed."%(os.path.join(path,filename),)
    assert(retcode == 0)
    assert(os.path.exists(filename))

def getdcctrfile(path,filename):
    if os.path.exists(filename):
        os.unlink(filename)
    args = [os.path.join(cptacdccbase,'cptactransfer.sh'),
	    '-q',
	    'get',
	    os.path.join(path,filename)
	    ]
    attempt = 0
    while attempt < maxattempts:
        attempt += 1
        retcode = subprocess.call(args,stdin=None,shell=False)
        if retcode == 0 and os.path.exists(filename):
            break
        print >>sys.stderr, "DCC XFER Path: %s, Failed Attempt: %d"%(os.path.join(path,filename),attempt)
        time.sleep(10)
    if retcode != 0 or not os.path.exists(filename):
        print >>sys.stderr, "DCC XFER Path: %s, Download Failed."%(os.path.join(path,filename),)
    assert(retcode == 0)
    assert(os.path.exists(filename))

def getportalfile(path,filename):
    if os.path.exists(filename):
        os.unlink(filename)
    args = [os.path.join(cptacdccbase,'cptacpublic.sh'),
	    '--accept',
	    '-q',
	    'get',
	    os.path.join(path,filename)
	    ]
    attempt = 0
    while attempt < maxattempts:
        attempt += 1
        retcode = subprocess.call(args,stdin=None,shell=False)
        if retcode == 0 and os.path.exists(filename):
            break
        print >>sys.stderr, "CPTAC Portal Path: %s, Failed Attempt: %d"%(os.path.join(path,filename),attempt)
        time.sleep(10)
    if retcode != 0 or not os.path.exists(filename):
        print >>sys.stderr, "CPTAC Portal Path: %s, Download Failed."%(os.path.join(path,filename),)
    assert(retcode == 0)
    assert(os.path.exists(filename))

def geturlfile(url,filename):
    if os.path.exists(filename):
	os.unlink(filename)
    attempt = 0                                                                                               
    while attempt < maxattempts:                                                                              
        attempt += 1                                                                                          
	exception = False
	try:
            urllib.urlretrieve(url,filename)
            if os.path.exists(filename):                                                         
                break
	except Exception, e:
	    traceback.print_exc()
	    exception = True
        print >>sys.stderr, "URL: %s, Failed Attempt: %d"%(url,attempt)
        time.sleep(10)
    if exception or not os.path.exists(filename):                                                          
        print >>sys.stderr, "URL: %s, Download Failed."%(url,)
    assert(os.path.exists(filename))    
    assert(not exception)

def getrclonefile(remote,path,filename):
    if os.path.exists(filename):
        os.unlink(filename)
    args = [os.path.join(rclonebase,'rclone.sh'),
	    remote,os.path.join(path,filename),
	    ]
    retcode = subprocess.call(args,stdin=None,shell=False)
    if retcode != 0 or not os.path.exists(filename):
	print >>sys.stderr, "rclone download failed: %s:%s"%(remote,os.path.join(path,filename),)
    assert(retcode == 0)
    assert(os.path.exists(filename))

def gets3file(path,filename):
    if os.path.exists(filename):
        os.unlink(filename)
    args = [os.path.join(rclonebase,'s3.sh'),
	    os.path.join(path,filename),
	    ]
    retcode = subprocess.call(args,stdin=None,shell=False)
    if retcode != 0 or not os.path.exists(filename):
	print >>sys.stderr, "S3 download failed: %s"%(os.path.join(path,filename),)
    assert(retcode == 0)
    assert(os.path.exists(filename))

def getlocalfile(path,filename):
    if os.path.exists(filename):
        os.unlink(filename)
    shutil.copy(os.path.join(path,filename),filename)
    assert(os.path.exists(filename)), "Copy local file failed: %s"%(os.path.join(path,filename),)

def getpdcfile(studyid,fileid,filename,resource):
    if os.path.exists(filename):
        os.unlink(filename)
    from PDC import PDC, PDCDEV
    if resource == "pdc":
        pdc = PDC()
    elif resource == "pdcdev":
	pdc = PDCDEV()
    else:
	raise RuntimeError("Bad PDC resource string: %s."%(resource,))
    thefile = None
    for f in pdc._filesPerStudy(study_id=studyid,file_name=filename):
	if f['file_name'] == filename:
	    thefile = f
	    break
    assert thefile , "Can't find PDC file: study_id=%s file_id=%s filename=%s"%(studyid,fileid,filename)
    signedurl = thefile['signedUrl']
    geturlfile(signedurl,filename)

def gethash(filename):
    md5hash = hashlib.md5()
    sha1hash = hashlib.sha1()
    h = open(filename,'rb')
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

if resource in ("dcc","dcctr"):
    transfer = 0
    if resource == "dcctr":
	transfer = 1
    password = None
    h = open(os.path.join(tooldata,"cptacdcc_login.loc"))
    for l in h:
        sl = l.strip().split('\t')
        if sl[0] == user and int(sl[3]) == transfer:
            password = sl[2]
	    break
    h.close()
    assert password != None, "Cannot find password for username %s in CPTAC DCC credentials"%(user,)
    if not transfer:
        inifile = "cptacdcc.ini"
    else:
        inifile = "cptactransfer.ini"
    wh = open(inifile,'w')
    print >>wh, """
[Portal]
User = %s
Password = %s
"""%(user,password.replace('%','%%'))
    wh.close()

    dccpath,filename = os.path.split(input)
    if not transfer:
        getdccfile(dccpath,filename)
    else:
        getdcctrfile(dccpath,filename)
    md5,sha1,size = gethash(filename)
    assert(md5hash == "" or md5hash == md5), "File MD5 and provided MD5 do not match: %s"%(input)
    assert(sha1hash == "" or sha1hash == sha1), "File SHA1 and provided SHA1 do not match: %s"%(input)
    assert(sizehash == "" or sizehash == size), "File size and provided size do not match: %s"%(input)
    shutil.move(filename,output)
    os.unlink(inifile)

elif resource == "portal":

    dccpath,filename = os.path.split(input)
    getportalfile(dccpath,filename)
    md5,sha1,size = gethash(filename)
    assert(md5hash == "" or md5hash == md5), "File MD5 and provided MD5 do not match: %s"%(input)
    assert(sha1hash == "" or sha1hash == sha1), "File SHA1 and provided SHA1 do not match: %s"%(input)
    assert(sizehash == "" or sizehash == size), "File size and provided size do not match: %s"%(input)
    shutil.move(filename,output)

elif resource == "portalurl":

    dccpath,filename = os.path.split(input)
    geturlfile("https://cptc-xfer.uis.georgetown.edu/publicData/"+dccpath.strip('/')+"/"+filename,filename)
    md5,sha1,size = gethash(filename)
    assert(md5hash == "" or md5hash == md5), "File MD5 and provided MD5 do not match: %s"%(input)
    assert(sha1hash == "" or sha1hash == sha1), "File SHA1 and provided SHA1 do not match: %s"%(input)
    assert(sizehash == "" or sizehash == size), "File size and provided size do not match: %s"%(input)
    shutil.move(filename,output)

elif resource == "url":

    dccpath,filename = os.path.split(input)
    geturlfile(dccpath+"/"+filename,filename)
    md5,sha1,size = gethash(filename)
    assert(md5hash == "" or md5hash == md5), "File MD5 and provided MD5 do not match: %s"%(input)
    assert(sha1hash == "" or sha1hash == sha1), "File SHA1 and provided SHA1 do not match: %s"%(input)
    assert(sizehash == "" or sizehash == size), "File size and provided size do not match: %s"%(input)
    shutil.move(filename,output)

elif resource == "s3":

    dccpath,filename = os.path.split(input)
    gets3file(dccpath,filename)
    md5,sha1,size = gethash(filename)
    assert(md5hash == "" or md5hash == md5), "File MD5 and provided MD5 do not match: %s"%(input)
    assert(sha1hash == "" or sha1hash == sha1), "File SHA1 and provided SHA1 do not match: %s"%(input)
    assert(sizehash == "" or sizehash == size), "File size and provided size do not match: %s"%(input)
    shutil.move(filename,output)

elif resource.split('/')[0] == "rclone":

    if '/' in resource:
        resource,remote = resource.split('/',1)
    elif ':' in input:
	remote,input = input.split(':',1)
    else:
	raise RuntimeError("Can't determine rclone remote")
    dccpath,filename = os.path.split(input)
    getrclonefile(remote,dccpath,filename)
    md5,sha1,size = gethash(filename)
    assert(md5hash == "" or md5hash == md5), "File MD5 and provided MD5 do not match: %s"%(input)
    assert(sha1hash == "" or sha1hash == sha1), "File SHA1 and provided SHA1 do not match: %s"%(input)
    assert(sizehash == "" or sizehash == size), "File size and provided size do not match: %s"%(input)
    shutil.move(filename,output)

elif resource == "local":

    path,filename = os.path.split(input)
    getlocalfile(path,filename)
    md5,sha1,size = gethash(filename)
    assert(md5hash == "" or md5hash == md5), "File MD5 and provided MD5 do not match: %s"%(input)
    assert(sha1hash == "" or sha1hash == sha1), "File SHA1 and provided SHA1 do not match: %s"%(input)
    assert(sizehash == "" or sizehash == size), "File size and provided size do not match: %s"%(input)
    shutil.move(filename,output)

elif resource in ("pdc","pdcdev"):

    studyid,fileid,filename = input.split("/",2)
    getpdcfile(studyid,fileid,filename,resource=resource)
    md5,sha1,size = gethash(filename)
    assert(md5hash == "" or md5hash == md5), "File MD5 and provided MD5 do not match: %s"%(input)
    assert(sha1hash == "" or sha1hash == sha1), "File SHA1 and provided SHA1 do not match: %s"%(input)
    assert(sizehash == "" or sizehash == size), "File size and provided size do not match: %s"%(input)
    shutil.move(filename,output)

else:

    raise RuntimeError("Bad resource %s"%(resource,))

