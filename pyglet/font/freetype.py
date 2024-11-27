from __future__ import annotations

import warnings
from ctypes import POINTER, byref, c_ubyte, cast, memmove
from typing import NamedTuple

import pyglet
from pyglet import image
from pyglet.font import base
from pyglet.font.fontconfig import get_fontconfig
from pyglet.font.freetype_lib import (
    FT_LOAD_RENDER,
    FT_PIXEL_MODE_GRAY,
    FT_PIXEL_MODE_MONO,
    FT_STYLE_FLAG_BOLD,
    FT_STYLE_FLAG_ITALIC,
    FreeTypeError,
    FT_Byte,
    FT_Done_Face,
    FT_Face,
    FT_GlyphSlot,
    FT_Load_Glyph,
    FT_New_Face,
    FT_New_Memory_Face,
    FT_Reference_Face,
    FT_Set_Char_Size,
    f26p6_to_float,
    float_to_f26p6,
    ft_get_library,
)
from pyglet.util import asbytes, asstr


class FreeTypeGlyphRenderer(base.GlyphRenderer):
    def __init__(self, font: FreeTypeFont) -> None:
        super().__init__(font)
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

    def _get_glyph(self, character: str) -> None:
        assert self.font
        assert len(character) == 1

        self._glyph_slot = self.font.get_glyph_slot(character)
        self._bitmap = self._glyph_slot.bitmap

    def _get_glyph_metrics(self) -> None:
        self._width = self._glyph_slot.bitmap.width
        self._height = self._glyph_slot.bitmap.rows
        self._mode = self._glyph_slot.bitmap.pixel_mode
        self._pitch = self._glyph_slot.bitmap.pitch

        self._baseline = self._height - self._glyph_slot.bitmap_top
        self._lsb = self._glyph_slot.bitmap_left
        self._advance_x = int(f26p6_to_float(self._glyph_slot.advance.x))

    def _get_bitmap_data(self) -> None:
        if self._mode == FT_PIXEL_MODE_MONO:
            # BCF fonts always render to 1 bit mono, regardless of render
            # flags. (freetype 2.3.5)
            self._convert_mono_to_gray_bitmap()
        elif self._mode == FT_PIXEL_MODE_GRAY:
            # Usual case
            assert self._glyph_slot.bitmap.num_grays == 256
            self._data = self._glyph_slot.bitmap.buffer
        else:
            msg = "Unsupported render mode for this glyph"
            raise base.FontException(msg)

    def _convert_mono_to_gray_bitmap(self) -> None:
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

    def _create_glyph(self) -> base.Glyph:
        # In FT positive pitch means `down` flow, in Pyglet ImageData
        # negative values indicate a top-to-bottom arrangement. So pitch must be inverted.
        # Using negative pitch causes conversions, so much faster to just swap tex_coords
        img = image.ImageData(self._width,
                              self._height,
                              "A",
                              self._data,
                              abs(self._pitch))

        # HACK: Get text working in GLES until image data can be converted properly
        #       GLES don't support coversion during pixel transfer so we have to
        #       force specify the glyph format to be GL_ALPHA. This format is not
        #       supported in 3.3+ core, but are present in ES because of pixel transfer
        #       limitations.
        if pyglet.gl.current_context.get_info().get_opengl_api() == "gles":
            GL_ALPHA = 0x1906
            glyph = self.font.create_glyph(img, fmt=GL_ALPHA)
        else:
            glyph = self.font.create_glyph(img)

        glyph.set_bearings(self._baseline, self._lsb, self._advance_x)
        if self._pitch > 0:
            t = list(glyph.tex_coords)
            glyph.tex_coords = t[9:12] + t[6:9] + t[3:6] + t[:3]

        return glyph

    def render(self, text: str) -> base.Glyph:
        self._get_glyph(text[0])
        self._get_glyph_metrics()
        self._get_bitmap_data()
        return self._create_glyph()


class FreeTypeFontMetrics(NamedTuple):
    ascent: int
    descent: int


class MemoryFaceStore:
    _dict: dict[tuple[str, str, bool], FreeTypeMemoryFace]

    def __init__(self) -> None:
        self._dict = {}

    def add(self, face: FreeTypeMemoryFace) -> None:
        self._dict[face.name.lower(), face.weight, face.italic] = face

    def contains(self, name: str) -> bool:
        lname = name and name.lower() or ""
        return len([name for name, _, _ in self._dict if name == lname]) > 0

    def get(self, name: str, weight: str, italic: bool) -> FreeTypeMemoryFace | None:
        lname = name and name.lower() or ""
        return self._dict.get((lname, weight, italic), None)


class FreeTypeFont(base.Font):
    glyph_renderer_class = FreeTypeGlyphRenderer

    # Map font (name, weight, italic) to FreeTypeMemoryFace
    _memory_faces = MemoryFaceStore()
    face: FreeTypeFace

    def __init__(self, name: str, size: float, weight: str = "normal", italic: bool = False, stretch: bool = False,
                 dpi: int | None = None) -> None:

        if stretch:
            warnings.warn("The current font render does not support stretching.")  # noqa: B028

        super().__init__()
        self._name = name
        self.size = size
        self.weight = weight
        self.italic = italic
        self.dpi = dpi or 96

        self._load_font_face()
        self.metrics = self.face.get_font_metrics(self.size, self.dpi)

    @property
    def name(self) -> str:
        return self.face.family_name

    @property
    def ascent(self) -> int:
        return self.metrics.ascent

    @property
    def descent(self) -> int:
        return self.metrics.descent

    def get_glyph_slot(self, character: str) -> FT_GlyphSlot:
        glyph_index = self.face.get_character_index(character)
        self.face.set_char_size(self.size, self.dpi)
        return self.face.get_glyph_slot(glyph_index)

    def _load_font_face(self) -> None:
        self.face = self._memory_faces.get(self._name, self.weight, self.italic)
        if self.face is None:
            self._load_font_face_from_system()

    def _load_font_face_from_system(self) -> None:
        match = get_fontconfig().find_font(self._name, self.size, self.weight, self.italic)
        if not match:
            msg = f"Could not match font '{self._name}'"
            raise base.FontException(msg)
        self.filename = match.file
        self.face = FreeTypeFace.from_fontconfig(match)

    @classmethod
    def have_font(cls: type[FreeTypeFont], name: str) -> bool:
        if cls._memory_faces.contains(name):
            return True

        return get_fontconfig().have_font(name)

    @classmethod
    def add_font_data(cls: type[FreeTypeFont], data: bytes) -> None:
        face = FreeTypeMemoryFace(data)
        cls._memory_faces.add(face)


class FreeTypeFace:
    """FreeType typographic face object.

    Keeps the reference count to the face at +1 as long as this object exists. If other objects
    want to keep a face without a reference to this object, they should increase the reference
    counter themselves and decrease it again when done.
    """
    _name: str
    ft_face: FT_Face

    def __init__(self, ft_face: FT_Face) -> None:
        assert ft_face is not None
        self.ft_face = ft_face
        self._get_best_name()

    @classmethod
    def from_file(cls: type[FreeTypeFace], file_name: str) -> FreeTypeFace:
        ft_library = ft_get_library()
        ft_face = FT_Face()
        FT_New_Face(ft_library,
                    asbytes(file_name),
                    0,
                    byref(ft_face))
        return cls(ft_face)

    @classmethod
    def from_fontconfig(cls: type[FreeTypeFace], match):
        if match.face is not None:
            FT_Reference_Face(match.face)
            return cls(match.face)
        else:
            if not match.file:
                msg = f'No filename for "{match.name}"'
                raise base.FontException(msg)
            return cls.from_file(match.file)

    @property
    def name(self) -> str:
        return self._name

    @property
    def family_name(self) -> str:
        return asstr(self.ft_face.contents.family_name)

    @property
    def style_flags(self) -> int:
        return self.ft_face.contents.style_flags

    @property
    def bold(self) -> bool:
        return self.style_flags & FT_STYLE_FLAG_BOLD != 0

    @property
    def weight(self) -> str:
        return "normal"

    @property
    def italic(self) -> bool:
        return self.style_flags & FT_STYLE_FLAG_ITALIC != 0

    @property
    def face_flags(self) -> int:
        return self.ft_face.contents.face_flags

    def __del__(self) -> None:
        if self.ft_face is not None:
            FT_Done_Face(self.ft_face)
            self.ft_face = None

    def set_char_size(self, size: float, dpi: int) -> bool:
        face_size = float_to_f26p6(size)
        try:
            FT_Set_Char_Size(self.ft_face,
                             0,
                             face_size,
                             dpi,
                             dpi)
            return True
        except FreeTypeError as e:
            # Error 0x17 indicates invalid pixel size, so font size cannot be changed
            # TODO Warn the user?
            if e.errcode == 0x17:
                return False

            raise

    def get_character_index(self, character: str) -> int:
        return get_fontconfig().char_index(self.ft_face, character)

    def get_glyph_slot(self, glyph_index: int) -> FT_GlyphSlot:
        FT_Load_Glyph(self.ft_face, glyph_index, FT_LOAD_RENDER)
        return self.ft_face.contents.glyph.contents

    def get_font_metrics(self, size: float, dpi: int) -> FreeTypeFontMetrics:
        if self.set_char_size(size, dpi):
            metrics = self.ft_face.contents.size.contents.metrics
            if metrics.ascender == 0 and metrics.descender == 0:
                return self._get_font_metrics_workaround()

            return FreeTypeFontMetrics(ascent=int(f26p6_to_float(metrics.ascender)),
                                       descent=int(f26p6_to_float(metrics.descender)))

        return self._get_font_metrics_workaround()

    def _get_font_metrics_workaround(self) -> FreeTypeFontMetrics:
        # Workaround broken fonts with no metrics.  Has been observed with
        # courR12-ISO8859-1.pcf.gz: "Courier" "Regular"
        #
        # None of the metrics fields are filled in, so render a glyph and
        # grab its height as the ascent, and make up an arbitrary
        # descent.
        i = self.get_character_index("X")
        self.get_glyph_slot(i)
        ascent = self.ft_face.contents.available_sizes.contents.height
        return FreeTypeFontMetrics(ascent=ascent,
                                   descent=-ascent // 4)  # arbitrary.

    def _get_best_name(self) -> None:
        self._name = asstr(self.ft_face.contents.family_name)
        self._get_font_family_from_ttf()

    def _get_font_family_from_ttf(self) -> None:
        # Replace Freetype's generic family name with TTF/OpenType specific
        # name if we can find one; there are some instances where Freetype
        # gets it wrong.

        return  # FIXME: This is broken

        if self.face_flags & FT_FACE_FLAG_SFNT:
            name = FT_SfntName()
            for i in range(FT_Get_Sfnt_Name_Count(self.ft_face)):
                try:
                    FT_Get_Sfnt_Name(self.ft_face, i, name)
                    if not (name.platform_id == TT_PLATFORM_MICROSOFT and
                            name.encoding_id == TT_MS_ID_UNICODE_CS):
                        continue
                    # name.string is not 0 terminated! use name.string_len
                    self._name = name.string.decode("utf-16be", "ignore")
                except:
                    continue


class FreeTypeMemoryFace(FreeTypeFace):
    def __init__(self, data: bytes) -> None:
        self._copy_font_data(data)
        super().__init__(self._create_font_face())

    def _copy_font_data(self, data: bytes) -> None:
        self.font_data = (FT_Byte * len(data))()
        memmove(self.font_data, data, len(data))

    def _create_font_face(self) -> FT_Face:
        ft_library = ft_get_library()
        ft_face = FT_Face()
        FT_New_Memory_Face(ft_library,
                           self.font_data,
                           len(self.font_data),
                           0,
                           byref(ft_face))
        return ft_face
