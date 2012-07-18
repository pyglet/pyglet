#!/bin/bash
# $Id$

base=`dirname $0`/..
cd $base

VERSION=`grep 'VERSION =' setup.py | cut -d "'" -f2`

# Source dists
python setup.py sdist --formats=gztar,zip

# Eggs
#python2.4 setup.py bdist_egg --exclude-source-files
#python2.5 setup.py bdist_egg --exclude-source-files
python2.6 setup.py bdist_egg --exclude-source-files
python2.7 setup.py bdist_egg --exclude-source-files
python3.3 setup.py bdist_egg --exclude-source-files

# Build docs archive
python setup.py sdist --manifest-only
rm dist/pyglet-docs-$VERSION.zip
(cd doc/_build; zip -r docs.zip html)
mv doc/_build/docs.zip dist/pyglet-docs-$VERSION.zip
zip dist/pyglet-docs-$VERSION.zip `grep '^examples/' MANIFEST`
