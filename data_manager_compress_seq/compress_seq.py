#!/bin/env python27
import sys, os, os.path
from peptidescan.Run import CompressSeqCommandLine, Options
csopt = Options()
assert(os.path.exists(sys.argv[1]))
csopt.set('i',sys.argv[1])
csopt.set('v')
csopt.set('D','false')
cs = CompressSeqCommandLine(csopt)
cs.run()
