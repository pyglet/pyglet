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

import sys
import os

if sys.platform == 'win32':
    raise NotImplemented('No font implementation')
elif sys.platform == 'darwin':
    from pyglet.text import freetype2
    LocalFontFactory = freetype2.FreetypeLocalFontFactory
    Font = freetype2.FreetypeFont
    #raise NotImplemented('No font implementation')
else:
    from pyglet.text import freetype2
    LocalFontFactory = freetype2.FreetypeLocalFontFactory
    Font = freetype2.FreetypeFont

from pyglet.GL.VERSION_1_1 import *

from pyglet.text import html, layout

Align = layout.Align

_path = os.path.join(os.path.split(__file__)[0], 'data')
_default_font_factory = LocalFontFactory(_path)

def layout_html(text, width=-1, font_factory=None):
    """Layout HTML markup ready for drawing in OpenGL.

    :Parameters:
        `text` : str
            HTML markup text to render
        `width` : int
            Width, in pixels, at which to wrap lines.  Defaults to not
            wrapping.
        `font_factory` : pyglyph.text.FontFactory
            Font factory to use for instantiating fonts.  If unspecified,
            search the current directory for Truetype files.
    """
    if not font_factory:
        font_factory = _default_font_factory
    runs = html.parse(text, font_factory)
    text = layout.OpenGLTextLayout(width)
    text.layout(runs)
    return text

_default_font = None
def layout_text(text, width=-1, font=None, color=(0,0,0,1)):
    """Layout plain text ready for drawing in OpenGL.

    :Parameters:
        `text` : str
            Text string to render
        `width` : int
            Width, in pixels, at which to wrap lines.  Defaults to not
            wrapping.
        `font` : pyglyph.text.Font
            FontInstance to render the text with.  If unspecified,
            the default font is used at size 16pt.
        `color` : tuple of size 3 or 4
            Color to render the text in (passed to glColor).
    """
    if not font:
        global _default_font
        if not _default_font:
            _default_font = _default_font_factory.get_font(
                'bitstream vera sans', 16)
        font = _default_font
    style = layout.Style(font, color)
    run = layout.StyledRun(text, style)
    text = layout.OpenGLTextLayout(width)
    text.layout([run])
    return text


def begin():
    """Push a text-rendering mode onto the OpenGL stack.

    This sets up the rendering context so it's ready for text rendering.
    Specifically, it enables texturing, alpha-blending and texture
    modulation.  The changes are pushed onto the attribute stack and
    the previous state can be recalled by calling `end`.

    Typical usage is::

        begin()
        draw_text('Hello')
        end()

    Since state changes in OpenGL are relatively expensive, you should
    group all text drawing calls into a single begin/end block each
    frame.  If your drawing context has texturing and alpha blending
    enabled and setup in the usual way anyway, there is no need to
    call this function.
    """
    glPushAttrib(GL_ENABLE_BIT | GL_TEXTURE_BIT)
    glEnable(GL_TEXTURE_2D)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE)

def end():
    """Pop the text-rendering mode off the OpenGL stack.

    See `begin` for details.
    """
    glPopAttrib()


