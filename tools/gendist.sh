#!/bin/bash
# $Id$

base=`dirname $0`/..
cd $base

VERSION=`grep 'VERSION =' setup.py | cut -d "'" -f2`

# Source dists
python setup.py sdist --formats=gztar,zip

# Eggs
python2.4 setup.py bdist_egg --exclude-source-files
python2.5 setup.py bdist_egg --exclude-source-files
python2.6 setup.py bdist_egg --exclude-source-files

# Build docs archive
python setup.py sdist --manifest-only
rm dist/pyglet-$VERSION-docs.zip
grep -v ^pyglet MANIFEST | zip dist/pyglet-$VERSION-docs.zip -@
