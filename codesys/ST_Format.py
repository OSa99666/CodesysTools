# CODESYS toolbar script: format all ST objects, then check naming.
from __future__ import print_function
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import st_codesys
st_codesys.run_format(projects, system, Severity)
