#!/bin/bash
# $Id:$

PYGLET_ORG=66.35.48.21
PYGLET_DIR=/home/pyglet/www

rsync -rv website/dist/* $PYGLET_ORG:$PYGLET_DIR/
#rsync -rv doc/html/* $PYGLET_ORG:$PYGLET_DIR/doc/
#rsync -rv doc/pdf/* $PYGLET_ORG:$PYGLET_DIR/doc/
