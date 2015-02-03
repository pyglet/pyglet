# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
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
#  * Neither the name of pyglet nor the names of its
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

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import ctypes
from pyglet.compat import asbytes
from pyglet.font import base
from pyglet import image
from pyglet.font.fontconfig import get_fontconfig
from pyglet.font.freetype_lib import *

FT_STYLE_FLAG_ITALIC = 1
FT_STYLE_FLAG_BOLD = 2

(FT_RENDER_MODE_NORMAL,
 FT_RENDER_MODE_LIGHT,
 FT_RENDER_MODE_MONO,
 FT_RENDER_MODE_LCD,
 FT_RENDER_MODE_LCD_V) = range(5)


def FT_LOAD_TARGET_(x):
    return (x & 15) << 16

FT_LOAD_TARGET_NORMAL = FT_LOAD_TARGET_(FT_RENDER_MODE_NORMAL)
FT_LOAD_TARGET_LIGHT = FT_LOAD_TARGET_(FT_RENDER_MODE_LIGHT)
FT_LOAD_TARGET_MONO = FT_LOAD_TARGET_(FT_RENDER_MODE_MONO)
FT_LOAD_TARGET_LCD = FT_LOAD_TARGET_(FT_RENDER_MODE_LCD)
FT_LOAD_TARGET_LCD_V = FT_LOAD_TARGET_(FT_RENDER_MODE_LCD_V)

(FT_PIXEL_MODE_NONE,
 FT_PIXEL_MODE_MONO,
 FT_PIXEL_MODE_GRAY,
 FT_PIXEL_MODE_GRAY2,
 FT_PIXEL_MODE_GRAY4,
 FT_PIXEL_MODE_LCD,
 FT_PIXEL_MODE_LCD_V) = range(7)


def f16p16_to_float(value):
    return float(value) / (1 << 16)


def float_to_f16p16(value):
    return int(value * (1 << 16))


def f26p6_to_float(value):
    return float(value) / (1 << 6)


def float_to_f26p6(value):
    return int(value * (1 << 6))


class FreeTypeGlyphRenderer(base.GlyphRenderer):
    def __init__(self, font):
        super(FreeTypeGlyphRenderer, self).__init__(font)
        self.font = font

        self._glyph_slot = None
        self._bitmap = None

        self._width = None
        self._height = None
        self._mode = None
        self._pitch = None

        self._baseline = None
        self._lsb = None
        self._advance_x = None

        self._data = None

    def _get_glyph(self, character):
        assert self.font
        assert len(character) == 1

        self._glyph_slot = self.font.get_glyph_slot(character)
        self._bitmap = self._glyph_slot.bitmap

    def _get_glyph_metrics(self):
        self._width = self._glyph_slot.bitmap.width
        self._height = self._glyph_slot.bitmap.rows
        self._mode = self._glyph_slot.bitmap.pixel_mode
        self._pitch = self._glyph_slot.bitmap.pitch

        self._baseline = self._height - self._glyph_slot.bitmap_top
        self._lsb = self._glyph_slot.bitmap_left
        self._advance_x = int(f26p6_to_float(self._glyph_slot.advance.x))

    def _get_bitmap_data(self):
        if self._mode == FT_PIXEL_MODE_MONO:
            # BCF fonts always render to 1 bit mono, regardless of render
            # flags. (freetype 2.3.5)
            self._convert_mono_to_gray_bitmap()
        elif self._mode == FT_PIXEL_MODE_GRAY:
            # Usual case
            assert self._glyph_slot.bitmap.num_grays == 256
            self._data = self._glyph_slot.bitmap.buffer
        else:
            raise base.FontException('Unsupported render mode for this glyph')

    def _convert_mono_to_gray_bitmap(self):
        bitmap_data = cast(self._bitmap.buffer,
                           POINTER(c_ubyte * (self._pitch * self._height))).contents
        data = (c_ubyte * (self._pitch * 8 * self._height))()
        data_i = 0
        for byte in bitmap_data:
            # Data is MSB; left-most pixel in a byte has value 128.
            data[data_i + 0] = (byte & 0x80) and 255 or 0
            data[data_i + 1] = (byte & 0x40) and 255 or 0
            data[data_i + 2] = (byte & 0x20) and 255 or 0
            data[data_i + 3] = (byte & 0x10) and 255 or 0
            data[data_i + 4] = (byte & 0x08) and 255 or 0
            data[data_i + 5] = (byte & 0x04) and 255 or 0
            data[data_i + 6] = (byte & 0x02) and 255 or 0
            data[data_i + 7] = (byte & 0x01) and 255 or 0
            data_i += 8
        self._data = data
        self._pitch <<= 3

    def _create_glyph(self):
        # In FT positive pitch means `down` flow, in Pyglet ImageData
        # negative values indicate a top-to-bottom arrangement. So pitch must be inverted.
        # Using negative pitch causes conversions, so much faster to just swap tex_coords
        img = image.ImageData(self._width,
                              self._height,
                              'A',
                              self._data,
                              abs(self._pitch))
        glyph = self.font.create_glyph(img)
        glyph.set_bearings(self._baseline, self._lsb, self._advance_x)
        if self._pitch > 0:
            t = list(glyph.tex_coords)
            glyph.tex_coords = t[9:12] + t[6:9] + t[3:6] + t[:3]

        return glyph

    def render(self, text):
        self._get_glyph(text[0])
        self._get_glyph_metrics()
        self._get_bitmap_data()
        return self._create_glyph()


class FreeTypeMemoryFont(object):
    def __init__(self, data):
        self._copy_font_data(data)
        self._create_font_face()
        self._get_font_properties()

    def _copy_font_data(self, data):
        self.buffer = (ctypes.c_byte * len(data))()
        ctypes.memmove(self.buffer, data, len(data))

    def _create_font_face(self):
        ft_library = ft_get_library()
        self.face = FT_Face()
        error = FT_New_Memory_Face(ft_library,
                                   self.buffer,
                                   len(self.buffer),
                                   0,
                                   self.face)
        FreeTypeError.check_and_raise_on_error('Could not load font data', error)

    def _get_font_properties(self):
        self.name = self.face.contents.family_name
        self.bold = self.face.contents.style_flags & FT_STYLE_FLAG_BOLD != 0
        self.italic = self.face.contents.style_flags & FT_STYLE_FLAG_ITALIC != 0

        self._get_font_family_from_ttf()

    def _get_font_family_from_ttf(self):
        # Replace Freetype's generic family name with TTF/OpenType specific
        # name if we can find one; there are some instances where Freetype
        # gets it wrong.
        if self.face.contents.face_flags & FT_FACE_FLAG_SFNT:
            name = FT_SfntName()
            for i in range(FT_Get_Sfnt_Name_Count(self.face)):
                result = FT_Get_Sfnt_Name(self.face, i, name)
                if result != 0:
                    continue
                if not (name.platform_id == TT_PLATFORM_MICROSOFT and
                        name.encoding_id == TT_MS_ID_UNICODE_CS):
                    continue
                if name.name_id == TT_NAME_ID_FONT_FAMILY:
                    string = string_at(name.string, name.string_len)
                    self.name = string.decode('utf-16be', 'ignore')

    def __del__(self):
        try:
            FT_Done_Face(self.face)
        except:
            pass


class FreeTypeFont(base.Font):
    glyph_renderer_class = FreeTypeGlyphRenderer

    # Map font (name, bold, italic) to FreeTypeMemoryFont
    _memory_fonts = {}

    def __init__(self, name, size, bold=False, italic=False, dpi=None):
        super(FreeTypeFont, self).__init__()

        self.name = name
        self.size = size
        self.face_size = float_to_f26p6(size)
        self.bold = bold
        self.italic = italic
        self.dpi = dpi or 96  # as of pyglet 1.1; pyglet 1.0 had 72.

        self._set_face(self._load_font_face())

    def get_character_index(self, character):
        assert self.face
        return get_fontconfig().char_index(self.face, character)

    def get_glyph_slot(self, character):
        error = FT_Set_Char_Size(self.face,
                                 0,
                                 self.face_size,
                                 self.dpi,
                                 self.dpi)
        # Error 0x17 indicates invalid pixel size, so font size cannot be changed
        # TODO Warn the user?
        if error != 0x17:
            FreeTypeError.check_and_raise_on_error('Could not set size for "%c"' % character, error)

        glyph_index = self.get_character_index(character)

        error = FT_Load_Glyph(self.face, glyph_index, FT_LOAD_RENDER)
        FreeTypeError.check_and_raise_on_error('Could not load glyph for "%c"' % character, error)

        return self.face.glyph.contents

    def _load_font_face(self):
        memory_font = self._get_memory_font(self.name, self.bold, self.italic)
        if memory_font:
            return memory_font.face
        else:
            return self._load_font_face_from_system()

    def _load_font_face_from_system(self):
        match = get_fontconfig().find_font(self.name, self.size, self.bold, self.italic)
        if not match:
            raise base.FontException('Could not match font "%s"' % self.name)

        font_face = match.face
        if not font_face:
            # Try to load from file directly
            if not match.file:
                raise base.FontException('No filename for "%s"' % self.name)

            font_face = self._load_font_face_from_file(match.file)

        return font_face

    @staticmethod
    def _load_font_face_from_file(file_name):
        font_face = FT_Face()
        ft_library = ft_get_library()
        error = FT_New_Face(ft_library, asbytes(file_name), 0, byref(font_face))
        FreeTypeError.check_and_raise_on_error('Could not load font from "%s"' % file_name, error)
        return font_face

    def _set_face(self, face):
        self.face = face.contents
        self._get_font_metrics()

    def _get_font_metrics(self):
        error = FT_Set_Char_Size(self.face, 0, self.face_size, self.dpi, self.dpi)
        # Error 0x17 indicates invalid pixel size, so no metrics
        if error == 0x17:
            self._get_font_metrics_workaround()
        else:
            FreeTypeError.check_and_raise_on_error('Could not set size', error)

            metrics = self.face.size.contents.metrics
            if metrics.ascender == 0 and metrics.descender == 0:
                self._get_font_metrics_workaround()
            else:
                self.ascent = int(f26p6_to_float(metrics.ascender))
                self.descent = int(f26p6_to_float(metrics.descender))

    def _get_font_metrics_workaround(self):
        # Workaround broken fonts with no metrics.  Has been observed with
        # courR12-ISO8859-1.pcf.gz: "Courier" "Regular"
        #
        # None of the metrics fields are filled in, so render a glyph and
        # grab its height as the ascent, and make up an arbitrary
        # descent.
        i = get_fontconfig().char_index(self.face, 'X')
        error = FT_Load_Glyph(self.face, i, FT_LOAD_RENDER)
        FreeTypeError.check_and_raise_on_error('Could load glyph for "X"', error)

        self.ascent = self.face.available_sizes.contents.height
        self.descent = -self.ascent // 4  # arbitrary.

    @classmethod
    def have_font(cls, name):
        # Check memory cache first
        name = name.lower()
        for font in cls._memory_fonts.values():
            if font.name.lower() == name:
                return True

        # Check system
        match = get_fontconfig().find_font(name, 12, False, False)
        if match:
            # Check the name matches, fontconfig can return a default
            if name and match.name and match.name.lower() != name.lower():
                return False
            return True
        else:
            return False

    @classmethod
    def add_font_data(cls, data):
        font = FreeTypeMemoryFont(data)
        cls._memory_fonts[font.name.lower(), font.bold, font.italic] = font

    @classmethod
    def _get_memory_font(cls, name, bold, italic):
        lname = name and name.lower() or ''
        return cls._memory_fonts.get((lname, bold, italic))
