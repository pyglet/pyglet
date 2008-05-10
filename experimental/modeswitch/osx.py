#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

# Patch for window/carbon/__init__.py::
# (in _create)
#
# fs_width = c_short(width)
# fs_height = c_short(width)
#
# ... that's it :-)
