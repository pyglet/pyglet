#!/usr/bin/env python
from __future__ import print_function
import os
import os.path as op
import sys
import shutil
import inspect
import webbrowser
from subprocess import call, check_output

THIS_DIR = op.dirname(op.abspath(__file__))
DOC_DIR = op.join(THIS_DIR, 'doc')

def clean():
    dirs = [op.join(DOC_DIR, '_build')]
    for d in dirs:
        print('   Removing:', d)
        shutil.rmtree(d, ignore_errors=True)

def docs():
    make_bin = 'make.exe' if sys.platform=='win32' else 'make'

    call([make_bin, 'html'], cwd=DOC_DIR)
    if '--no-open' not in sys.argv:
        webbrowser.open('file://'+op.abspath(DOC_DIR)+'/_build/html/index.html')

if __name__=='__main__':
    avail_cmds = dict(filter(lambda kv: not kv[0].startswith('_') 
                             and inspect.isfunction(kv[1])
                             and kv[1].__module__ == '__main__',
                             locals().items()))
    try:
        cmd = avail_cmds[sys.argv[1]]
    except Exception as exc:
        print(type(exc).__name__, ':', exc)
        print('Usage:', op.basename(sys.argv[0]), '<command>')
        print('  where commands are:', ', '.join(avail_cmds))
    else:
        cmd()
