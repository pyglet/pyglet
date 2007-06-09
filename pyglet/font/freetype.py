#!/usr/bin/env python
# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2007 Alex Holkner
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright 
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of the pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import ctypes
from ctypes import *
from ctypes import util
from warnings import warn

from pyglet.font import base
from pyglet import image
from pyglet.font.freetype_lib import *

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

FT_STYLE_FLAG_ITALIC = 1
FT_STYLE_FLAG_BOLD = 2

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

class FreeTypeGlyphRenderer(base.GlyphRenderer):
    def __init__(self, font):
        super(FreeTypeGlyphRenderer, self).__init__(font)
        self.font = font

    def render(self, text):
        face = self.font.face
        FT_Set_Char_Size(face, 0, self.font._face_size, 0, 0)
        glyph_index = fontconfig.FcFreeTypeCharIndex(byref(face), ord(text[0]))
        error = FT_Load_Glyph(face, glyph_index, FT_LOAD_RENDER)
        if error != 0:
            raise base.FontException(
                'Could not load glyph for "c"' % text[0], error) 
        glyph_slot = face.glyph.contents
        width = glyph_slot.bitmap.width
        height = glyph_slot.bitmap.rows
        baseline = height - glyph_slot.bitmap_top
        lsb = glyph_slot.bitmap_left
        advance = unfrac(glyph_slot.advance.x)
        pitch = glyph_slot.bitmap.pitch  # 1 component, so no alignment prob.

        # pitch should be negative, but much faster to just swap tex_coords
        img = image.ImageData(width, height, 
                              'A', glyph_slot.bitmap.buffer, pitch)
        glyph = self.font.create_glyph(img) 
        glyph.set_bearings(baseline, lsb, advance)
        glyph.tex_coords = (glyph.tex_coords[3],
                            glyph.tex_coords[2],
                            glyph.tex_coords[1],
                            glyph.tex_coords[0])

        return glyph

class FreeTypeMemoryFont(object):
    def __init__(self, data):
        self.buffer = (ctypes.c_byte * len(data))()
        ctypes.memmove(self.buffer, data, len(data))

        ft_library = ft_get_library()
        self.face = FT_Face()
        r = FT_New_Memory_Face(ft_library, 
            self.buffer, len(self.buffer), 0, self.face)
        if r != 0:
            raise base.FontException('Could not load font data')

        self.name = self.face.contents.family_name
        self.bold = self.face.contents.style_flags & FT_STYLE_FLAG_BOLD != 0
        self.italic = self.face.contents.style_flags & FT_STYLE_FLAG_ITALIC != 0

    def __del__(self):
        try:
            FT_Done_Face(self.face)
        except NameError:
            pass

class FreeTypeFont(base.Font):
    glyph_renderer_class = FreeTypeGlyphRenderer

    # Map font (name, bold, italic) to FreeTypeMemoryFont
    _memory_fonts = {}

    def __init__(self, name, size, bold=False, italic=False):
        super(FreeTypeFont, self).__init__()

        # Check if font name/style matches a font loaded into memory by user
        lname = name.lower()
        if (lname, bold, italic) in self._memory_fonts:
            font = self._memory_fonts[lname, bold, italic]
            self._set_face(font.face, size)
            return

        # Use fontconfig to match the font (or substitute a default).
        ft_library = ft_get_library()

        match = self.get_fontconfig_match(name, size, bold, italic)
        if not match:
            raise base.FontException('Could not match font "%s"' % name)

        f = FT_Face()
        if fontconfig.FcPatternGetFTFace(match, FC_FT_FACE, 0, byref(f)) != 0:
            value = FcValue()
            result = fontconfig.FcPatternGet(match, FC_FILE, 0, byref(value))
            if result != 0:
                raise base.FontException('No filename or FT face for "%s"' % \
                                         name)
            result = FT_New_Face(ft_library, value.u.s, 0, byref(f))
            if result:
                raise base.FontException('Could not load "%s": %d' % \
                                         (name, result))

        fontconfig.FcPatternDestroy(match)

        self._set_face(f, size)

    def _set_face(self, face, size):
        self.face = face.contents
        self._face_size = frac(size)

        FT_Set_Char_Size(self.face, 0, frac(size), 0, 0)
        self.ascent = self.face.ascender * size / self.face.units_per_EM
        self.descent = self.face.descender * size / self.face.units_per_EM

    @staticmethod
    def get_fontconfig_match(name, size, bold, italic):
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
        
        return match

    @classmethod
    def have_font(cls, name):
        value = FcValue()
        match = cls.get_fontconfig_match(name, 12, False, False)
        result = fontconfig.FcPatternGet(match, FC_FAMILY, 0, byref(value))
        return value.u.s == name
    
    @classmethod
    def add_font_data(cls, data):
        font = FreeTypeMemoryFont(data)
        cls._memory_fonts[font.name.lower(), font.bold, font.italic] = font
