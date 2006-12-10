#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from pyglet.GL.VERSION_1_1 import *
try:
    from pyglet.GL.ARB_imaging import *
    _have_imaging = True
except ImportError:
    _have_imaging = False

from ctypes import *
from ctypes import util
from warnings import warn

from pyglet.text import *
from pyglet.text.freetype_lib import *

# fontconfig library definitions

path = util.find_library('fontconfig')
if not path:
    raise ImportError('Cannot locate fontconfig library')
fontconfig = cdll.LoadLibrary(path)

FcResult = c_int

fontconfig.FcPatternBuild.restype = c_void_p
fontconfig.FcFontMatch.restype = c_void_p
fontconfig.FcFreeTypeCharIndex.restype = c_uint

FC_FAMILY = 'family'
FC_SIZE = 'size'
FC_SLANT = 'slant'
FC_WEIGHT = 'weight'
FC_FT_FACE = 'ftface'
FC_FILE = 'file'

FC_WEIGHT_REGULAR = 80
FC_WEIGHT_BOLD = 200

FC_SLANT_ROMAN = 0
FC_SLANT_ITALIC = 100

(FcTypeVoid,
 FcTypeInteger,
 FcTypeDouble, 
 FcTypeString, 
 FcTypeBool,
 FcTypeMatrix,
 FcTypeCharSet,
 FcTypeFTFace,
 FcTypeLangSet) = range(9)
FcType = c_int

(FcMatchPattern,
 FcMatchFont) = range(2)
FcMatchKind = c_int

class _FcValueUnion(Union):
    _fields_ = [
        ('s', c_char_p),
        ('i', c_int),
        ('b', c_int),
        ('d', c_double),
        ('m', c_void_p),
        ('c', c_void_p),
        ('f', c_void_p),
        ('p', c_void_p),
        ('l', c_void_p),
    ]

class FcValue(Structure):
    _fields_ = [
        ('type', FcType),
        ('u', _FcValueUnion)
    ]

# End of library definitions


# Hehe, battlestar galactica... (sorry.  was meant to be short for "fraction")
def frac(value):
    return int(value * 64)

def unfrac(value):
    return value >> 6

class FreeTypeGlyphTextureAtlas(GlyphTextureAtlas):
    def apply_blend_state(self):
        # There is no alpha component, use luminance.
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_BLEND)

class FreeTypeGlyphRenderer(GlyphRenderer):
    def __init__(self, font):
        super(FreeTypeGlyphRenderer, self).__init__(font)
        self.font = font

    def render(self, text):
        face = self.font.face
        glyph_index = fontconfig.FcFreeTypeCharIndex(byref(face), ord(text[0]))
        error = FT_Load_Glyph(face, glyph_index, FT_LOAD_RENDER)
        if error != 0:
            raise FontException('Could not load glyph for "c"' % text[0], error) 
        glyph_slot = face.glyph.contents
        width = glyph_slot.bitmap.width
        height = glyph_slot.bitmap.rows
        baseline = height - glyph_slot.bitmap_top
        lsb = glyph_slot.bitmap_left
        advance = unfrac(glyph_slot.advance.x)
        pitch = glyph_slot.bitmap.pitch  # 1 component, so no alignment prob.
    
        # Allocate space within an atlas
        glyph = self.font.allocate_glyph(width, height)
        glyph.set_bearings(baseline, lsb, advance)
        glyph.flip_vertical()

        # Copy bitmap into texture
        if _have_imaging:
            glMatrixMode(GL_COLOR)
            matrix = (c_float * 16)(
                1, 0, 0, 1,
                0, 1, 0, 0,
                0, 0, 1, 0, 
                0, 0, 0, 0)
            glLoadMatrixf(matrix)
        else:
            import warnings
            warnings.warn('No ARB_imaging: font colour/blend will be incorrect')
            # TODO

        glPushClientAttrib(GL_CLIENT_PIXEL_STORE_BIT)
        glBindTexture(GL_TEXTURE_2D, glyph.texture.id)
        glPixelStorei(GL_UNPACK_ROW_LENGTH, pitch)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)
        glTexSubImage2D(GL_TEXTURE_2D, 0,
            glyph.x, glyph.y,
            width, height,
            GL_LUMINANCE,
            GL_UNSIGNED_BYTE,
            glyph_slot.bitmap.buffer)
        glPopClientAttrib()

        if _have_imaging:
            glLoadIdentity()
            glMatrixMode(GL_MODELVIEW)

        return glyph

class FreeTypeFont(BaseFont):
    glyph_texture_atlas_class = FreeTypeGlyphTextureAtlas
    glyph_renderer_class = FreeTypeGlyphRenderer

    def __init__(self, name, size, bold=False, italic=False):
        super(FreeTypeFont, self).__init__()
        ft_library = ft_get_library()

        if bold:
            bold = FC_WEIGHT_BOLD
        else:
            bold = FC_WEIGHT_REGULAR

        if italic:
            italic = FC_SLANT_ITALIC
        else:
            italic = FC_SLANT_ROMAN

        fontconfig.FcInit()

        pattern = fontconfig.FcPatternCreate()
        fontconfig.FcPatternAddDouble(pattern, FC_SIZE, c_double(size))
        fontconfig.FcPatternAddInteger(pattern, FC_WEIGHT, bold)
        fontconfig.FcPatternAddInteger(pattern, FC_SLANT, italic)
        fontconfig.FcPatternAddString(pattern, FC_FAMILY, name)
        fontconfig.FcConfigSubstitute(0, pattern, FcMatchPattern)
        fontconfig.FcDefaultSubstitute(pattern)

        # Look for a font that matches pattern
        result = FcResult()
        match = fontconfig.FcFontMatch(0, pattern, byref(result))
        fontconfig.FcPatternDestroy(pattern)
        
        value = FcValue()
        result = fontconfig.FcPatternGet(match, FC_FAMILY, 0, byref(value))
        if result != 0:
            raise FontException('Could not match font "%s"' % name)
        if value.u.s != name:
            warn('Using font "%s" in place of "%s"' % (value.u.s, name))

        f = FT_Face()
        if fontconfig.FcPatternGetFTFace(match, FC_FT_FACE, 0, byref(f)) != 0:
            result = fontconfig.FcPatternGet(match, FC_FILE, 0, byref(value))
            if result != 0:
                raise FontException('No filename or FT face for "%s"' % name)
            result = FT_New_Face(ft_library, value.u.s, 0, byref(f))
            if result:
                raise FontException('Could not load "%s": %d' % (name, result))

        fontconfig.FcPatternDestroy(match)

        self.face = f.contents

        FT_Set_Char_Size(self.face, 0, frac(size), 0, 0)
        self.ascent = self.face.ascender * size / self.face.units_per_EM
        self.descent = self.face.descender * size / self.face.units_per_EM
