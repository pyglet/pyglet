import math

import ctypes

import pyglet.image

from pyglet.GL.VERSION_1_1 import *

class Glyph(object):
    def __init__(self, face, c, width, height, advance_x, baseline):
        self.face = face
        self.c = c
        self.width = width
        self.height = height
        self.advance_x = advance_x
        self.baseline = baseline

    def has_kerning(self):
        raise NotImplementedError

    def get_kerning_right(self, right):
        raise NotImplementedError

_default_character_set = 'acemnorsuvwxzfbdhikltgjpqy' \
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ' \
    '1234567890;:,.`!?@#$%^&+*=_-~()[]{}<>\\/"\' '

#_default_character_set = 'AB'

# XXX get from config
_max_texture_width = 1024

class Font(object):


    def __init__(self, file, size, character_set=_default_character_set):
        '''Create a renderable instance of the given font at the given
        size.

        :Parameters:
            `file` : str or file-type object
                File or filename of Truetype font.
            `size` : int
                Size in points of typeface.
            `character_set` : str
                String of characters that will be present in the font
                instance.

        '''
        self.character_set = character_set

        self.glyphs = {}

        self.face = self.load_font(file, size)

        glyphs = []
        h = 0
        w = 0
        for c in character_set:
            data, glyph = self.render_glyph(c)
            self.glyphs[c] = glyph
            h = max(h, glyph.height)
            w += glyph.width
            glyphs.append((data, glyph))

        #w += len(character_set) * _min_texture_character_space
        if w > _max_texture_width:
            h = (w / _max_texture_width + 1) * h
            w = _max_texture_width
        tw, th = pyglet.image._nearest_pow2(w), pyglet.image._nearest_pow2(h)

        # create the storage texture
        texdata = [chr(0)] * (tw*th*2)
        rects = []
        x = y = 0
        tw2 = tw * 2
        for data, glyph in glyphs:
            if x + glyph.width > tw:
                x = 0
                y += h

            # copy in the glyph
            gw2 = glyph.width * 2
            for row in xrange(glyph.height):
                tdx = x * 2 + row * tw2 + y * tw2
                dx = row * gw2
                texdata[tdx:tdx + gw2] = data[dx:dx + gw2]

            rects.append((x, y, glyph.width, glyph.height))
            x += glyph.width

        data = ''.join(texdata)
        self.texture = pyglet.image.TextureAtlas.from_data(data,
            tw, th, 2, rects=rects)

        for index, (data, glyph) in enumerate(glyphs):
            glyph.tex_info = (self.texture, index)

    def load_font(self, file, size):
        raise NotImplementedError

    def render_glyph(self, c):
        raise NotImplementedError

    def render(self, text):
        l = []
        for c in text:
            if c not in self.glyphs:
                raise NotImplementedError
#                data, glyph = self.render_glyph(c)
#                XXX store data in the texture
#                self.glyphs[c] = glyph
            l.append(self.glyphs[c])
        return Text(l)


class Text(object):
    def __init__(self, glyphs):
        self.glyphs = glyphs

        xpos = ypos = 0

        # create new display list with correct offsets
        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)
        kern_x = kern_y = 0
        self.width = 0
        self.ascent = self.descent = 0
        for i, this in enumerate(glyphs):
            if i > 0:
                last = glyphs[i-1]
                if last.face is not this.face:
                    kern_x = kern_y = 0
                elif this.has_kerning():
                    kern_x, kern_y = last.get_kerning_right(this)
                # translate
                glTranslatef(kern_x + last.advance_x, 0, 0)
                self.width += kern_x

            glPushMatrix()

            # Y position using baseline... and y kerning
            glTranslatef(0, -this.baseline + kern_y, 0)

            # call glyph display list
            texture, index = this.tex_info
            glCallList(texture.quad_lists[index])

            glPopMatrix()

            self.width += this.advance_x

            # keep track of the top and bottom to figure the height
            self.ascent = max(-this.baseline + this.height, self.ascent)
            self.descent = min(-this.baseline, self.descent)

        # now set the height
        self.height = self.ascent - self.descent

        glEndList()

    def draw(self):
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glCallList(self.gl_list)
        glPopAttrib()


"""

The original implementation - should be reinstated once we can get basic
freetype rendering going!

import pyglet.sprite

_min_texture_character_space = 2

class TextSprite(pyglet.sprite.Sprite):
    __slots__ = pyglet.sprite.Sprite.__slots__ + \
                ['vertices', 'n_vertices', 'texcoords']

    def __init__(self, font, text):
        self.texture = font.atlas.id
        self.position = (0, 0)
        self.anchor = 0, font.ascent
        self.rotation = 0.0
        self.scale = 1.0
        self.color = (1, 1, 1, 1)
        vertices = []
        texcoords = []
        x = 0
        y = 0
        for c in text:
            if c == '\n':
                y += font.line_height
                x = 0
                continue
            i = font.character_set.find(c)
            vert, tex = font.atlas.get_quad(0, i)
            vertices.append(x)
            vertices.append(y)
            vertices.append(vert[0] + x)
            vertices.append(y)
            vertices.append(vert[0] + x)
            vertices.append(vert[1] + y)
            vertices.append(x)
            vertices.append(vert[1] + y)
            texcoords.append(tex[0])
            texcoords.append(tex[1])
            texcoords.append(tex[2])
            texcoords.append(tex[1])
            texcoords.append(tex[2])
            texcoords.append(tex[3])
            texcoords.append(tex[0])
            texcoords.append(tex[3])
            x += font.advances[i]
        self.n_vertices = len(vertices) / 2
        self.vertices = std_array('f', vertices).tostring()
        self.texcoords = std_array('f', texcoords).tostring()

    def draw(self):
        glPushMatrix()
        glPushAttrib(GL_CURRENT_BIT)

        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glColor4fv(self.color)
        glTranslate(self.position[0], self.position[1], 0)
        glRotate(self.rotation, 0, 0, -1)
        glScale(self.scale, self.scale, 1)
        glTranslate(-self.anchor[0], -self.anchor[1], 0)

        # Don't push/pop client state, it leaks memory (the arrays?) badly
        glVertexPointer(2, GL_FLOAT, 0, self.vertices)
        glTexCoordPointer(2, GL_FLOAT, 0, self.texcoords)
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_TEXTURE_COORD_ARRAY)
        glDrawArrays(GL_QUADS, 0, self.n_vertices)
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_TEXTURE_COORD_ARRAY)

        glPopAttrib()
        glPopMatrix()
"""
