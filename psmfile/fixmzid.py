#!/bin/env python
import sys
import xml.etree.ElementTree as ET

ET.register_namespace('', "http://psidev.info/psi/pi/mzIdentML/1.1")
doc = ET.parse(sys.stdin)
root = doc.getroot()
ns = '{http://psidev.info/psi/pi/mzIdentML/1.1}'

#
#  <Peptide id="Pep_SGLTPLHLVAQEGHVPVADVLIK-115HGVMVDATTR">
#    <PeptideSequence>SGLTPLHLVAQEGHVPVADVLIKHGVMVDATTR</PeptideSequence>
#    <Modification location="0" monoisotopicMassDelta="229.162932">
#      <cvParam cvRef="UNIMOD" accession="UNIMOD:737" name="TMT6plex"/>
#    </Modification>
#    <Modification location="23" monoisotopicMassDelta="229.162932">
#      <cvParam cvRef="UNIMOD" accession="UNIMOD:737" name="TMT6plex"/>
#    </Modification>
#    <Modification location="23" monoisotopicMassDelta="-115.120005">
#      <cvParam cvRef="PSI-MS" accession="MS:1001460" name="unknown modification" value="GlyGlyInsteadOfTMT6plex"/>
#    </Modification>
#  </Peptide>
#

for pep in root.getiterator(ns+'Peptide'):
    # print(ET.tostring(pep, encoding='utf8')) 
    dblmods = dict()
    for mod in pep.findall(ns+'Modification'):
        if mod.find(ns+'cvParam').get('name') in ('TMT6plex','TMTpro'):
            pos = int(mod.get('location'))
            if pos not in dblmods:
                dblmods[pos] = [None,None,None]
            dblmods[pos][0] = mod
        elif mod.find(ns+'cvParam').get('value') in ('GlyGlyInsteadOfTMT6plex','GlyGlyInsteadOfTMTpro'):
            pos = int(mod.get('location'))
            if pos not in dblmods:
                dblmods[pos] = [None,None,None]
            dblmods[pos][1] = mod
        elif mod.find(ns+'cvParam').get('value') in ('AcetylInsteadOfTMT6plex','AcetylInsteadOfTMTpro'):
            pos = int(mod.get('location'))
            if pos not in dblmods:
                dblmods[pos] = [None,None,None]
            dblmods[pos][2] = mod
    for pos,(m1,m2,m3) in dblmods.items():
        if m2 is None and m3 is None:
            continue
        assert(m1 is not None)
        assert(m2 is None or m3 is None)
        if m2 is not None:
            pep.remove(m2)
            m1.set('monoisotopicMassDelta','114.042927')
            cvp = m1.find(ns+'cvParam')
            cvp.set('accession','UNIMOD:121')
            cvp.set('name','GG')
        elif m3 is not None:
            pep.remove(m3)
            m1.set('monoisotopicMassDelta','42.010565')
            cvp = m1.find(ns+'cvParam')
            cvp.set('accession','UNIMOD:1')
            cvp.set('name','Acetyl')

# <SearchModification fixedMod="true" massDelta="229.16293" residues="K">
#   <cvParam cvRef="UNIMOD" accession="UNIMOD:737" name="TMT6plex"/>
# </SearchModification>
# <SearchModification fixedMod="false" massDelta="-115.12" residues="K">
#   <cvParam cvRef="PSI-MS" accession="MS:1001460" name="unknown modification" value="GlyGlyInsteadOfTMT6plex"/>
# </SearchModification>


for sm in root.getiterator(ns+'SearchModification'):
    if sm.find(ns+'cvParam').get('name') in ("TMT6plex","TMTpro"):
        sm.set('fixedMod','false')
    elif sm.find(ns+'cvParam').get('value') in ("GlyGlyInsteadOfTMT6plex","GlyGlyInsteadOfTMTpro"):
        cvp = sm.find(ns+'cvParam')
        cvp.set('cvRef','UNIMOD')
        cvp.set('accession','UNIMOD:121')
        cvp.set('name','GG')
        cvp.attrib.pop('value',None)
        sm.set('massDelta','114.042927')
    elif sm.find(ns+'cvParam').get('value') in ("AcetylInsteadOfTMT6plex","AcetylInsteadOfTMTpro"):
        cvp = sm.find(ns+'cvParam')
        cvp.set('cvRef','UNIMOD')
        cvp.set('accession','UNIMOD:1')
        cvp.set('name','Acetyl')
        cvp.attrib.pop('value',None)
        sm.set('massDelta','42.010565')

print(ET.tostring(root, encoding='utf8')) 
