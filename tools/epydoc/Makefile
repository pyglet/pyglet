############################################################
##  epydoc Makefile
##
##  Edward Loper
############################################################

##//////////////////////////////////////////////////////////////////////
## Configuration variables
##//////////////////////////////////////////////////////////////////////

# Where do man pages and documentation go?
LIB = /usr/share
MAN = ${LIB}/man/
DOC = ${LIB}/doc/

# What version of python to use?
PYTHON = python

##//////////////////////////////////////////////////////////////////////
## Makefile
##//////////////////////////////////////////////////////////////////////
all: usage
usage:
	@echo "Usage:"
	@echo "  make install -- Install epydoc"
	@echo "  make installdocs -- Install the documentation for epydoc"

install:
	$(PYTHON) setup.py install

docs: installdocs
installdocs:
	@test -e ${MAN} || \
	    echo "Could not find ${MAN}; check the makefile variables."
	@test -e ${DOC} || \
	    echo "Could not find ${DOC}; check the makefile variables."
	@test -e ${MAN}
	@test -e ${DOC}
	test -e doc || ln -s ../webpage doc
	test -e man || ln -s ../man man
	cp man/*.1 ${MAN}/man1/
	cp -r doc ${DOC}/epydoc/

##//////////////////////////////////////////////////////////////////////
## These targets should only be called from
## the cvs repository (not from distributions).
##//////////////////////////////////////////////////////////////////////

# Clean.  
#    - Erase any pyc and pyo files.
#    - Get rid of build/dist directories
clean:
	rm -rf build dist MANIFEST
	rm -f *.pyc epydoc/*.pyc epydoc/*/*.pyc
	rm -f *.pyo epydoc/*.pyo epydoc/*/*.pyo
	rm -f doc man 2>/dev/null || true

# Distributions.
# Build all from scratch; and create links for convenient access.
distributions: clean sdist bdist

# Source distributions
sdist: gztardist zipdist

# Built distributions
bdist: rpmdist windist

# Produce dist/$(NAME)-$(VERSION).tar.gz
gztardist:
	test -e doc || ln -s ../webpage doc
	test -e man || ln -s ../man man
	$(PYTHON) setup.py -q sdist --format=gztar

# Produce dist/$(NAME)-$(VERSION).tar.gz
zipdist:
	test -e doc || ln -s ../webpage doc
	test -e man || ln -s ../man man
	$(PYTHON) setup.py -q sdist --format=zip

# Produce dist/$(NAME)-$(VERSION)-1.noarch.rpm
# Produce dist/$(NAME)-$(VERSION)-1.src.rpm
rpmdist:
	test -e doc || ln -s ../webpage doc
	test -e man || ln -s ../man man
	$(PYTHON) setup.py -q bdist --format=rpm

# Produce dist/$(NAME)-$(VERSION).win32.exe
windist:
	test -e doc || ln -s ../webpage doc
	test -e man || ln -s ../man man
	$(PYTHON) setup.py -q bdist --format=wininst
