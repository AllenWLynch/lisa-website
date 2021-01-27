#!/usr/bin/python

import sys
import os
import logging

logging.basicConfig(stream=sys.stderr)
#p = '/data/home/qqin/lisa_web'

activate_this = os.path.join('/data/home/qqin/rabit/rabitqqin/', 'bin', 'activate_this.py')
execfile(activate_this, dict(__file__=activate_this))

sys.path.insert(0, '/project/Cistrome/LISA2/lisa_web/')

from lisa_web import app as application