#!/bin/bash

PYGLET_USR=pyglet
PYGLET_ORG=pyglet.org
PYGLET_DIR=/home/pyglet/www

make clean
mkdir _build/html
make html

rsync -az --delete _build/html/ -e "ssh -p 6185" $PYGLET_USR@$PYGLET_ORG:$PYGLET_DIR/doc-current

