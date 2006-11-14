'''Text rendering comes in two flavours:

1. ask a Font to render some text straight, no fancy stuff
2. ask this module to render some marked-up text that has a base font
'''

import math
import re
import os

import ctypes

import pyglet.image
import pyglet.sprite
from pyglet.text import ttf

from pyglet.GL.VERSION_1_1 import *


class BaseFontFactory:
    """Abstract base class for collection of fonts.

    A font factory constructs fonts from some resource.  The only
    user-accessible method is get_font, used to construct a font.
    Subclasses must override the `impl_get_font` method.  See
    `LocalFontFactory` for a concrete example.

    This class provides a font cache to avoid reloading a font
    of a given size and style.
    """
    def __init__(self, allow_fake_bold=True, allow_fake_italic=True):
        """Construct the cache for a font factory.

        :Parameters:
            `allow_fake_bold`
                Whether to allow Pygame's "fake" bold when a suitable font
                cannot be found.  If this is False and a bold font is
                requested that cannot be found, an exception is raised.
                Defaults to True.
            `allow_fake_italic`
                The same as `allow_fake_bold`, but for fake italic.
        """

        self._cache = {}
        self.allow_fake_bold = allow_fake_bold
        self.allow_fake_italic = allow_fake_italic

    def get_font(self, family, size, bold=False, italic=False):
        """Create a font with the given characteristics.

        :Parameters:
            `family`
                The font's family name, e.g. "times new roman".  This is
                case insensitive.  Required.
            `size`
                Size of the font, in points (e.g., 12 is a standard readable
                size for paragraph text).  Required.
            `bold`, `italic`
                Boolean bold and italic characteristics.  Default to False.

        If successful, a `FontInstance` instance is returned.  If the
        requested font cannot be created, an exception is raised.
        """
        try:
            return self._cache[(family, size, bold, italic)]
        except KeyError:
            pass
        font = self.impl_get_font(family, size, bold, italic)
        self._cache[(family, size, bold, italic)] = font
        return font

    def impl_get_font(self, family, size, bold, italic):
        """Subclasses should override just this method.

        Implementations of this method should follow the contract
        specified in `get_font`.
        """
        raise NotImplementedError()

    def load_font(self, filename, size, metrics):
        """Subclasses should override just this method.

        XXX document

        Return a Font implementation instance.
        """
        raise NotImplementedError()

class LocalFontFactory(BaseFontFactory):
    """Font factory for a collection of font files loaded from disk.
   
    Typical applications will distribute Truetype font files alongside
    the executable or source code.  In this case, use this font factory
    and instantiate it with either a list of files or directories::
       
        fonts = LocalFontFactory('./fonts')

    or::

        fonts = LocalFontFactory(['times.ttf', 'arial.ttf'])

    Additional fonts can be searched later with the `add` method.
    """
    def __init__(self, path=None, **kwargs):
        """Construct a font factory for a set of font files.

        :Parameters:
            `path`
                A file, directory, or list of files or directories to
                search for fonts.  Only files with the extension ``.ttf``
                will be read, unless named explicitly.
            ``allow_fake_bold``
                See `BaseFontFactory.__init__`
            ``allow_fake_italic``
                See `BaseFontFactory.__init__`
        """
        BaseFontFactory.__init__(self, **kwargs)
        self._fonts = {}
        if path:
            self.add(path)

    def add(self, path):
        """Add a path or list of paths to search.

        A path can be either a truetype file or a directory containing
        truetype files.  Directories are not searched recursively."""
        if type(path) == list:
            for p in path:
                self.add(p)
        elif os.path.isdir(path):
            for file in os.listdir(path):
                if os.path.splitext(file)[1].lower() == '.ttf':
                    self.add(os.path.join(path, file))
        else:
            info = ttf.TruetypeInfo(path)
            metrics = FontMetrics(info)
            self._fonts[(info.get_name('family').lower(),
                         info.is_bold(),
                         info.is_italic())] = (path, metrics)
            info.close()
       
    def impl_get_font(self, family, size, bold, italic):
        attempts = [(bold, italic)]
        if bold and self.allow_fake_bold:
            attempts.append((False, italic))
        if italic and self.allow_fake_italic:
            attempts.append((bold, False))
        if len(attempts) >= 3:
            attempts.append((False, False))

        filename = None
        for b, i in attempts:
            try:
                # XXX try partial matching on name if no exact match
                filename, metrics = self._fonts[(family.lower(), b, i)]
                if filename:
                    break
            except:
                pass
        if not filename:
            raise Exception, 'Font \"%s\" (bold=%s,italic=%s) not found' % \
                (family, bold, italic)
        fake_bold = bold and not b
        fake_italic = italic and not i

        font = self.load_font(filename, size, metrics)
        if fake_bold:
            font = FakeBold(font)
        if fake_italic:
            return FakeItalic(font)
        return font

class FakeBold(object):
    def __init__(self, font):
        self.__font = font
 
    def __getattr__(self, attr):
        return getattr(self.__font, attr)

    def get_boxes(self, text):
        boxes, advance = self.__font.get_boxes(text)
        # XXX why can't I increase the advance here?
        return boxes, advance + 5

    def draw_boxes(self, boxes):
        self.__font.draw_boxes(boxes)
        glPushMatrix()
        glTranslatef(1, 0, 0)
        self.__font.draw_boxes(boxes)
        glPopMatrix()

sixteen = ctypes.c_float * 16

class FakeItalic(object):
    def __init__(self, font):
        self.__font = font
 
    def __getattr__(self, attr):
        return getattr(self.__font, attr)

    def draw_boxes(self, boxes):
        glPushMatrix()
        matrix = sixteen(*[0]*16)
        matrix[0] = 1
        matrix[4] = .3      # XXX good value?
        matrix[12] = 15     # XXX fix this
        matrix[5] = 1
        matrix[10] = 1
        matrix[15] = 1
        glMultMatrixf(matrix)
        self.__font.draw_boxes(boxes)
        glPopMatrix()

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

class FontMetrics:
    """Size-independent metrics for a truetype font.
   
    We avoid using TruetypeInfo directly since:
        * it would need to keep the mmap, which is ugly, and
        * maybe we'll support Postscript or bitmap fonts in the future.
    """
    def __init__(self, info=None):
        """Construct a new instance with the given Truetype information

        :Parameters:
            `info` : TruetypeInfo
                TruetypeInfo instance to get metrics from
        """
        self.advances = {}
        self.kerns = {}
        if info:
            try:
                self.kerns = info.get_character_kernings()
            except:
                pass
            try:
                self.advances = info.get_character_advances()
            except:
                pass

class Font(object):
    def __init__(self, file, size, metrics, do_kerning=True,
            character_set=_default_character_set):
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
        self.size = size
        self.metrics = metrics
        self.do_kerning = do_kerning
        self.character_set = character_set

        # Premultiply font metrics for this size
        self.advances = {}
        self.kerns = {}
        for ch in metrics.advances:
            self.advances[ch] = int(self.size * metrics.advances[ch])
        for pair in metrics.kerns:
            self.kerns[pair] = int(self.size * metrics.kerns[pair])

        self.glyphs = {}

        self.face = self.load_font(file, size, metrics)

        glyphs = []
        max_height = 0
        for c in character_set:
            data, glyph = self.render_glyph(c)
            self.glyphs[c] = glyph
            max_height = max(max_height, glyph.height)
            glyphs.append((data, glyph))

        # try to lay the glyphs out in a square
        location = {}
        rows = [0]
        for data, glyph in glyphs:
            min_length = None
            for i, length in enumerate(rows):
                if min_length is None or length < min_length:
                    min_length = length
                    rownum = i
            location[glyph.c] = (min_length, rownum * max_height)
            rows[rownum] += glyph.width
            if rows[rownum] > len(rows) * max_height:
                rows.append(0)

        if rows[-1] == 0: rows.pop()

        # create the storage texture
        tw = max(rows)
        th = len(rows) * max_height
        texdata = [chr(0)] * (tw*th*2)

        rects = []
        tw2 = tw * 2
        self.ascent = self.descent = 0
        for data, glyph in glyphs:
            x, y = location[glyph.c]

            # copy in the glyph
            gw2 = glyph.width * 2
            for row in xrange(glyph.height):
                tdx = x * 2 + row * tw2 + y * tw2
                dx = row * gw2
                texdata[tdx:tdx + gw2] = data[dx:dx + gw2]

            rects.append((x, y, glyph.width, glyph.height))

            self.ascent = max(-glyph.baseline + glyph.height, self.ascent)
            self.descent = min(-glyph.baseline, self.descent)

        self.glyph_height = self.ascent - self.descent

        data = ''.join(texdata)
        self.texture = pyglet.image.TextureAtlasRects.from_data(data,
            tw, th, GL_LUMINANCE_ALPHA, GL_UNSIGNED_BYTE, rects=rects)

        for index, (data, glyph) in enumerate(glyphs):
            glyph.texture = self.texture.get_texture(index)

    def load_font(self, file, size):
        raise NotImplementedError

    def render_glyph(self, c):
        raise NotImplementedError

    def render(self, text):
        '''Render the given text.
        '''
        l = []
        for c in text:
            if c not in self.glyphs:
                # TODO pack these into another larger texture?
                # XXX using a single texture would allow us to use vert
                # XXX arrays etc. but might be prohbitive for large
                # XXX font sizes
                data, glyph = self.render_glyph(c)
                self.glyphs[c] = glyph
                glyph.texture = pyglet.image.Texture.from_data(data,
                    glyph.width, glyph.height, GL_LUMINANCE_ALPHA,
                    GL_UNSIGNED_BYTE)
            l.append(self.glyphs[c])
        l = addHorizontalKerning(l)
        return Text(l)

    def get_boxes(self, text):
        """Compute the boxes for a given string.

        :Parameters:
            `text` : str
                Text to be rendered

        Pairwise kerning will be applied, if enabled.  Nothing is rendered;
        this is a precompute step.  The return value is a tuple::

            glr, total_advance

        where boxes is a list of tuples of the form::
           
            (renderbox, glyph)

        where ``renderbox`` and ``texbox`` are 4-element tuples representing
        the render-space and texture-space rectangles for a glyph.  No
        guarantee is made about the order or number of boxes returned
        (for example, in the future, automatic ligaturing may take place).

        Generally a user application can simply pass ``boxes`` to
        `draw_boxes`.
        """
        if not self.do_kerning:
            kerned_text = \
                [(self.glyphs[c], 0) for c in text]
        else:
            kerned_text = []
            for i in range(len(text)-1):
                c = text[i]
                pair = (c, text[i+1])
                kerned_text.append((self.glyphs[c], self.kerns.get(pair, 0)))
            c = text[-1]
            kerned_text.append((self.glyphs[c], 0))
        boxes = []
        total_advance = 0
        x, y = 0, self.descent
        for glyph, kern in kerned_text:
            advance = glyph.advance_x + kern
            renderbox = (x, y - glyph.baseline,
                x + glyph.width, y + glyph.height - glyph.baseline)
            boxes.append((renderbox, glyph))
            total_advance += advance
            x += advance
        return boxes, total_advance

    def draw_boxes(self, boxes):
        """Draw a set of precalculated glyph boxes at the origin.

        :Parameters:
            `boxes`
                A list of (renderbox,texbox) tuples; see `get_boxes`.

        The text will be rendered at pixel-size at the origin.  Use
        ``glTranslate`` to draw the text at a different position.
        Make sure you have an orthagonal projection set up if you want
        the text to be displayed at the optimal resolution.  This
        method assumes texturing and alpha-blending is already enabled
        (see `begin` and `end`).
        """
        # XXX sort by actual texture
        glBindTexture(GL_TEXTURE_2D, boxes[0][1].texture.texture.id)
        glBegin(GL_QUADS)
        for renderbox, glyph in boxes:
            texbox = glyph.texture.uv
            glTexCoord2f(texbox[0], texbox[1])
            glVertex2f(renderbox[0], renderbox[1])
            glTexCoord2f(texbox[2], texbox[1])
            glVertex2f(renderbox[2], renderbox[1])
            glTexCoord2f(texbox[2], texbox[3])
            glVertex2f(renderbox[2], renderbox[3])
            glTexCoord2f(texbox[0], texbox[3])
            glVertex2f(renderbox[0], renderbox[3])
        glEnd()

def addHorizontalKerning(glyphs):
    result = []
    last = None
    for this in glyphs:
        result.append(this)
        if last is not None and last.face is this.face and this.has_kerning():
            result.append((last.get_kerning_right(this), this))
        else:
            result.append((0, this))
        last = this
    return result

_default = []
class Text(pyglet.sprite.Sprite):
    def __init__(self, text, line_spacing=_default):
        self.text = text

        self.position = (0., 0.)
        self.rotation = 0.0
        self.scale = 1.
        #self.color = (1., 1., 1., 1.)

        xpos = ypos = 0

        # create new display list with correct offsets
        self.gl_list = glGenLists(1)
        glNewList(self.gl_list, GL_COMPILE)
        kern_x = kern_y = 0
        self.width = 0
        self.ascent = self.descent = 0
        last_height = 0
        for j, glyphs in enumerate(text):
            height = 0
            width = 0
            glPushMatrix()
            for kern_x, this in enumerate(glyphs):
                if kern_x:
                    glTranslatef(kern_x, 0, 0)

                glPushMatrix()

                # Y position using baseline... 
                glTranslatef(0, -this.baseline, 0)

                # call glyph display list
                glCallList(this.texture.quad_list)

                glPopMatrix()

                glTranslatef(this.advance_x, 0, 0)

                width += (kern_x + this.advance_x)
                height = max(height, this.height)

                # keep track of the top and bottom to figure the height
                self.ascent = max(-this.baseline + this.height, self.ascent)
                self.descent = min(-this.baseline, self.descent)

            glPopMatrix()

            self.width = max(width, self.width)

        # now set the height
        self.height = self.ascent - self.descent

        # TODO default anchor on the top? really?
        self.anchor = 0, self.ascent

        glEndList()

    def set_anchor(self, vertical, horizontal):
        x = {
            'left': 0,
            'center': self.width/2,
            'right': self.width,
        }[horizontal]
        y = {
            'top': self.ascent,
            'baseline': 0,
            'bottom': self.descent,
        }[vertical]
        self.anchor = x, y

    def draw(self):
        glPushAttrib(GL_ENABLE_BIT)

        glEnable(GL_BLEND)
        glEnable(GL_TEXTURE_2D)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        glColor4f(*self.color)

        glPushMatrix()
        glTranslatef(self.position[0], self.position[1], 0)
        glRotatef(self.rotation, 0, 0, 1)
        glScalef(self.scale, self.scale, 1)
        glTranslatef(-self.anchor[0], -self.anchor[1], 0)

        glCallList(self.gl_list)
        glPopMatrix()

        glPopAttrib()

