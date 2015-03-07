#!/bin/bash
# $Id$

base=`dirname $0`/..
cd $base

VERSION=`grep 'VERSION =' setup.py | cut -d "'" -f2`

# Source dists
python setup.py sdist --formats=gztar,zip

# Wheels
python2 setup.py bdist_wheel
python3 setup.py bdist_wheel 

# Build docs archive
rm dist/pyglet-docs-$VERSION.zip
(cd doc/_build; zip -r docs.zip html)
mv doc/_build/docs.zip dist/pyglet-docs-$VERSION.zip
# Add the examples
zip -r dist/pyglet-docs-$VERSION.zip examples
