#!/bin/bash
# $Id:$

TOOLS=`dirname $0`
BASE=$TOOLS/..
EPYDOC=$TOOLS/epydoc
PYTHONPATH=$EPYDOC:$BASE:$PYTHONPATH

MODULES_EXCLUDE='pyglet.window.xlib|pyglet.window.carbon|pyglet.window.win32'

export PYTHONPATH
export MODULES_EXCLUDE
$EPYDOC/scripts/epydoc \
    --config=$TOOLS/epydoc.config \
    --css=$TOOLS/epydoc_pyglet.css \
    $*
