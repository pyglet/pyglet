import ctypes

from pyglet.GL.VERSION_1_1 import *


class Glyph(object):
    def __init__(self, face, c, texture, advance_x, baseline):
        self.face = face
        self.c = c
        # XXX pack into a big texture?
        self.texture = texture
        self.advance_x = advance_x
        self.baseline = baseline

    def has_kerning(self):
        raise NotImplementedError

    def get_kerning_right(self, right):
        raise NotImplementedError

class Font(object):
    def __init__(self, face):
        self.glyphs = {}
        self.face = face

    @classmethod
    def load_font(cls, filename, size):
        raise NotImplementedError

    def render_glyph(self, c):
        raise NotImplementedError

    def render(self, text):
        l = []
        for c in text:
            if c not in self.glyphs:
                self.glyphs[c] = self.render_glyph(c)
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
            glCallList(this.texture.quad_list)

            glPopMatrix()

            self.width += this.advance_x

            # keep track of the top and bottom to figure the height
            self.ascent = max(-this.baseline + this.texture.height, self.ascent)
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


import pyglet.image
import pyglet.sprite

_default_character_set = 'abcdefghijklmnopqrstuvwxyz' \
                         'ABCDEFGHIJKLMNOPQRSTUVWXYZ' \
                         '1234567890;:,.`!?@#$%^&+*=_-~()[]{}<>\\/"\' '

_max_texture_width = 1024
_min_texture_character_space = 2

class Font(object):
    __slots__ = ['atlas', 'character_set', 'advances', 
                 'ascent', 'descent', 'line_height']

    def __init__(self, file, size, character_set=None):
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
        if not character_set:
            character_set = _default_character_set
        self.character_set = character_set

        if not hasattr(file, 'read'):
            file = open(file, 'r')

        # Load with SDL_ttf
        if not TTF_WasInit():
            TTF_Init()
        rw = SDL_RWFromObject(file)
        font = TTF_OpenFontRW(rw, 0, size)
        self.ascent = TTF_FontAscent(font)
        self.descent = TTF_FontDescent(font)
        self.line_height = TTF_FontHeight(font)

        # Determine required size of texture
        w, h = TTF_SizeText(font, character_set)
        w += len(character_set) * _min_texture_character_space
        if w > _max_texture_width:
            h = (w / _max_texture_width + 1) * h
            w = _max_texture_width
        w, h = pyglet.image._nearest_pow2(w), pyglet.image._nearest_pow2(h)

        # Create new surface to draw to
        surface = SDL_CreateRGBSurface(0, w, h, 32, 
                                       SDL_SwapLE32(0x000000ff),
                                       SDL_SwapLE32(0x0000ff00),
                                       SDL_SwapLE32(0x00ff0000),
                                       SDL_SwapLE32(0xff000000))

        # Draw each glyph into surface, record advances
        rects = []
        self.advances = []
        x, y = 0, 0
        colour = SDL_Color(255, 255, 255)
        for i, c in enumerate(character_set):
            glyph = TTF_RenderText_Blended(font, c, colour)
            glyph.flags &= ~SDL_SRCALPHA
            cw, ch = glyph.w, glyph.h
            if x + cw >= w:
                x = 0
                y += self.line_height
            dstrect = SDL_Rect(x, y , cw, ch)
            SDL_BlitSurface(glyph, None, surface, dstrect)
            SDL_FreeSurface(glyph)

            rects.append((x, y, cw, ch))
            self.advances.append(TTF_GlyphMetrics(font, c)[4])
            x += cw + _min_texture_character_space

        self.atlas = pyglet.image.TextureAtlas(surface, rects=rects)
        SDL_FreeSurface(surface)
        TTF_CloseFont(font)

    def draw(self, text):
        glPushMatrix()
        glTranslate(0, -self.ascent, 0)
        x = 0
        for c in text:
            if c == '\n':
                glTranslate(-x, -self.line_height, 0)
                x = 0
                continue
            i = self.character_set.find(c)
            self.atlas.draw(0, i)
            glTranslate(self.advances[i], 0, 0)
            x += self.advances[i]
        glPopMatrix()

    def create_sprite(self, text):
        return TextSprite(self, text)

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
