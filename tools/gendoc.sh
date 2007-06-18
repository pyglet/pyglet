#!/bin/bash
# $Id:$

TOOLS=`dirname $0`
BASE=$TOOLS/..
EPYDOC=$TOOLS/epydoc
PYTHONPATH=$EPYDOC:$BASE:$PYTHONPATH

DOC=$BASE/doc
DOC_HTML=$DOC/html
DOC_HTML_API=$DOC_HTML/api

# Clean old docs and create dir structure
rm -rf $DOC_HTML
mkdir -p $DOC_HTML

# Generate API (html) docs
export PYTHONPATH
$EPYDOC/scripts/epydoc \
    --config=$TOOLS/epydoc.config \
    --css=$TOOLS/epydoc_pyglet.css \
    $*

# Generate html docs
#$TOOLS/gendoc_html.py \
#    --apidoc-dir=$DOC_HTML_API \
#    --html-dir=$DOC_HTML \
#    --depth=2 \
#    --add-navigation \
#    $DOC/programming_guide.txt

#$TOOLS/gendoc_html.py \
#    --html-dir=$DOC_HTML \
#    $DOC/index.txt

# Copy stylesheet
cp $DOC/doc.css $DOC_HTML/doc.css

