#!/usr/bin/env python

from distutils.core import setup

import os

MAIN_PY = 'astraea.py'
DATA_FILES = []
for file in os.listdir('res'):
    file = os.path.join('res', file)
    if os.path.isfile(file):
        DATA_FILES.append(file)

setup_args = dict(
    data_files=[('res', DATA_FILES)]
)

try:
    import py2exe
    setup_args.update(dict(
        windows=[dict(
            script=MAIN_PY,
            icon_resources=[(1, 'res/astraea.ico')],
        )],
    ))
except ImportError:
    pass

setup(**setup_args)
