#!/bin/env python

import sys, os, os.path, csv, re

dr = csv.DictReader(sys.stdin,dialect='excel-tab')
for i,r in enumerate(dr):
    if i == 0:
	print "\t".join(dr.fieldnames)
    newpep = []
    spep = re.split(r'([A-Z]+)',r['Peptide'])
    # print >>sys.stderr, spep
    for i in range(len(spep)):
        if not spep[i]:
            continue
	if spep[i][0] not in '0123456789+-':
	    newpep.append(spep[i])
	else:
	    newpep.append("%+.3f"%(eval(spep[i]),))
    # print >>sys.stderr, newpep
    r['Peptide'] = "".join(newpep)
    print "\t".join(map(r.get,dr.fieldnames))
