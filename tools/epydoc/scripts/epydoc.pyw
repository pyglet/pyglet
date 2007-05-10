#!/usr/bin/python
#
# Call the graphical interface for Epydoc.
#

# We have to do some path magic to prevent Python from getting
# confused about the difference between this epydoc module, and the
# real epydoc package.  So sys.path[0], which contains the directory
# of the script.
import sys, os.path
script_path = os.path.abspath(sys.path[0])
sys.path = [p for p in sys.path if
            os.path.abspath(p) != script_path]

from epydoc.gui import gui
gui()

