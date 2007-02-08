#!/usr/bin/env python

'''OpenGL and GLU API.

Recommended use is to import * from this package, which exports all GL, GLU
and GL extension functions listed in the OpenGL Registry (pyglet.gl.gl,
pyglet.gl.glu, pyglet.gl.glext_abi and pyglet.gl.glext_missing).

Other commonly required modules are pyglet.gl.gl_info and pyglet.gl.glext_nv
modules.  
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.gl.gl import *
from pyglet.gl.glu import *
from pyglet.gl.glext_abi import *
from pyglet.gl.glext_missing import *
