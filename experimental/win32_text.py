from ctypes import *

from pyglet.GL.VERSION_1_1 import *
from pyglet.image import *
from pyglet.window import *
from pyglet.window.event import *
from pyglet.window.win32.constants import *
from pyglet.window.win32.types import *
from pyglet.window.win32 import _gdi32 as gdi32, _user32 as user32
from pyglet.window.win32 import _kernel32 as kernel32
from pyglet.window.win32 import _check

HFONT = HANDLE
HBITMAP = HANDLE
HDC = HANDLE
HGDIOBJ = HANDLE
gdi32.CreateFontIndirectA.restype = HFONT
gdi32.CreateCompatibleBitmap.restype = HBITMAP
gdi32.CreateCompatibleDC.restype = HDC
user32.GetDC.restype = HDC
gdi32.GetStockObject.restype = HGDIOBJ
gdi32.CreateDIBSection.restype = HBITMAP

class LOGFONT(Structure):
    _fields_ = [
        ('lfHeight', c_long),
        ('lfWidth', c_long),
        ('lfEscapement', c_long),
        ('lfOrientation', c_long),
        ('lfWeight', c_long),
        ('lfItalic', c_byte),
        ('lfUnderline', c_byte),
        ('lfStrikeOut', c_byte),
        ('lfCharSet', c_byte),
        ('lfOutPrecision', c_byte),
        ('lfClipPrecision', c_byte),
        ('lfQuality', c_byte),
        ('lfPitchAndFamily', c_byte),
        ('lfFaceName', (c_char * LF_FACESIZE))  # Use ASCII
    ]
    __slots__ = [f[0] for f in _fields_]

class TEXTMETRIC(Structure):
    _fields_ = [
        ('tmHeight', c_long),
        ('tmAscent', c_long),
        ('tmDescent', c_long),
        ('tmInternalLeading', c_long),
        ('tmExternalLeading', c_long),
        ('tmAveCharWidth', c_long),
        ('tmMaxCharWidth', c_long),
        ('tmWeight', c_long),
        ('tmOverhang', c_long),
        ('tmDigitizedAspectX', c_long),
        ('tmDigitizedAspectY', c_long),
        ('tmFirstChar', c_char),  # Use ASCII 
        ('tmLastChar', c_char),
        ('tmDefaultChar', c_char),
        ('tmBreakChar', c_char),
        ('tmItalic', c_byte),
        ('tmUnderlined', c_byte),
        ('tmStruckOut', c_byte),
        ('tmPitchAndFamily', c_byte),
        ('tmCharSet', c_byte)
    ]
    __slots__ = [f[0] for f in _fields_]

class ABC(Structure):
    _fields_ = [
        ('abcA', c_int),
        ('abcB', c_uint),
        ('abcC', c_int)
    ]
    __slots__ = [f[0] for f in _fields_]

class BITMAPINFOHEADER(Structure):
    _fields_ = [
        ('biSize', c_uint32),
        ('biWidth', c_int),
        ('biHeight', c_int),
        ('biPlanes', c_short),
        ('biBitCount', c_short),
        ('biCompression', c_uint32),
        ('biSizeImage', c_uint32),
        ('biXPelsPerMeter', c_long),
        ('biYPelsPerMeter', c_long),
        ('biClrUser', c_uint32),
        ('biClrImportant', c_uint32)
    ]
    __slots__ = [f[0] for f in _fields_]

class RGBQUAD(Structure):
    _fields_ = [
        ('rgbBlue', c_byte),
        ('rgbGreen', c_byte),
        ('rgbRed', c_byte),
        ('rgbReserved', c_byte)
    ]

class BITMAPINFO(Structure):
    _fields_ = [
        ('bmiHeader', BITMAPINFOHEADER),
        ('bmiColors', RGBQUAD * 1)
    ]

def str_ucs2(text):
    if byteorder == 'big':
        text = text.encode('utf_16_be')
    else:
        text = text.encode('utf_16_le')   # explicit endian avoids BOM
    return create_string_buffer(text + '\0')

# XXX NewTextureAtlas to become AllocatingTextureAtlas(TextureAtlas)
#     NewTextureSubImage to become TextureSubImage.

class NewTextureAtlasOutOfSpaceException(ImageException):
    pass

class NewTextureSubImage(object):
    def __init__(self, texture, x, y, width, height):
        self.texture_id = texture.id
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.tex_coords = (
            float(x) / texture.width,
            float(y) / texture.height,
            float(x + width) / texture.width,
            float(y + height) / texture.height)

    def flip_vertical(self):
        self.tex_coords = (
            self.tex_coords[0], 
            self.tex_coords[3], 
            self.tex_coords[2],
            self.tex_coords[1])

class NewTextureAtlas(Texture):
    x = 0
    y = 0
    line_height = 0
    subimage_class = NewTextureSubImage

    def allocate(self, width, height):
        '''Returns (x, y) position for a new glyph, and reserves that
        space.'''
        if self.x + width > self.width:
            self.x = 0
            self.y += self.line_height
            self.line_height = 0
        if self.y + height > self.height:
            raise NewTextureAtlasOutOfSpaceException()

        self.line_height = max(self.line_height, height)
        x = self.x
        self.x += width
        return self.subimage_class(self, x, self.y, width, height)

class Glyph(NewTextureSubImage):
    advance = 0
    vertices = (0, 0, 0, 0)

    def set_bearings(self, baseline, left_side_bearing, advance):
        self.advance = advance
        self.vertices = (
            left_side_bearing,
            -baseline,
            left_side_bearing + self.width,
            -baseline + self.height)

    def draw(self):
        '''Debug method: use the higher level APIs for performance and
        kerning.'''
        glBindTexture(GL_TEXTURE_2D, self.texture_id)
        glBegin(GL_QUADS)
        glTexCoord2f(self.tex_coords[0], self.tex_coords[1])
        glVertex2f(self.vertices[0], self.vertices[1])
        glTexCoord2f(self.tex_coords[2], self.tex_coords[1])
        glVertex2f(self.vertices[2], self.vertices[1])
        glTexCoord2f(self.tex_coords[2], self.tex_coords[3])
        glVertex2f(self.vertices[2], self.vertices[3])
        glTexCoord2f(self.tex_coords[0], self.tex_coords[3])
        glVertex2f(self.vertices[0], self.vertices[3])
        glEnd()

    def get_kerning_pair(self, right_glyph):
        return 0

class GlyphTextureAtlas(NewTextureAtlas):
    subimage_class = Glyph

class StyledText(object):
    '''One contiguous sequence of characters sharing the same
    GL state.'''
    # TODO Not there yet: must be split on texture atlas changes.
    def __init__(self, text, font):
        self.text = text
        self.font = font
        self.glyphs = font.get_glyphs(text)

class TextLayout(object):
    '''Will eventually handle all complex layout, line breaking,
    justification and state sorting/coalescing.'''
    def __init__(self, styled_texts):
        self.styled_texts = styled_texts

    def draw(self):
        glPushMatrix()
        for styled_text in self.styled_texts:
            styled_text.font.apply_blend_state()
            for glyph in styled_text.glyphs:
                glyph.draw()
                glTranslatef(glyph.advance, 0, 0)
        glPopMatrix()

class Font(object):
    texture_width = 256
    texture_height = 256

    # TODO: a __new__ method to instantiate correct Font for platform

    def __init__(self):
        self.textures = []
        self.glyphs = {}

    # TODO: static add_font(file) and add_font_directory(dir) methods.

    def create_glyph_texture(self):
        texture = GlyphTextureAtlas.create(
            self.texture_width,
            self.texture_height,
            GL_LUMINANCE_ALPHA)
        return texture

    def apply_blend_state(self):
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)

    def allocate_glyph(self, width, height):
        # Search atlases for a free spot
        for texture in self.textures:
            try:
                return texture.allocate(width, height)
            except NewTextureAtlasOutOfSpaceException:
                pass

        # If requested glyph size is bigger than atlas size, increase
        # next atlas size.  A better heuristic could be applied earlier
        # (say, if width is > 1/4 texture_width).
        if width > self.texture_width or height > self.texture_height:
            self.texture_width, self.texture_height, u, v= \
                Texture.get_texture_size(width * 2, height * 2)

        texture = self.create_glyph_texture()
        self.textures.insert(0, texture)

        # This can't fail.
        return texture.allocate(width, height)

    def get_glyph_renderer(self):
        raise NotImplementedError('Subclass must override')

    def get_glyphs(self, text):
        glyph_renderer = None
        for c in text:
            if c not in self.glyphs:
                if not glyph_renderer:
                    glyph_renderer = self.get_glyph_renderer()
                self.glyphs[c] = glyph_renderer.render(c)
        return [self.glyphs[c] for c in text] 

    def render(self, text):
        return TextLayout([StyledText(text, self)])

class GlyphRenderer(object):
    def render(self, text):
        pass

class Win32Font(Font):
    def __init__(self, name, size, bold=False, italic=False):
        super(Win32Font, self).__init__()

        # Create a dummy DC for coordinate mapping
        dc = user32.GetDC(0)
        logpixelsy = gdi32.GetDeviceCaps(dc, LOGPIXELSY)

        logfont = LOGFONT()
        # Conversion of point size to device pixels
        logfont.lfHeight = -size * logpixelsy / 72
        if bold:
            logfont.lfWeight = FW_BOLD
        else:
            logfont.lfWeight = FW_NORMAL
        logfont.lfItalic = italic
        logfont.lfFaceName = name
        logfont.lfQuality = ANTIALIASED_QUALITY
        self.hfont = gdi32.CreateFontIndirectA(byref(logfont))

        metrics = TEXTMETRIC()
        gdi32.SelectObject(dc, self.hfont)
        gdi32.GetTextMetricsA(dc, byref(metrics))
        self.ascent = metrics.tmAscent
        self.descent = metrics.tmDescent
        self.max_glyph_width = metrics.tmMaxCharWidth

    def apply_blend_state(self):
        # There is no alpha component, use luminance.
        glBlendFunc(GL_ONE, GL_ONE_MINUS_SRC_COLOR)
        glEnable(GL_BLEND)

    def get_glyph_renderer(self):
        return Win32GlyphRenderer(self)

class Win32GlyphRenderer(GlyphRenderer):
    _bitmap = None
    _bitmap_dc = None
    _bitmap_rect = None

    def __init__(self, font):
        super(Win32GlyphRenderer, self).__init__()
        self.font = font
        self._create_bitmap_dc(font.max_glyph_width, font.ascent + font.descent) 
        self._black = gdi32.GetStockObject(BLACK_BRUSH)
        self._white = gdi32.GetStockObject(WHITE_BRUSH)

    def __del__(self):
        if self._bitmap_dc:
            gdi32.DeleteDC(self._bitmap_dc)
        if self._bitmap:
            gdi32.DeleteObject(self._bitmap)

    def render(self, text):
        # Attempt to get ABC widths (only for TrueType)
        abc = ABC()
        if gdi32.GetCharABCWidthsW(self._bitmap_dc, 
            ord(text), ord(text), byref(abc)):
            width = abc.abcB 
            lsb = abc.abcA
            advance = abc.abcA + abc.abcB + abc.abcC
        else:
            width_buf = c_int()
            gdi32.GetCharWidth32(self._bitmap_dc, 
                ord(text), ord(text), byref(width_buf))
            width = width_buf.value
            lsb = 0
            advance = width

        # Can't get glyph-specific dimensions, use whole line-height.
        height = self._bitmap_rect.bottom

        # Draw to DC
        user32.FillRect(self._bitmap_dc, byref(self._bitmap_rect), self._black)
        gdi32.ExtTextOutA(self._bitmap_dc, -lsb, 0, 0, c_void_p(), text,
            len(text), c_void_p())
        gdi32.GdiFlush()

        # Create glyph object and copy bitmap data to texture
        glyph = self.font.allocate_glyph(width, height)
        glyph.set_bearings(font.descent, lsb, advance)

        glBindTexture(GL_TEXTURE_2D, glyph.texture_id)
        glPushClientAttrib(GL_CLIENT_PIXEL_STORE_BIT)
        glPixelStorei(GL_UNPACK_ROW_LENGTH, self._bitmap_rect.right)
        glTexSubImage2D(GL_TEXTURE_2D, 0,
            glyph.x, glyph.y,
            glyph.width, glyph.height,
            GL_RGBA,
            GL_UNSIGNED_BYTE,
            self._bitmap_data)
        glPopClientAttrib()

        return glyph
        
    def _create_bitmap_dc(self, width, height):
        if self._bitmap_dc:
            gdi32.ReleaseDC(self._bitmap_dc)
        if self._bitmap:
            gdi32.DeleteObject(self._bitmap)

        pitch = width * 4
        data = POINTER(c_byte * (height * pitch))()
        info = BITMAPINFO()
        info.bmiHeader.biSize = sizeof(info.bmiHeader)
        info.bmiHeader.biWidth = width
        info.bmiHeader.biHeight = height
        info.bmiHeader.biPlanes = 1
        info.bmiHeader.biBitCount = 32
        info.bmiHeader.biCompression = BI_RGB

        self._bitmap_dc = gdi32.CreateCompatibleDC(c_void_p())
        self._bitmap = gdi32.CreateDIBSection(c_void_p(),
            byref(info), DIB_RGB_COLORS, byref(data), c_void_p(),
            0)
        # Spookiness: the above line causes a "not enough storage" error,
        # even though that error cannot be generated according to docs,
        # and everything works fine anyway.  Call GetLastError to clear it.
        kernel32.GetLastError()
        gdi32.SelectObject(self._bitmap_dc, self._bitmap)
        gdi32.SelectObject(self._bitmap_dc, self.font.hfont)

        self._bitmap_data = data.contents
        gdi32.SetBkColor(self._bitmap_dc, 0)
        gdi32.SetTextColor(self._bitmap_dc, 0x00ffffff)

        self._bitmap_rect = RECT()
        self._bitmap_rect.left = 0
        self._bitmap_rect.right = width
        self._bitmap_rect.top = 0
        self._bitmap_rect.bottom = height



window = Window(256, 256)

glClearColor(.5, 0, 0, 1)
glClear(GL_COLOR_BUFFER_BIT)
glMatrixMode(GL_PROJECTION)
glOrtho(0, window.width, 0, window.height, -1, 1)
glMatrixMode(GL_MODELVIEW)

glEnable(GL_TEXTURE_2D)
glTranslatef(0, 20, 0)

font = Win32Font('Georgia', 72)
font.render("Hello, world!").draw()
#font.textures[0].draw()

window.flip()



exit = ExitHandler()
window.push_handlers(exit)
while not exit.exit:
    window.dispatch_events()
