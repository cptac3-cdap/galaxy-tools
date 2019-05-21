#!/bin/env python
import sys
import xml.etree.ElementTree as ET

def append_element(r,e):
    r.append(e)

def replace_element(r,e0,e1):
    ii = None
    for i,e in enumerate(r):
        if e == e0:
            ii = i
            break
    assert(ii)
    r.insert(ii,e1)
    r.remove(e0)

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def matching_element(r,e):
    act = e.attrib.get('action','merge')
    match = e.attrib.get('match',"").split()
    matches = []
    for ei in r.findall(e.tag):
	nomatch = False
	for k in match:
	    if ei.attrib.get(k) != e.attrib.get(k):
		nomatch = True
		break
	if nomatch:
	    continue
     	matches.append((act,ei))
    if len(matches) == 1:
	return matches[0]
    return 'append',None

def recursive_insert(r0,r1):
    for ele1 in r1:
	action,ele0 = matching_element(r0,ele1)
        if 'action' in ele1.attrib:
            del ele1.attrib['action']
        if 'match' in ele1.attrib:
            del ele1.attrib['match']
	if action == 'merge':
	    recursive_insert(ele0,ele1)
	elif action == 'replace':
	    replace_element(r0,ele0,ele1)
	elif action == 'append':
	    append_element(r0,ele1)

doc = ET.parse(sys.argv[1])
root = doc.getroot()
insdoc = ET.parse(sys.argv[2])
insroot = insdoc.getroot()
assert root.tag == insroot.tag
recursive_insert(root,insroot)
indent(root)
if len(sys.argv) >= 4:
    doc.write(sys.argv[3])
else:
    doc.write(sys.stdout)
