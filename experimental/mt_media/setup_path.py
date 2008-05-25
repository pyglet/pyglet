#!/usr/bin/python
# $Id: setup_path.py 1580 2008-01-15 15:08:39Z Alex.Holkner $

import os.path
import sys

script_dir = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(script_dir, '..', '..'))
sys.path.insert(0, script_dir)
