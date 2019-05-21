#!/bin/env python27

import sys, os, os.path

iniFile = sys.argv[1]
toolData = sys.argv[2]
csfile = os.path.join(toolData,'compress_seq.loc')
valuemap = dict()
for l in open(csfile):
    sl = l.split('\t')
    valuemap[sl[0]+'.fasta'] = sl[2]
assert(os.path.isdir(toolData))
for l in open(iniFile):
    if l.startswith('filename'):
        filename = l.split('=')[1].strip()
	if filename in valuemap:
	    thepath = valuemap[filename]
	    l = 'filename = %s\n'%(thepath,)
    sys.stdout.write(l)
