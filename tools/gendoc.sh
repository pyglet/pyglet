#!/bin/bash
# $Id:$

TOOLS=`dirname $0`
BASE=$TOOLS/..
EPYDOC=$TOOLS/epydoc
PYTHONPATH=$EPYDOC:$BASE:$PYTHONPATH
export PYTHONPATH

DOC=$BASE/doc
DOC_HTML=$DOC/html
DOC_HTML_API=$DOC_HTML/api
DOC_HTML_GUIDE=$DOC_HTML/programming_guide
DOC_PDF=$DOC/pdf

function clean() {
    # Clean old docs, not needed usually
    echo "Removing doc directories..."
    rm -rf $DOC_HTML
    rm -rf $DOC_PDF
}

function html_api() {
    # Generate API (html) docs
    echo "Generating HTML API..."
    rm -rf $DOC_HTML_API
    mkdir -p $DOC_HTML_API
    $EPYDOC/scripts/epydoc \
        --config=$TOOLS/epydoc.config \
        --css=$TOOLS/epydoc_pyglet.css \
        -v
}

function html_guide() {
    echo "Generating HTML guide..."
    # Generate html docs
    rm -rf $DOC_HTML_GUIDE
    mkdir -p $DOC_HTML_GUIDE
    $TOOLS/gendoc_html.py \
        --apidoc-dir=$DOC_HTML_API \
        --html-dir=$DOC_HTML_GUIDE \
        --depth=1 \
        --add-navigation \
        $DOC/programming_guide/index.txt

    $TOOLS/gendoc_html.py \
        --html-dir=$DOC_HTML \
        $DOC/index.txt

    # Copy stylesheet
    cp $DOC/doc.css $DOC_HTML/doc.css
    cp $DOC/doc.css $DOC_HTML_GUIDE/doc.css
}

function pdf_guide() {
    echo "Generating PDF guide..." 
    # hack this on
    python $TOOLS/gendoc_pdf.py
}

function usage() {
    echo "Usage: $0 ([clean] [html-api] [html-guide] [pdf-guide]) | all"
}

if [ -z "$1" ]
then
    usage
fi

until [ -z "$1" ]
do
    case "$1" in
        "clean"     ) clean;;
        "html-api"  ) html_api;;
        "html-guide") html_guide;;
        "pdf-guide" ) pdf_guide;;
        "all"       ) clean; html_api; html_guide; pdf_guide;;
        *           ) usage; exit 1;;
    esac
    shift
done
