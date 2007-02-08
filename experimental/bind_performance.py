#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from timeit import Timer

NUMBER=100000

setup='''
from pyglet.gl.VERSION_1_1 import glBindTexture, glEnable, GL_TEXTURE_2D
from pyglet.gl.VERSION_1_1 import glBegin, glEnd, glVertex2f, GL_LINES
from pyglet.window import Window
from pyglet.image import Texture
w = Window(visible=False)
t1 = t2 = Texture.load('examples/kitten.png')
glEnable(GL_TEXTURE_2D)
'''

print 'No repeated binding'
print Timer('''
glBindTexture(GL_TEXTURE_2D, t1.id)
glBegin(GL_LINES)
glVertex2f(0,0)
glVertex2f(0,0)
glEnd()
glBegin(GL_LINES)
glVertex2f(0,0)
glVertex2f(0,0)
glEnd()
''',
setup).repeat(number=NUMBER)

print 'Repeated binding'
print Timer('''
glBindTexture(GL_TEXTURE_2D, t1.id)
glBegin(GL_LINES)
glVertex2f(0,0)
glVertex2f(0,0)
glEnd()
glBindTexture(GL_TEXTURE_2D, t2.id)
glBegin(GL_LINES)
glVertex2f(0,0)
glVertex2f(0,0)
glEnd()
''',
setup).repeat(number=NUMBER)

print 'Bind to different tex'
print Timer('''
glBindTexture(GL_TEXTURE_2D, t1.id)
glBegin(GL_LINES)
glVertex2f(0,0)
glVertex2f(0,0)
glEnd()
glBindTexture(GL_TEXTURE_2D, t2.id)
glBegin(GL_LINES)
glVertex2f(0,0)
glVertex2f(0,0)
glEnd()
''',
setup).repeat(number=NUMBER)
