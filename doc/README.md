# Building the documentation

## Basic

Install doc requirements:

    pip install -r doc/requirements.txt

The simpleast way build html docs:

    python setup.py build_sphinx

The build result will appear in a `_build` directory in the root of the project.

## Advanced

The more advanced way to building docs is using `make`
(`make.bat` for windows).

    cd doc/
    make html

The HTML docs will be generated in the `doc/_build` subdirectory.

Please run `make help` for a complete list of targets, but be aware that some
of them may have extra requirements.

    $ make help
    Please use `make <target>' where <target> is one of
    html       to make standalone HTML files
    dirhtml    to make HTML files named index.html in directories
    singlehtml to make a single large HTML file
    pickle     to make pickle files
    json       to make JSON files
    htmlhelp   to make HTML files and a HTML help project
    qthelp     to make HTML files and a qthelp project
    devhelp    to make HTML files and a Devhelp project
    epub       to make an epub
    latex      to make LaTeX files, you can set PAPER=a4 or PAPER=letter
    latexpdf   to make LaTeX files and run them through pdflatex
    text       to make text files
    man        to make manual pages
    texinfo    to make Texinfo files
    info       to make Texinfo files and run them through makeinfo
    gettext    to make PO message catalogs
    changes    to make an overview of all changed/added/deprecated items
    linkcheck  to check all external links for integrity
    doctest    to run all doctests embedded in the documentation (if enabled)
