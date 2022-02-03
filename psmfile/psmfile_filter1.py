#!/bin/env python27

import sys, os, os.path, csv, re, math
from collections import defaultdict
from operator import itemgetter

sys.path.append(os.path.abspath(os.path.join(os.path.split(sys.argv[0])[0],"../lib/python")))
from peptidescan.PeptideRemapper import PeptideRemapper, FirstWord

infile = sys.argv[1].strip()
proms = sys.argv[2].strip()
reporterfile = sys.argv[3].strip()
outfile = sys.argv[4].strip()
threshold = float(sys.argv[5])/100.0
opts = dict()
for arg in sys.argv[6:]:
    if arg.startswith('seqdb:'):
	opts['seqdb'] = arg[6:]
    else:
        opts[arg] = True
# print(opts)

promsdata = defaultdict(lambda: ('0','0.00000000','0'))
if proms not in ("None","",None):
    h = open(proms)
    sec7 = False
    for l in h:
	if l.strip() == 'Section 7 starts':
	    sec7 = True
	    continue
	if l.strip() in ('end of section 7','End'):
	    sec7 = False
            continue
	if sec7:
	    if l.startswith('Nvalues='):
		continue
	    sl = l.split()
	    scan = int(sl[1])
	    absprec = sl[21]
	    relprec = sl[20]
	    rthalfprec = sl[15]
	    # note, leave all values as string...
	    assert scan not in promsdata
	    promsdata[scan] = (absprec,relprec,rthalfprec)

labeling_metadata = """
option    label    prefix   tags
itraq     iTRAQ    iTRAQ    114 115 116 117
itraq4    iTRAQ    iTRAQ    114 115 116 117
tmt6      TMT6     TMT6-    126 127 128 129 130 131
tmt10     TMT10    TMT10-   126 127N 127C 128N 128C 129N 129C 130N 130C 131
tmt11     TMT11    TMT11-   126C 127N 127C 128N 128C 129N 129C 130N 130C 131N 131C
"""

labelingmd = dict()
headers = None
for l in labeling_metadata.splitlines():
    if not l:
        continue
    if not headers:
        headers = l.split()
        continue
    row = dict(zip(headers,l.split(None,3)))
    row['tags'] = row['tags'].split()
    row['ntags'] = len(row['tags'])
    labelingmd[row['option']] = row

opts['labeling'] = None
for labeling in labelingmd:
    if opts.get(labeling):
        assert not opts.get('labeling')
        opts['labeling'] = labeling

def tofloat(v):
    try:
        return float(v)
    except (TypeError,ValueError):
        pass
    return None

def round_to_n(x, n):
    if not x: return 0
    power = -int(math.floor(math.log10(abs(x)))) + (n - 1)
    factor = (10 ** power)
    val = round(x * factor) / factor
    if round(val) == val:
        val = int(val)
    return val

reporterdata = None
if reporterfile not in ("None","",None):
    reporterdata = dict()
    lmd = labelingmd[opts['labeling']]
    for r in csv.reader(open(reporterfile),dialect='excel-tab'):
        targetscan = int(r[0])
        assert r[1] == lmd['label']
        nlabels = lmd['ntags']
        assert len(r) == 2+nlabels+nlabels+1
        p = 2
        ab = r[p:(p+nlabels)]
        abvals = map(tofloat,ab)
        assert None not in abvals
        p += nlabels
        dmzhwhm = r[p:(p+nlabels)]
        dmzhwhmvals = filter(lambda v: v != None,map(tofloat,dmzhwhm))
        p += nlabels
        abfract = tofloat(r[p])
        data = dict()
        if max(abvals) == 0:
            assert dmzhwhm.count('?') == len(dmzhwhm) and abfract in None
            for t,abi,di in zip(lmd['tags'],ab,dmzhwhm):
                data[lmd['prefix']+t] = abi
        else:
            for t,abi,di in zip(lmd['tags'],ab,dmzhwhm):
                data[lmd['prefix']+t] = "%s/%s"%(abi,di)
            data[lmd['prefix']+"FractionOfTotalAb"] = abfract
        data[lmd['prefix']+"Abundance"] = abvals
        data[lmd['prefix']+"dMz/HWHM"] = dmzhwhmvals
        data[lmd['prefix']+"TotalAb"] = ("%.6g"%round_to_n(sum(abvals),6)).replace('e+','e+0')        
        reporterdata[targetscan]= data

def barepepseq(pepseq):
    modpep = re.split(r'([A-Z])',pepseq)
    barepepseq = ""
    for i in range(1,len(modpep),2):
	barepepseq += modpep[i]
    return barepepseq

pepmap = None
mappedpeptides = set()
if opts.get('deglycopeptide') and opts.get('seqdb'):
    for row in csv.DictReader(open(infile),dialect='excel-tab'):
	pepseq = row['Peptide']
	m = re.search(r'N([+-]\d+(\.\d+)?)$',pepseq)
	if m and abs(float(m.group(1)) - 0.984016) < 1e-2:
	    mappedpeptides.add(barepepseq(pepseq))
    pepmap = PeptideRemapper(list(mappedpeptides),opts.get('seqdb'),FirstWord(),preprocess=True)

inrows = csv.DictReader(open(infile),dialect='excel-tab')

simplefieldre = re.compile(r'^(\w+):(\d+(\.\d+)?(eV|\?)?)$')

ambigscans = set()

# These fields are renamed in psm file format...
headermapping = """
#SpecFile           FileName
Precursor           QueryPrecursorMz
PrecursorMonoisoMZ  OriginalPrecursorMz
Charge              QueryCharge
PrecursorCharge     OriginalCharge
PrecursorScan       PrecursorScanNum
Peptide             PeptideSequence
EValue              Evalue
QValue              Qvalue
PepQValue           PepQvalue
HCD                 HCDEnergy
"""
headermapping = dict(map(str.split,filter(lambda s: s.strip() != "",headermapping.splitlines())))

def manipulate_rows(rows,qvalthr):
    lastscan=None; lastscore = None
    for r in rows:
        scan,title,qvalue,score,pepseq = map(r.get,('ScanNum','Title','QValue','MSGFScore','Peptide'))
	if scan == 'ScanNum':
	    # extra header row, ignore
	    continue
        qvalue = float(qvalue);
        if qvalue > qvalthr:
            continue

	# Special rule for Ubiquitylome analysis, remove any peptide with
	# K+114.043 at the end (no trypsin digest where GG tag is attached.
	if opts.get('ubiquityl'):
	    m = re.search(r'K\+(\d+(\.(\d+)?)?)$',pepseq)
	    if m and abs(float(m.group(1)) - 114.04927) < 1e-2:
	        continue

	# Special rule for detatched glycan analysis. This is problematic
	# since we may not have sufficient sequence context to absolutely
	# determine whether there is a S or T two characters from site
	# of deamidation in the protein, if the deamidation site is in
	# the last or second last position of the peptide sequence. We
	# can only clean this up properly once we have aligned the
	# peptide sequence. Nevertheless, we remove any peptide with
	# deamidation on N that does not have an S or T in the right spot.
	if opts.get('deglycopeptide'):
	    proteins = []
	    if barepepseq(pepseq) in mappedpeptides:
		for pracc,laa,raa in map(itemgetter(0,2,5),pepmap.proteins(barepepseq(pepseq))):
		    proteins.append((pracc,laa,raa))
            else:
	        for pr in r['Protein'].split(';'):
		    m = re.search(r'^(.*)[(]pre=([A-Z-]*),post=([A-Z-]*)[)]$',pr)
	            assert m
		    proteins.append((m.group(1),m.group(2),m.group(3)))

	    keptproteins = []
	    for pracc,laa,raa in proteins:
		pepseq1 = pepseq + raa
		modpep = re.split(r'([A-Z])',pepseq1)
		bad = False
		for i in range(1,len(modpep)-4,2):
		    if modpep[i] == "N" and modpep[i+1] and abs(float(modpep[i+1]) - 0.984016) < 1e-2:
			if modpep[i+4] not in "ST":
			    bad = True
		if not bad:
		    keptproteins.append((pracc,laa,raa))
	    
	    if len(keptproteins) == 0:
		continue

            r['Proteins'] = ";".join(["%s(pre=%s,post=%s)"%(pracc,laa[-1],raa[0]) for pracc,laa,raa in keptproteins])

        if scan == lastscan:
            rank += 1
            if score < lastscore:
                trank += 1
        else:
            rank = 1; trank = 1
        lastscan = scan; lastscore = score
        for k,v in r.items():
            try:
                r[k] = float(v)
                r[k] = int(v)
            except ValueError:
                pass
        r['Index'] = rank; r['Rank'] = trank
        if rank > 1:
            ambigscans.add(int(scan))
        # Filter may have spaces in it, but it is last field in the string...
	if title:
             rest,filter = title.rsplit('Filter:',1)
	else:
	     rest = ""; filter = ""
        r['Filter'] = filter.strip()
	# print r['ScanNum']
        ppvals = None
        for keyval in rest.split():
            # print repr(keyval)
            m = simplefieldre.search(keyval)
            if m:
                key = m.group(1)
                try:
                    value = m.group(2)
                    value = float(m.group(2))
                    value = int(m.group(2))
                except ValueError:
                    pass
                r[key] = value
                # print repr(key),repr(value)
                continue
            if keyval.startswith('pp:'):
                key = "PrecursorPurity"
                value = keyval[3:]
		value = value.replace('?','0.0')
                try:
                    ppvals = map(float,value.split(','))
                except ValueError:
                    ppvals = None
                r[key] = value
                # print repr(key),repr(value)
		try:
	            ppv1 = 100.0*r['IRI-1:p%']/r['IRI-1:c%']
		except KeyError:
		    ppv1 = 0.0
		try:
	            ppv2 = 100.0*r['IRI-2:p%']/r['IRI-2:c%']
		except KeyError:
		    ppv2 = 0.0
		r[key] = "%.1f,%.1f"%(round(ppv1,1),round(ppv2,1))
		ppvals = [ppv1,ppv2]
		# if r['ScanNum'] == 3790:
		#    print ppvals,map(lambda v: round(v,1),ppvals),map(lambda v: "%.1f"%v,ppvals)
                continue
	    if keyval.startswith('IRI-1('):
		m = re.search(r'^IRI-1\((.*)\)(;([^;]*))?(;([^;]*))?$',keyval)
		assert m and m.group(1), keyval
		if m.group(1):
		    srest = re.split(r',([a-zA-Z/%0-9]+):',m.group(1))
                    # print srest
                    for i in range(1,len(srest),2):
                        k = srest[i]
                        v = srest[i+1]                                                                           
                        if k in ('c%',) and 'IRI-1:'+k not in r:
			    try:
                                r['IRI-1:'+k] = float(v)
			    except ValueError:
				pass
		if m.group(2):
		    srest = re.split(r',([a-zA-Z/%0-9]+):',m.group(3))
		    # print srest
		    for i in range(1,len(srest),2):
		        k = srest[i]
		        v = srest[i+1]
		        if k in ('f2e%','p%') and 'IRI-1:'+k not in r:
			    try:
			        r['IRI-1:'+k] = float(v)
			    except ValueError:
				pass
	    if keyval.startswith('IRI-2('):
		m = re.search(r'^IRI-2\((.*)\)(;([^;]*))?(;([^;]*))?$',keyval)
		assert m and m.group(1), keyval
		if m.group(1):
		    srest = re.split(r',([a-zA-Z/%0-9]+):',m.group(1))
		    # print srest
		    for i in range(1,len(srest),2):
		        k = srest[i]
		        v = srest[i+1]
		        if k in ('c%',) and 'IRI-2:'+k not in r:
			    try:
			        r['IRI-2:'+k] = float(v)
			    except ValueError:
				pass
		if m.group(2):
		    srest = re.split(r',([a-zA-Z/%0-9]+):',m.group(3))
		    # print srest
		    for i in range(1,len(srest),2):
		        k = srest[i]
		        v = srest[i+1]
		        if k in ('f2e%','p%') and 'IRI-2:'+k not in r:
			    try:
			        r['IRI-2:'+k] = float(v)
			    except ValueError:
				pass
	    if keyval.startswith('LT2/t:'):
	        key = 'LT2/t'
		try:
		    value = float(keyval[6:])
		except ValueError:
		    value = 0.0
		r[key] = value
            if keyval.startswith('HCD='):
                key = "HCD"
                value = keyval[4:]
                r[key] = value
                # print repr(key),repr(value)
                continue
            if not reporterdata and keyval.startswith('iTRAQ4_'):
                tags = (114,115,116,117)
		ab = []; abfract = None; abvals = []
		dmzhwhm = ['']; dmzhwhmvals = []
                for m in re.finditer(r'_([^(]+)\(([^)]+)\)',keyval):
                    if m.group(1) == 'ab':
                        ab = m.group(2).split(',')
			for v in ab:
                            try:
				v = abvals.append(float(v))
                            except ValueError:
				pass
                    elif m.group(1) == 'dMz/HWHM':
                        dmzhwhm = m.group(2).split(',')
			for v in dmzhwhm:
                            try:
				dmzhwhmvals.append(float(v))
                            except ValueError:
				pass
                    elif m.group(1) == 'AbFract':
                        abfract = float(m.group(2))
                for t,v1,v2 in zip(tags,ab,dmzhwhm):
                    r["iTRAQ"+str(t)] = "%s/%s"%(v1,v2)
		if abfract != None:
                    r["iTRAQFractionOfTotalAb"] = abfract
		if len(ab) > 0:
                  r["iTRAQTotalAb"] = ("%.6g"%round_to_n(sum(map(float,ab)),6)).replace('e+','e+0')
                continue
            if not reporterdata and (keyval.startswith('TMT10_') or keyval.startswith('TMT11_') or keyval.startswith('TMT6_')):
	        if keyval.startswith('TMT10_'):
		    prefix="TMT10"
                    tags = "126 127N 127C 128N 128C 129N 129C 130N 130C 131".split()
	        elif keyval.startswith('TMT6_'):
		    prefix="TMT6"
                    tags = "126 127 128 129 130 131".split()
		elif keyval.startswith('TMT11_'):
		    prefix="TMT11"
                    tags = "126C 127N 127C 128N 128C 129N 129C 130N 130C 131N 131C".split()
		else:
		    raise RuntimeError("Problem with TMT key-values")
		
		ab = []; abfract = None; abvals = []
		dmzhwhm = ['']*len(tags); dmzhwhmvals = []
		# print "----------------------------------------------"
		# print keyval
                for m in re.finditer(r'_([^(]+)\(([^)]+)\)',keyval):
		    # print m.group(1),m.group(2)
                    if m.group(1) == 'ab':
                        ab = m.group(2).split(',')
			for v in ab:
                            try:
				v = abvals.append(float(v))
                            except ValueError:
				pass
                    elif m.group(1) == 'dMz/HWHM':
                        dmzhwhm = m.group(2).split(',')
			for v in dmzhwhm:
                            try:
				dmzhwhmvals.append(float(v))
                            except ValueError:
				pass
		    elif m.group(1) == 'AbFract':
                        abfract = float(m.group(2))
		if len(ab) == 0:
		    continue
		assert len(tags) == len(ab) and len(tags) == len(dmzhwhm)
                for t,v1,v2 in zip(tags,ab,dmzhwhm):
		    if v2 == "":
                        r[prefix+"-"+str(t)] = "%s"%(v1,)
		    else:
                        r[prefix+"-"+str(t)] = "%s/%s"%(v1,v2)
		if abfract != None:
                    r[prefix+"-FractionOfTotalAb"] = abfract
		if len(ab) > 0:
                    r[prefix+"-TotalAb"] = ("%.6g"%round_to_n(sum(map(float,ab)),6)).replace('e+','e+0')
                    # r["TMT10-TotalAb"] = ("%.6g"%sum(map(float,ab))).replace('e+','e+0')
		    # if r["ScanNum"] in (7902,16886):
		    #     print sum(map(float,ab)),round_to_n(sum(map(float,ab)),6),"%.6g"%sum(map(float,ab))
		# print r
                continue

        for k,v in headermapping.items():
            if k in r:
                r[v] = r[k]

        if reporterdata:
            if r['ScanNum'] in reporterdata:
                lmd = labelingmd[opts['labeling']]
                r.update(reporterdata[r['ScanNum']])
                abvals = reporterdata[r['ScanNum']][lmd['prefix']+'Abundance']
                dmzhwhmvals = reporterdata[r['ScanNum']][lmd['prefix']+'dMz/HWHM']
            else:
                lmd = labelingmd[opts['labeling']]
                for t in lmd['tags']:
                    r[lmd['prefix']+t] = 0
                r[lmd['prefix']+'TotalAb'] = 0
                abvals = [0]*len(lmd['tags']); dmzhwhmvals = [];

        if opts.get('labeling'):
            lmd = labelingmd[opts['labeling']]
            flagkey = lmd['prefix']+"Flags"
            r[flagkey] = ""
            if len(abvals) > 0 and min(abvals) == 0.0:
                r[flagkey] += "M"
            if len(dmzhwhmvals) > 0 and max(map(abs,dmzhwhmvals)) > 1:
                r[flagkey] += "D"
            if ppvals != None and math.sqrt(ppvals[0]*ppvals[1])<90:
                r[flagkey] += "I"

	def decomp(f2e,LT2_t):
	    # print f2e,LT2_t,
	    f2e /= 100.0
	    c_b_1 = 1.0/f2e
	    a_b = LT2_t * c_b_1 - c_b_1
	    # print a_b/(1.0 + a_b),
	    return a_b/(1.0 + a_b)
	
	# print r['ScanNum'],
	try:
	    r['LT2/t'] = 10.0**float(r['LT2/t'])
	except (ValueError, TypeError, KeyError):
	    r['LT2/t'] = 10.0**0
	val = []
	for i in (1,2):
	  key = 'IRI-%d:f2e%%'%i
	  if r.get(key,-1) >= 0:
	    f2e = r[key]
	    if f2e == 0.0:
		val.append('100.0')
	    else:
		val.append("%.1f"%(100.0*decomp(f2e,r['LT2/t'],)))
	  else:
	    val.append('?')
	# print
	r['FractionDecomposition'] = ','.join(val)

        # Recompute PrecursorError(ppm) based on??????

	if r.get('OriginalPrecursorMz'):
            r['OriginalPrecursorMz'] = "%0.4f"%r['OriginalPrecursorMz']
	elif r.get('PrecursorMonoisoMZ'):
            r['OriginalPrecursorMz'] = "%0.4f"%r['PrecursorMonoisoMZ']
	elif r.get('ms1PrecursorMZ'):
	    r['OriginalPrecursorMz'] = "%0.4f"%r['ms1PrecursorMZ']
	else:
	    r['OriginalPrecursorMz'] = ""

	if r['FileName'].endswith('.mgf'):
            r['FileName'] = (r['FileName'][:-3]+'raw')
	elif r['FileName'].endswith('.mzML'):
            r['FileName'] = (r['FileName'][:-4]+'raw')

        yield r

def setambig(scans,rows):
    for r in rows:
        if r['ScanNum'] in scans:
            r['AmbiguousMatch'] = 1
        else:
            r['AmbiguousMatch'] = 0
        yield r

def addproms(proms,rows):
    for r in rows:
	r.update(dict(zip(('PrecursorArea','PrecursorRelAb','RTAtPrecursorHalfElution'),proms[r['ScanNum']])))
	yield r

# Sorted forces all rows to be instatiated, so ambigscans is set by the time it is used...
outrows = addproms(promsdata,
              setambig(ambigscans,
                  sorted(manipulate_rows(inrows,threshold), 
			 key=lambda r: map(r.get,('Scan','Index')))))

# Basic/common headers
outheaders = """
FileName
ScanNum
QueryPrecursorMz
OriginalPrecursorMz
PrecursorError(ppm)
QueryCharge
OriginalCharge
PrecursorScanNum
PeptideSequence
AmbiguousMatch
Protein
DeNovoScore
MSGFScore
Evalue
Qvalue
PepQvalue
PrecursorPurity
FractionDecomposition
HCDEnergy
""".split()
# Insert ProMS headers immediately before PeptideSequence
if proms not in ("None","",None):
    outheaders.insert(outheaders.index('PeptideSequence'),"PrecursorArea")
    outheaders.insert(outheaders.index('PeptideSequence'),"PrecursorRelAb")
    outheaders.insert(outheaders.index('PeptideSequence'),"RTAtPrecursorHalfElution")

# Append Reporter Ion headers at the end
if opts.get('labeling'):
    lmd = labelingmd[opts['labeling']]
    for t in lmd['tags']:
        outheaders.append(lmd['prefix']+t)
    outheaders.append(lmd['prefix']+'Flags')
    outheaders.append(lmd['prefix']+'FractionOfTotalAb')
    outheaders.append(lmd['prefix']+'TotalAb')

# Insert Phospho header at the end (after iTRAQ/TMT if present)
if opts.get('phospho'):
    outheaders.extend('PhosphoRSPeptide	nPhospho	FullyLocalized'.split())
writer=csv.DictWriter(open(outfile,'w'),fieldnames=outheaders,extrasaction='ignore',dialect='excel-tab')
writer.writeheader()
writer.writerows(outrows)

