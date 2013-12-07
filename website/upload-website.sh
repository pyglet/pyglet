#!/bin/bash
# $Id:$

PYGLET_USR=pyglet
PYGLET_ORG=pyglet.org
PYGLET_DIR=/home/pyglet/www

rsync -rv dist/* $PYGLET_USR@$PYGLET_ORG:$PYGLET_DIR/
#rsync -rv ../doc/html/* $PYGLET_ORG:$PYGLET_DIR/doc/
#rsync -rv ../doc/pdf/* $PYGLET_ORG:$PYGLET_DIR/doc/
