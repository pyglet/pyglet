from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING
from ctypes import c_void_p, c_uint16, c_uint32, string_at, create_string_buffer, py_object, cast, POINTER
import sys

from pyglet.font.base import GlyphPosition

if TYPE_CHECKING:
    from pyglet.font.freetype import FreeTypeFont
    from pyglet.font.dwrite import Win32DirectWriteFont
    from pyglet.font.quartz import QuartzFont
    from pyglet.font.base import Font, Glyph

from .harfbuzz_lib import hb_lib
_available = False

if hb_lib:
    _available = True

from .harfbuzz_lib import HB_MEMORY_MODE_READONLY, HB_DIRECTION_LTR


def harfbuzz_available() -> bool:
    """Return if the Harfbuzz library is available to use."""
    return _available


_hb_cache: dict[tuple[str, str, bool, str | bool], _HarfbuzzResources] = {}


def _add_utf16_buffer(text: str, buffer: c_void_p) -> None:
    txt_utf16 = text.encode("utf-16-le")  # HarfBuzz expects little-endian UTF-16
    length = len(txt_utf16) // 2
    txt_array = (c_uint16 * length).from_buffer_copy(txt_utf16)
    hb_lib.hb_buffer_add_utf16(buffer, txt_array, length, 0, length)

def _add_utf32_buffer(text: str, buffer: c_void_p) -> None:
    txt_utf32 = text.encode("utf-32-le")
    char_ct = (len(txt_utf32) // 4)
    txt_array = (c_uint32 * char_ct).from_buffer_copy(txt_utf32)
    hb_lib.hb_buffer_add_utf32(buffer, txt_array,char_ct, 0, char_ct)


# Set which unicode python is using for the strings.
if sys.maxunicode == 0x10FFFF:  # UTF-32
    set_buffer_string = _add_utf32_buffer
elif sys.maxunicode == 0xFFFF:  # UTF-16
    set_buffer_string = _add_utf16_buffer

def get_resource_from_ct_font(font: QuartzFont):
    """Get a harfbuzz resource object from a CoreText (Mac) font."""
    key = (font.name, font.weight, font.italic, font.stretch)
    if key in _hb_cache:
        return _hb_cache[key]

    resource = _HarfbuzzResources()
    hb_face = font._get_hb_face()
    resource.load_from_tabled_face(hb_face)
    _hb_cache[key] = resource
    return resource


def get_resource_from_dw_font(font: Win32DirectWriteFont) -> _HarfbuzzResources:
    """Get a harfbuzz resource object from a DirectWrite (Windows) font."""
    key = (font.name, font.weight, font.italic, font.stretch)
    if key in _hb_cache:
        return _hb_cache[key]

    data = font.get_font_data()
    if data:
        resource = _HarfbuzzResources()
        resource.load_from_memory(data)
        _hb_cache[key] = resource
        return resource

    raise Exception("Font data could not be read.")

def get_resource_from_ft_font(font: FreeTypeFont) -> _HarfbuzzResources:
    """Get a harfbuzz resource object from a FreeType (Linux) font."""
    key = (font.name, font.weight, font.italic, font.stretch)
    if key in _hb_cache:
        return _hb_cache[key]

    stream = font.face.ft_face.contents.stream.contents
    data = string_at(stream.base, stream.size)
    resource = _HarfbuzzResources()
    resource.load_from_memory(data)
    _hb_cache[key] = resource
    return resource


def get_resource_from_path(font_path: str):
    with open(font_path, "rb") as f:
        data = f.read()

    resource = _HarfbuzzResources()
    resource.load_from_memory(data)
    return resource

def _get_fallback_glyph_shape(font: Font, text: str) -> tuple[list[Glyph], list[GlyphPosition]]:
    glyphs = []
    offsets = []
    pystr_len = len(text)
    for fallback in font.fallbacks:
        glyph_info = fallback.hb_resource.shape_text(text, fallback.pixel_size)

        indices = [glyph_data["codepoint"] for glyph_data in glyph_info]
        fallback.render_glyph_indices(indices)

        for glyph_data in glyph_info:
            glyph = fallback.glyphs[glyph_data["codepoint"]]
            glyphs.append(glyph)
            offset =  GlyphPosition(glyph_data["x_advance"]-glyph.advance, glyph_data["y_advance"],
                                         glyph_data["x_offset"], glyph_data["y_offset"])
            offsets.append(offset)

    diff = pystr_len - len(glyphs)
    if diff > 0:
        for i in range(diff):
            glyphs.append(font._zero_glyph)
            offsets.append(GlyphPosition(0, 0, 0, 0))

    return glyphs, offsets

def get_harfbuzz_shaped_glyphs(font: Font, text: str) -> tuple[list[Glyph], list[GlyphPosition]]:
    glyph_info = font.hb_resource.shape_text(text, font.pixel_size)
    clusters = [glyph_data["cluster"] for glyph_data in glyph_info]
    cluster_map = defaultdict(list)

    # Find any clusters that have empty indices.
    empty_clusters = {}
    indices = []
    for glyph_data in glyph_info:
        # If any clusters have no codepoint, determine the size to pass to fallback.
        cluster_num = glyph_data["cluster"]
        glyph_index = glyph_data["codepoint"]
        if glyph_index == 0 and cluster_num not in empty_clusters:
            empty_clusters[cluster_num] = clusters.count(cluster_num)

        if cluster_num not in cluster_map:
            cluster_map[cluster_num] = []

        cluster_map[cluster_num].append(glyph_data)
        indices.append(glyph_index)

    font.render_glyph_indices(indices)

    # If a cluster is missing and had 0 indices.
    missing_glyphs = {}
    for cluster_id, cluster_ct in empty_clusters.items():
        missing_text = text[cluster_id:cluster_id + cluster_ct]
        if missing_text not in font.glyphs:
            if missing_text == '\n':
                fb_glyph_info = ([font._zero_glyph], [GlyphPosition(0, 0, 0, 0)])
            else:
                # Get glyphs from fallback, since we need the fallback to actually render it.
                fb_glyph_info = _get_fallback_glyph_shape(font, missing_text)
            font.glyphs[missing_text] = fb_glyph_info  # Cache by string to prevent future fallback paths.
        missing_glyphs[cluster_id] = font.glyphs[missing_text]

    glyphs = []
    offsets = []
    for i in range(len(text)):
        cluster_glyph_info = cluster_map[i]

        # Cluster has data, check if it's part of the missing glyphs.
        if i in missing_glyphs:
            _glyphs, _offsets = missing_glyphs[i]
            glyphs.extend(_glyphs)
            offsets.extend(_offsets)

        # If this cluster is missing, add some zero glyphs until count matches.
        elif len(cluster_glyph_info) == 0:
            while len(glyphs) - 1 < i:
                glyphs.append(font._zero_glyph)
                offsets.append(GlyphPosition(0, 0, 0, 0))
        else:
            for glyph_info in cluster_glyph_info:
                glyph = font.glyphs[glyph_info["codepoint"]]
                glyphs.append(glyph)

                offsets.append(
                    GlyphPosition(glyph_info["x_advance"] - glyph.advance, glyph_info["y_advance"],
                                  glyph_info["x_offset"], glyph_info["y_offset"])
                )

    return glyphs, offsets


class _HarfbuzzResources:
    def __init__(self) -> None:
        self.blob = None
        self.face = None
        self.font = None

    def load_from_tabled_face(self, hb_face: c_void_p) -> None:
        self.blob = None
        self.face = hb_face
        self.font = hb_lib.hb_font_create(self.face)

    def load_from_memory(self, data: bytes) -> None:
        data_len = len(data)
        data_buf = create_string_buffer(data, data_len)
        self.blob = hb_lib.hb_blob_create(data_buf, data_len, HB_MEMORY_MODE_READONLY, None, None)
        self.face = hb_lib.hb_face_create(self.blob, 0)
        self.font = hb_lib.hb_font_create(self.face)

    def shape_text(self, text: str, pixel_size: int, direction: int=HB_DIRECTION_LTR):
        """Shapes the given string using the provided hb_font.
        Returns a list of dictionaries for each glyph containing:
          - codepoint: the glyph index
          - cluster: the index into the original string
          - x_advance, y_advance: the advances (including kerning adjustments)
          - x_offset, y_offset: the offsets (shaped adjustments)
        """
        # Create a new buffer.
        buf = hb_lib.hb_buffer_create()

        # hb_lib.hb_buffer_set_cluster_level(buf, HB_BUFFER_CLUSTER_LEVEL_MONOTONE_CHARACTERS)
        set_buffer_string(text, buf)

        scale = int(pixel_size * 64)
        hb_lib.hb_font_set_scale(self.font, scale, scale)

        hb_lib.hb_buffer_guess_segment_properties(buf)

        # Set text direction (LTR, RTL, etc.).
        hb_lib.hb_buffer_set_direction(buf, direction)

        # Perform shaping.
        hb_lib.hb_shape(self.font, buf, None, 0)

        # Retrieve the number of glyphs.
        length = hb_lib.hb_buffer_get_length(buf)

        # Get pointers to the glyph info and position arrays.
        infos = hb_lib.hb_buffer_get_glyph_infos(buf, None)
        positions = hb_lib.hb_buffer_get_glyph_positions(buf, None)

        # Collect glyph metrics.
        glyphs = []
        for i in range(length):
            info = infos[i]
            pos = positions[i]
            glyphs.append({
                "codepoint": info.codepoint,
                "cluster": info.cluster,
                "x_advance": pos.x_advance / 64.0,
                "y_advance": pos.y_advance / 64.0,
                "x_offset": pos.x_offset / 64.0,
                "y_offset": pos.y_offset / 64.0,
            })

        # Clean up the buffer.
        hb_lib.hb_buffer_destroy(buf)

        return glyphs

    def __del__(self):
        self.destroy()

    def destroy(self):
        if self.font:
            hb_lib.hb_font_destroy(self.font)
            self.font = None

        if self.face:
            hb_lib.hb_face_destroy(self.face)
            self.face = None

        if self.blob:
            hb_lib.hb_blob_destroy(self.blob)
            self.blob = None
