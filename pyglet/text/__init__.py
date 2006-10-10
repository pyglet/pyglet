#!/usr/bin/env python

'''

Some thoughts from Alex:

A font should be allowed to spread over more than one texture.. e.g a 
large size with lots of glyphs could go over 4096x4096.

Before rendering a string, it should be searched for characters that 
haven't been texturized yet, and bundle them into a new texture (yeah, 
latin-1 should be done be default when you create a font).  This is 
better than making the programmer do it manually, because who knows what 
a user is going to type.

No bidi support needs to be in from the start, but keep in mind it will 
be eventually, so don't make it too left-to-rightist.

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'


from pyglet.text.freetype2 import FreetypeFont as Font

