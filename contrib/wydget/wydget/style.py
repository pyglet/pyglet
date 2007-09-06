
from pyglet.gl import *
from pyglet import font
from layout import *

import util

class Style(object):

    font_name = ''
    font_size = 14

    def getFont(self, name=None, size=None):
        if name is None: name = self.font_name
        if size is None: size = self.font_size
        return font.load(name, size)

    def getGlyphString(self, text, name=None, size=None):
        glyphs = self.getFont(name=name, size=size).get_glyphs(text)
        return font.GlyphString(text, glyphs)

    def text(self, text, color=(0, 0, 0, 1), font_size=None,
            font_name=None, halign='left', width=None,
            valign=font.Text.BOTTOM):
        if font_size is None: font_size = self.font_size
        if font_name is None: font_name = self.font_name
        f = self.getFont(name=font_name, size=font_size)
        return font.Text(f, text, color=color, halign=halign, width=width,
            valign=valign)

    def textAsTexture(self, text, color=(0, 0, 0, 1), bgcolor=(1, 1, 1, 0),
            font_size=None, font_name=None, halign='left', width=None,
            rotate=0):
        label = self.text(text, color=color, font_size=font_size,
            font_name=font_name, halign=halign, width=width, valign='top')
        label.width
        w = int(width or label.width)
        h = font_size * len(label.lines) #int(label.height)
        x = c_int()
        def _f():
            glPushAttrib(GL_COLOR_BUFFER_BIT|GL_ENABLE_BIT|GL_CURRENT_BIT)
            glEnable(GL_TEXTURE_2D)
            glDisable(GL_DEPTH_TEST)
            glClearColor(*bgcolor)
            glClear(GL_COLOR_BUFFER_BIT)
            glPushMatrix()
            if rotate == 0:
                glTranslatef(0, h, 0)
            if rotate:
                glRotatef(rotate, 0, 0, 1)
            if rotate == 270:
                glTranslatef(-w, h, 0)
            if rotate == 180:
                glTranslatef(-w, 0, 0)
            # prevent the text's alpha channel being written into the new
            # texture
            glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_FALSE)
            label.draw()
            glPopMatrix()
            glPopAttrib()
        if rotate in (0, 180):
            return util.renderToTexture(w, h, _f)
        else:
            return util.renderToTexture(h, w, _f)

    stylesheet = '''
body {margin: 0px; background-color: white; font-family: sans-serif;}
div.frame {border: 1px solid #555; background-color: white;}
h1 {font-size: %(font_size)spx; color: black; margin: 2px;}
p {font-size: %(font_size)spx; color: #444; margin: 2px;}
.button {font-size: %(font_size)spx; border: 1px solid black; padding: 2px; margin: 0px;}
a {color: blue;}
'''%locals()

    def xhtml(self, text, width=None, height=None, style=None):
        layout = Layout()
        if style is None:
            style = self.stylesheet
        layout.set_xhtml('''<?xml version="1.0"?>
            <html><head><style>%s</style></head>
            <body>%s</body></html>'''%(style, text))
        layout.viewport_x = 0
        layout.viewport_y = 0
        layout.viewport_width = width or 256
        layout.viewport_height = height or 200
        h = int(layout.view.canvas_height)
        w = int(layout.view.canvas_width)
        layout.viewport_width = w
        layout.viewport_height = h
        return layout

    def xhtmlAsTexture(self, text, width=None, height=None, style=None):
        return xhtmlAsTexture(self.xhtml(text, width, height, style))

def xhtmlAsTexture(layout):
    h = int(layout.view.canvas_height)
    w = int(layout.view.canvas_width)
    def _f():
        glPushAttrib(GL_CURRENT_BIT|GL_COLOR_BUFFER_BIT|GL_ENABLE_BIT)
        # always draw onto solid white
        glClearColor(1, 1, 1, 1)
        glClear(GL_COLOR_BUFFER_BIT)
        glPushMatrix()
        glLoadIdentity()
        glTranslatef(0, h, 0)
        # ... and blend with solid white
        glColor4f(1, 1, 1, 1)
        layout.view.draw()
        glPopMatrix()
        glPopAttrib()
    return util.renderToTexture(w, h, _f)

class Gradient(object):
    def __init__(self, *corners):
        '''Corner colours in order bottomleft, topleft, topright,
        bottomright.
        '''
        self.corners = corners

    def __call__(self, rect, clipped):
        scissor = clipped != rect
        if scissor:
            glPushAttrib(GL_ENABLE_BIT|GL_SCISSOR_BIT)
            glEnable(GL_SCISSOR_TEST)
            glScissor(*map(int, (clipped.x, clipped.y, clipped.width,
                clipped.height)))

        glBegin(GL_QUADS)
        glColor4f(*self.corners[0])
        glVertex2f(*rect.bottomleft)

        glColor4f(*self.corners[1])
        glVertex2f(*rect.topleft)

        glColor4f(*self.corners[2])
        glVertex2f(*rect.topright)

        glColor4f(*self.corners[3])
        glVertex2f(*rect.bottomright)

        glEnd()

        if scissor:
            glPopAttrib()

