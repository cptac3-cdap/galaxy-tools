#!/bin/env python

import sys, os, os.path

wh = open(sys.argv[2],'w')
for i,l in enumerate(open(sys.argv[1],'r')):
    if i > 0 and l.startswith('#SpecFile'):                                                                      
        continue                                                                                                 
    wh.write(l+'\n')                                                                                             
wh.close() 
