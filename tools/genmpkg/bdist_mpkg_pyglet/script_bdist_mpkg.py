#!/usr/bin/env python

import sys, os

import setuptools
import bdist_mpkg_pyglet

def main():
    del sys.argv[0]
    if not sys.argv:
        sys.argv[:0] = ['setup.py', '--open']
    elif sys.argv[0].startswith('-'):
        sys.argv[:0] = ['setup.py']
    elif len(sys.argv) == 1:
        sys.argv[1:1] = ['--open']
    sys.argv.insert(1, 'bdist_mpkg_pyglet')
    if os.path.isdir(sys.argv[0]):
        sys.argv[0] = os.path.join(sys.argv[0], 'setup.py')
    path, name = os.path.split(os.path.abspath(sys.argv[0]))
    if path:
        os.chdir(path)
    sys.path.insert(0, path)
    sys.argv[0] = name
    g = dict(globals())
    g['__file__'] = sys.argv[0]
    g['__name__'] = '__main__'
    execfile(sys.argv[0], g, g)

if __name__ == '__main__':
    main()
