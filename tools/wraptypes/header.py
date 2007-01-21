#!/usr/bin/env python

'''Parse a C header file.

Unlike the ctypes-gen wrapper or GCC-XML, we take note of #ifdefs because
the gengl.py script needs them preserved rather than filtered.  Macros
are expanded as usual.

Support only for reading constants, typedefs and functions at this stage,
no structs or (hah) inline blocks.

Requires Plex (http://www.cosc.canterbury.ac.nz/greg.ewing/python/Plex/).
You can download and install it into your search path, or just include
'pyglet/layout/Plex' in your PYTHONPATH.
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'


