#!/bin/env python

import sys, re

selected_scans = set(map(int,open(sys.argv[2]).read().split()))

wh = open(sys.argv[3],'w')

def process(header,spectrum):
    m = re.search(r'^Scan:(\d+) ',header['TITLE'])
    assert(m)
    scan = int(m.group(1))
    if scan in selected_scans:
	print >>wh, "\n".join(spectrum)

inspec = False
for l in open(sys.argv[1]):
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

wh.close()
