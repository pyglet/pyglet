from __future__ import annotations

import warnings
from ctypes import POINTER, byref, c_ubyte, cast, memmove
from typing import NamedTuple, Sequence

import pyglet
from pyglet import image
from pyglet.font import base
from pyglet.font.base import GlyphPosition
from pyglet.font.fontconfig import get_fontconfig
from pyglet.font.freetype_lib import (
    FT_LOAD_RENDER,
    FT_PIXEL_MODE_GRAY,
    FT_PIXEL_MODE_MONO,
    FT_STYLE_FLAG_BOLD,
    FT_STYLE_FLAG_ITALIC,
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
    ft_get_library, FT_LOAD_TARGET_MONO, FT_LOAD_COLOR, FT_FACE_FLAG_SCALABLE, FT_FACE_FLAG_FIXED_SIZES,
    FT_FACE_FLAG_COLOR, FT_Select_Size, FT_PIXEL_MODE_BGRA, FT_Get_Char_Index, FT_FACE_FLAG_KERNING, FT_Vector,
    FT_Get_Kerning, FT_KERNING_DEFAULT, FT_LOAD_NO_BITMAP, FT_Load_Char
)
from pyglet.font.harfbuzz import harfbuzz_available, get_resource_from_ft_font, get_harfbuzz_shaped_glyphs
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

    def _get_glyph_by_char(self, character: str) -> None:
        assert self.font
        assert len(character) == 1

        self._glyph_slot = self.font.get_glyph_slot(character)
        self._bitmap = self._glyph_slot.bitmap

    def _get_glyph_by_index(self, glyph_index: int) -> None:
        self._glyph_slot = self.font.get_glyph_slot_index(glyph_index)
        self._bitmap = self._glyph_slot.bitmap

    def _get_glyph_metrics(self) -> None:
        self._width = self._glyph_slot.bitmap.width
        self._height = self._glyph_slot.bitmap.rows
        self._mode = self._glyph_slot.bitmap.pixel_mode
        self._pitch = self._glyph_slot.bitmap.pitch

        self._baseline = self._height - self._glyph_slot.bitmap_top
        self._lsb = self._glyph_slot.bitmap_left
        self._advance_x = int(f26p6_to_float(self._glyph_slot.advance.x))

    def _expand_to_rgba(self, data: bytes, src_format: str, dst_format: str) -> bytes:
        """Expands data type to 4 components with putting values into A.

        Will re-evaluate on a better system later.
        """
        src_len = len(src_format)
        dst_len = len(dst_format)

        if src_len >= dst_len:
            return data

        expanded_data = bytearray(len(data) // src_len * dst_len)
        mapping = {c: i for i, c in enumerate(src_format)}

        for i in range(len(data) // src_len):
            default_value = data[i * src_len + 0] if src_len > 0 else 0

            for j, c in enumerate(dst_format):
                if c in mapping:
                    expanded_data[i * dst_len + j] = 255
                elif c == 'A':
                    # Default alpha to fully opaque
                    expanded_data[i * dst_len + j] = default_value
                else:
                    expanded_data[i * dst_len + j] = 255

        return bytes(expanded_data)

    def _get_bitmap_data(self) -> None:
        if self._mode == FT_PIXEL_MODE_MONO:
            # BCF fonts always render to 1 bit mono, regardless of render
            # flags. (freetype 2.3.5)
            self._convert_mono_to_gray_bitmap()
        elif self._mode == FT_PIXEL_MODE_GRAY:
            # Usual case
            assert self._glyph_slot.bitmap.num_grays == 256
            self._data = self._glyph_slot.bitmap.buffer
        elif self._mode == FT_PIXEL_MODE_BGRA:
            # as of freetype 2.5
            self._data = self._glyph_slot.bitmap.buffer
        else:
            msg = "Unsupported render mode for this glyph"
            raise base.FontException(msg)

    def _convert_mono_to_gray_bitmap(self) -> None:
        if self._bitmap.buffer:
            bitmap_data = cast(self._bitmap.buffer,
                               POINTER(c_ubyte * (self._pitch * self._height))).contents

            data = (c_ubyte * (self._width * self._height))()

            # Tightly pack the data, as freetype pads it.
            for y in range(self._height):
                for x in range(self._width):
                    byte = bitmap_data[y * self._pitch + (x // 8)]
                    bit = 7 - (x % 8)  # Data is MSB; left-most pixel in a byte has value 128.
                    data[y * self._width + x] = 255 if (byte & (1 << bit)) else 0
        else:
            # No pointer in the buffer, no default or fallback in this font.
            data = (c_ubyte * 0)()
        self._data = data
        self._pitch = self._width

    def _create_glyph(self) -> base.Glyph:
        # Textures should be a minimum of 1x1.
        if self._width == 0 and self._height == 0:
            width = 1
            height = 1
            data = bytes(bytearray([0, 0, 0, 0]))
            pitch = 4
        else:
            width = self._width
            height = self._height
            # If it's not in BGRA, convert it manually.
            if self._mode != FT_PIXEL_MODE_BGRA:
                size = self._width * self._height
                ptr = cast(self._data, POINTER(c_ubyte * size))
                data = self._expand_to_rgba(ptr.contents, 'R', 'BGRA')
                pitch = self._pitch * 4
            else:
                data = self._data
                pitch = self._pitch

        img = image.ImageData(width, height, "BGRA", data, pitch)

        glyph = self.font.create_glyph(img)
        glyph.set_bearings(self._baseline, self._lsb, self._advance_x)

        # In FT positive pitch means `down` flow, in Pyglet ImageData
        # negative values indicate a top-to-bottom arrangement. So pitch must be inverted.
        # Using negative pitch causes a CPU re-ordering. For now, swap texture coordinates for speed.
        if self._pitch > 0:
            t = list(glyph.tex_coords)
            glyph.tex_coords = t[9:12] + t[6:9] + t[3:6] + t[:3]

        return glyph

    def render_index(self, glyph_index: int):
        self._get_glyph_by_index(glyph_index)
        self._get_glyph_metrics()
        self._get_bitmap_data()
        return self._create_glyph()

    def render(self, text: str) -> base.Glyph:
        self._get_glyph_by_char(text[0])
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
    _glyph_renderer: FreeTypeGlyphRenderer

    # Map font (name, weight, italic) to FreeTypeMemoryFace
    _memory_faces = MemoryFaceStore()
    face: FreeTypeFace
    fallbacks: list[FreeTypeFont]

    def __init__(self, name: str, size: float, weight: str = "normal", italic: bool = False,
                 stretch: bool | str = False, dpi: int | None = None) -> None:
        super().__init__()
        self._name = name
        self.size = size
        self.weight = weight
        self.italic = italic
        self.stretch = stretch
        self.dpi = dpi or 96
        self.pixel_size = (self.size * self.dpi) // 72

        self._load_font_face()
        self.metrics = self.face.get_font_metrics(self.size, self.dpi)

        if pyglet.options.text_shaping == 'harfbuzz' and harfbuzz_available():
            self.hb_resource = get_resource_from_ft_font(self)

    @property
    def name(self) -> str:
        return self.face.family_name

    @property
    def ascent(self) -> int:
        return self.metrics.ascent

    @property
    def descent(self) -> int:
        return self.metrics.descent

    def add_fallback(self, font):
        self.fallbacks.append(font)

    def _get_slot_from_fallbacks(self, character: str) -> FT_GlyphSlot | None:
        """Checks all fallback fonts in order to find a valid glyph index."""
        # Check if fallback has this glyph, if so.
        for fallback_font in self.fallbacks:
            fb_index = fallback_font.face.get_character_index(character)
            if fb_index:
                fallback_font.face.set_char_size(self.size, self.dpi)
                return fallback_font.get_glyph_slot(character)

        return None

    def get_glyph_slot_index(self, glyph_index: int) -> FT_GlyphSlot:
        self.face.set_char_size(self.size, self.dpi)
        return self.face.get_glyph_slot(glyph_index)

    def get_glyph_slot(self, character: str) -> FT_GlyphSlot:
        glyph_index = self.face.get_character_index(character)
        # Glyph index does not exist, so check fallback fonts.
        if glyph_index == 0 and (self.name not in self.fallbacks):
            glyph_slot = self._get_slot_from_fallbacks(character)
            if glyph_slot is not None:
                return glyph_slot

        self.face.set_char_size(self.size, self.dpi)
        return self.face.get_glyph_slot(glyph_index)

    def _load_font_face(self) -> None:
        self.face = self._memory_faces.get(self._name, self.weight, self.italic)
        if self.face is None:
            self._load_font_face_from_system()

    def _load_font_face_from_system(self) -> None:
        match = get_fontconfig().find_font(self._name, self.size, self.weight, self.italic, self.stretch)
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
        font_data = (FT_Byte * len(data))()
        memmove(font_data, data, len(data))

        face = FreeTypeMemoryFace(font_data, 0)
        cls._memory_faces.add(face)
        count = face.face_count
        # Some fonts may be a collection. Load each one.
        if count > 1:
            for i in range(1, count):
                face = FreeTypeMemoryFace(font_data, i)
                cls._memory_faces.add(face)

    def render_glyph_indices(self, indices: Sequence[int]):
        # Process any glyphs that have not been rendered.
        self._initialize_renderer()

        missing = set()
        for glyph_indice in set(indices):
            if glyph_indice not in self.glyphs:
                missing.add(glyph_indice)

        # Missing glyphs, get their info.
        for glyph_indice in missing:
            self.glyphs[glyph_indice] = self._glyph_renderer.render_index(glyph_indice)

    def get_glyphs(self, text: str) -> tuple[list[base.Glyph], list[base.GlyphPosition]]:
        """Create and return a list of Glyphs for `text`.

        If any characters do not have a known glyph representation in this
        font, a substitution will be made.

        Args:
            text:
                Text to render.
        """
        self._initialize_renderer()
        if pyglet.options.text_shaping == "harfbuzz" and harfbuzz_available():
            return get_harfbuzz_shaped_glyphs(self, text)
        else:
            glyphs = []  # glyphs that are committed.
            for idx, c in enumerate(text):
                # Get the glyph for 'c'.  Hide tabs (Windows and Linux render
                # boxes)
                if c == "\t":
                    c = " "  # noqa: PLW2901
                if c not in self.glyphs:
                    self.glyphs[c] = self._glyph_renderer.render(c)
                glyphs.append(self.glyphs[c])

            return glyphs, [GlyphPosition(0, 0, 0, 0)] * len(text)

    def get_text_size(self, text: str) -> tuple[int, int]:
        width = 0
        max_top = 0
        min_bottom = 0
        length = len(text)
        self.face.set_char_size(self.size, self.dpi)
        for i, char in enumerate(text):
            FT_Load_Char(self.face.ft_face, ord(char), FT_LOAD_NO_BITMAP)
            slot = self.face.ft_face.contents.glyph.contents

            if i == length-1:
                # Last glyph, use just the width.
                width += slot.metrics.width >> 6
            else:
                width += slot.advance.x >> 6

            glyph_top = slot.metrics.horiBearingY >> 6
            glyph_bottom = (slot.metrics.horiBearingY - slot.metrics.height) >> 6

            max_top = max(max_top, glyph_top)
            min_bottom = min(min_bottom, glyph_bottom)

        return width, max_top - min_bottom

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

        self._italic = self.style_flags & FT_STYLE_FLAG_ITALIC != 0
        bold = self.style_flags & FT_STYLE_FLAG_BOLD != 0
        if bold:
            self._weight = "bold"
        else:
            # Sometimes it may have a weight, but FT_STYLE_FLAG_BOLD is not accurate. Check the font config.
            config = get_fontconfig()
            self._weight, italic, self._stretch = config.style_from_face(self.ft_face)
            if italic != self._italic:
                # Discrepancy in italics?
                self._italic = italic

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
    def style_name(self) -> str:
        return asstr(self.ft_face.contents.style_name)

    @property
    def style_flags(self) -> int:
        return self.ft_face.contents.style_flags

    @property
    def bold(self) -> bool:
        return self.style_flags & FT_STYLE_FLAG_BOLD != 0

    @property
    def weight(self) -> str:
        return self._weight

    @property
    def italic(self) -> bool:
        return self._italic

    @property
    def face_flags(self) -> int:
        return self.ft_face.contents.face_flags

    def __del__(self) -> None:
        if self.ft_face is not None:
            FT_Done_Face(self.ft_face)
            self.ft_face = None

    def set_char_size(self, size: float, dpi: int) -> bool:
        if self.face_flags & FT_FACE_FLAG_SCALABLE:
            face_size = float_to_f26p6(size)
            FT_Set_Char_Size(self.ft_face, 0, face_size, dpi, dpi)

        elif self.face_flags & FT_FACE_FLAG_COLOR:
            if FT_Select_Size:
                FT_Select_Size(self.ft_face, 0)
            else:
                return False

        elif self.face_flags & FT_FACE_FLAG_FIXED_SIZES:
            if self.ft_face.contents.num_fixed_sizes:
                if FT_Select_Size:
                    FT_Select_Size(self.ft_face, 0)
                else:
                    return False
            else:
                warnings.warn(f"{self.name} no fixed sizes, but is flagged as a fixed size font.")

        return True

    def get_character_index(self, character: str) -> int:
        return FT_Get_Char_Index(self.ft_face, ord(character))

    def get_glyph_slot(self, glyph_index: int) -> FT_GlyphSlot:
        flags = FT_LOAD_RENDER
        if pyglet.options.text_antialiasing is False:
            flags |= FT_LOAD_TARGET_MONO

        if self.face_flags & FT_FACE_FLAG_COLOR:
            flags |= FT_LOAD_COLOR

        FT_Load_Glyph(self.ft_face, glyph_index, flags)
        return self.ft_face.contents.glyph.contents

    def get_font_metrics(self, size: float, dpi: int) -> FreeTypeFontMetrics:
        if self.set_char_size(size, dpi):
            metrics = self.ft_face.contents.size.contents.metrics
            if metrics.ascender == 0 and metrics.descender == 0:
                return self._get_font_metrics_workaround()

            return FreeTypeFontMetrics(ascent=int(f26p6_to_float(metrics.ascender)),
                                       descent=int(f26p6_to_float(metrics.descender)),
                                       )

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
    def __init__(self, data: bytes, face_index: int = 0) -> None:
        self.font_data = data
        ft_library = ft_get_library()
        ft_face = FT_Face()
        FT_New_Memory_Face(ft_library,
                           self.font_data,
                           len(self.font_data),
                           face_index,
                           byref(ft_face))

        super().__init__(ft_face)

    @property
    def face_count(self) -> int:
        return self.ft_face.contents.num_faces
