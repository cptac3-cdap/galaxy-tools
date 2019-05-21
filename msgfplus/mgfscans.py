#!/bin/env python

import sys, re, random
from optparse import OptionParser

parser = OptionParser()
parser.add_option("--random",action="store_true",dest="random",default=False)
parser.add_option("--mw",action="store_true",dest="mw",default=False)
parser.add_option("--size",type="int",dest="size",default=None)
parser.add_option("--max",type="int",dest="max",default=None)

opts,args = parser.parse_args()

if not opts.size:
    opts.size = int(1e+20)
if not opts.max:
    opts.max = 1e+20

allscans = []
metadata = dict()
def process(header,spectrum):
    m = re.search(r'^Scan:(\d+) ',header['TITLE'])
    assert(m)
    allscans.append(int(m.group(1)))
    pmz = float(header['PEPMASS'])
    pz = int(header['CHARGE'].strip('+'))
    pmw = pmz*pz-pz*1.0078
    metadata[int(m.group(1))] = dict(pmz=pmz,pz=pz,pmw=pmw)

inspec = False
for l in open(args[0]):
    l = l.rstrip()
    if l == 'BEGIN IONS':
	inspec = True
	header = {}
	spec = []
        spec.append(l)
	continue
    if l == 'END IONS':
        spec.append(l)
	process(header,spec)
	inspec = False
	continue
    if not inspec:
	continue
    m = re.search(r'^([A-Z]+)=(.*)$',l)
    if m:
	header[m.group(1)] = m.group(2).strip()
    spec.append(l)

# nscans = len(allscans)
if opts.random:
    random.shuffle(allscans)
elif opts.mw:
    allscans.sort(key=lambda s: metadata[s]['pmw'])
else:
    allscans.sort()
wh = open(args[1],'w')
j = 0
for i in range(0,len(allscans),opts.size):
    if j >= opts.max:
	break
    print >>wh, " ".join(map(str,allscans[i:(i+opts.size)]))
    j += 1
wh.close()
