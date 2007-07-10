
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
            halign='left', width=None):
        if font_size is None: font_size = self.font_size
        f = self.getFont(size=font_size)
        return font.Text(f, text, color=color, halign=halign, width=width,
            valign=font.Text.BOTTOM)

    def textAsTexture(self, text, color=(0, 0, 0, 1), bgcolor=(1, 1, 1, 0),
            font_size=None, halign='left', width=None):
        label = self.text(text, color=color, font_size=font_size,
            halign=halign, width=width)
        w = int(label.width)
        h = int(label.height)
        x = c_int()
        def _f():
            glPushAttrib(GL_COLOR_BUFFER_BIT|GL_ENABLE_BIT|GL_CURRENT_BIT)
            glEnable(GL_TEXTURE_2D)
            glDisable(GL_DEPTH_TEST)
            glClearColor(*bgcolor)
            glClear(GL_COLOR_BUFFER_BIT)
            label.draw()
            glPopAttrib()
        return util.renderToTexture(w, h, _f)

    stylesheet = '''
body {margin: 0px; background-color: white; font-family: sans-serif;}
div.frame {border: 1px solid #555; background-color: white;}
h1 {font-size: %(font_size)spx; color: black; margin: 2px;}
p {font-size: %(font_size)spx; color: #444; margin: 2px;}
.button {font-size: %(font_size)spx; border: 1px solid black; padding: 2px; margin: 0px;}
'''%locals()

    def renderXHTML(self, text, width=None, height=None):
        label = Layout()
        label.set_xhtml('''<?xml version="1.0"?><html><head><style>%s</style></head><body>%s</body></html>'''%(self.stylesheet, text))

        label.viewport_x = 0
        label.viewport_y = 0
        label.viewport_width = width or 256
        label.viewport_height = height or 200
        h = int(label.view.canvas_height)
        w = int(label.view.canvas_width)
        label.viewport_width = w
        label.viewport_height = h
        def _f():
            glPushAttrib(GL_CURRENT_BIT|GL_COLOR_BUFFER_BIT|GL_ENABLE_BIT)
            glEnable(GL_TEXTURE_2D)
            glDisable(GL_DEPTH_TEST)
            glClearColor(1, 1, 1, 0)
            glClear(GL_COLOR_BUFFER_BIT)
            glPushMatrix()
            glLoadIdentity()
            glTranslatef(0, h, 0)
            label.view.draw()
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

