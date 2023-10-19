#!/bin/env python

import sys, os, os.path, csv, re

headers = None
for l in sys.stdin:
    sl = l.rstrip().split('\t')
    if not headers:
        headers = sl
        print "\t".join(headers)
        continue
    r = dict(zip(headers,sl))
    newpep = []
    spep = re.split(r'([A-Z]+)',r['Peptide'])
    for i in range(len(spep)):
        if not spep[i]:
            continue
	if spep[i][0] not in '0123456789+-':
	    newpep.append(spep[i])
	else:
	    newpep.append("%+.3f"%(eval(spep[i]),))
    # print >>sys.stderr, newpep
    r['Peptide'] = "".join(newpep)
    print "\t".join(map(r.get,headers))
