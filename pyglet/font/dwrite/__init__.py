from __future__ import annotations

import copy
import ctypes
import math
import pathlib
from ctypes.wintypes import WCHAR, BOOL, FLOAT, UINT
from typing import NoReturn, BinaryIO, Any

from _ctypes import POINTER, pointer, sizeof, byref, Array
from ctypes import c_wchar_p, c_void_p, c_ubyte, cast, c_uint32, create_unicode_buffer, c_wchar

from enum import Flag

import pyglet
from pyglet.font import base
from pyglet.font.base import Glyph, GlyphPosition
from pyglet.font.dwrite.dwrite_lib import DWRITE_FONT_WEIGHT_NORMAL, DWRITE_FONT_WEIGHT_BOLD, \
    DWRITE_FONT_STRETCH_CONDENSED, \
    DWRITE_SCRIPT_ANALYSIS, IDWriteFontFileStream, IDWriteFontFile, IDWriteFactory, IDWriteFontFileEnumerator, \
    IDWriteTextAnalyzer, DWRITE_GLYPH_OFFSET, IDWriteFontFace, DWRITE_GLYPH_RUN, IDWriteColorGlyphRunEnumerator1, \
    IDWriteColorGlyphRunEnumerator, DWRITE_TEXT_METRICS, \
    D2D_POINT_2F, DWRITE_FONT_STYLE_ITALIC, DWRITE_FONT_STYLE_NORMAL, \
    DWRITE_FONT_STRETCH_EXPANDED, DWRITE_FONT_STRETCH_NORMAL, IDWriteFont, IDWriteTextLayout, IDWriteFontFileLoader_LI, \
    IDWriteFontCollection1, IDWriteFontCollection, IDWriteLocalizedStrings, D2D1_COLOR_F, TextAnalysis, \
    LegacyFontFileLoader, LegacyCollectionLoader, DWRITE_TEXT_RANGE, IDWriteTextRenderer, \
    DWRITE_MATRIX, DWRITE_GLYPH_RUN_DESCRIPTION, DWRITE_GLYPH_IMAGE_FORMATS_ALL
from pyglet.font.dwrite.d2d1_lib import D2D1_TEXT_ANTIALIAS_MODE_DEFAULT, D2D1_TEXT_ANTIALIAS_MODE_ALIASED, \
    D2D1_DRAW_TEXT_OPTIONS_ENABLE_COLOR_FONT, D2D1_DRAW_TEXT_OPTIONS_NONE, ID2D1RenderTarget, default_target_properties, \
    ID2D1SolidColorBrush, ID2D1DeviceContext4, IID_ID2D1DeviceContext4, ID2D1Factory, D2D1CreateFactory, \
    D2D1_FACTORY_TYPE_SINGLE_THREADED, IID_ID2D1Factory
from pyglet.font.dwrite.d2d1_types_lib import D2D_POINT_2F, D2D1_COLOR_F
from pyglet.font.dwrite.dwrite_lib import DWRITE_FONT_WEIGHT_BOLD, DWRITE_FONT_WEIGHT_NORMAL, DWRITE_FONT_WEIGHT_THIN, \
    DWRITE_FONT_WEIGHT_EXTRA_LIGHT, DWRITE_FONT_WEIGHT_ULTRA_LIGHT, DWRITE_FONT_WEIGHT_LIGHT, \
    DWRITE_FONT_WEIGHT_SEMI_LIGHT, DWRITE_FONT_WEIGHT_REGULAR, DWRITE_FONT_WEIGHT_MEDIUM, DWRITE_FONT_WEIGHT_DEMI_BOLD, \
    DWRITE_FONT_WEIGHT_SEMI_BOLD, DWRITE_FONT_WEIGHT_EXTRA_BOLD, DWRITE_FONT_WEIGHT_ULTRA_BOLD, \
    DWRITE_FONT_WEIGHT_BLACK, DWRITE_FONT_WEIGHT_HEAVY, DWRITE_FONT_WEIGHT_EXTRA_BLACK, DWRITE_FONT_STRETCH_UNDEFINED, \
    DWRITE_FONT_STRETCH_ULTRA_CONDENSED, DWRITE_FONT_STRETCH_EXTRA_CONDENSED, DWRITE_FONT_STRETCH_CONDENSED, \
    DWRITE_FONT_STRETCH_SEMI_CONDENSED, DWRITE_FONT_STRETCH_NORMAL, DWRITE_FONT_STRETCH_MEDIUM, \
    DWRITE_FONT_STRETCH_SEMI_EXPANDED, DWRITE_FONT_STRETCH_EXPANDED, DWRITE_FONT_STRETCH_EXTRA_EXPANDED, \
    DWRITE_FONT_STYLE_NORMAL, DWRITE_FONT_STYLE_OBLIQUE, DWRITE_FONT_STYLE_ITALIC, DWRITE_SCRIPT_ANALYSIS, \
    IDWriteTextAnalysisSource, IDWriteTextAnalysisSink, IDWriteTextAnalyzer, IDWriteFontFileStream, \
    IDWriteFontFileLoader_LI, IDWriteFontFileEnumerator, IDWriteFactory, IDWriteFontFile, IDWriteFontCollectionLoader, \
    DWRITE_MEASURING_MODE_NATURAL, IDWriteTextLayout, DWRITE_TEXT_METRICS, IDWriteFontFace, DWRITE_GLYPH_OFFSET, \
    DWRITE_SHAPING_TEXT_PROPERTIES, DWRITE_SHAPING_GLYPH_PROPERTIES, DWRITE_GLYPH_METRICS, DWRITE_GLYPH_RUN, \
    IDWriteColorGlyphRunEnumerator, IDWriteColorGlyphRunEnumerator1, DWRITE_COLOR_GLYPH_RUN1, DWRITE_NO_PALETTE_INDEX, \
    DWRITE_GLYPH_IMAGE_FORMATS_SVG, DWRITE_GLYPH_IMAGE_FORMATS_BITMAP, IDWriteFontFamily1, IDWriteFont, \
    IDWriteTextFormat, IDWriteFontFace4, IID_IDWriteFontFace4, IDWriteFontFace2, IID_IDWriteFontFace2, \
    DWRITE_FONT_METRICS, IDWriteFontFallback, IDWriteFontFileLoader, IDWriteLocalFontFileLoader, \
    IID_IDWriteLocalFontFileLoader, DWRITE_CLUSTER_METRICS, IDWriteFactory7, IID_IDWriteFactory7, IDWriteFactory5, \
    IID_IDWriteFactory5, IDWriteFactory2, IID_IDWriteFactory2, IID_IDWriteFactory, DWriteCreateFactory, \
    DWRITE_FACTORY_TYPE_SHARED, IDWriteInMemoryFontFileLoader, IDWriteFontSetBuilder1, IDWriteFontSet, \
    IDWriteFontCollection1, IDWriteFontCollection, IDWriteFontFamily, IDWriteLocalizedStrings, \
    DWRITE_INFORMATIONAL_STRING_WIN32_FAMILY_NAMES
from pyglet.image import ImageData
from pyglet.image.codecs.wincodec_lib import IWICBitmap, GUID_WICPixelFormat32bppPBGRA, WICBitmapCacheOnDemand
from pyglet.libs.win32 import com, UINT32, UINT64, _kernel32 as kernel32, UINT16
from pyglet.libs.win32.constants import LOCALE_NAME_MAX_LENGTH, WINDOWS_8_1_OR_GREATER, \
    WINDOWS_10_CREATORS_UPDATE_OR_GREATER, WINDOWS_10_1809_OR_GREATER
from pyglet.util import debug_print

_debug_font = pyglet.options["debug_font"]
_debug_print = debug_print("debug_font")

try:
    from pyglet.image.codecs import wic
except ImportError as err:
    msg = "Failed to initialize Windows Imaging Component module."
    raise ImportError(msg) from err


name_to_weight = {
    True: DWRITE_FONT_WEIGHT_BOLD,      # Temporary alias for attributed text
    False: DWRITE_FONT_WEIGHT_NORMAL,   # Temporary alias for attributed text
    None: DWRITE_FONT_WEIGHT_NORMAL,    # Temporary alias for attributed text
    "thin": DWRITE_FONT_WEIGHT_THIN,
    "extralight": DWRITE_FONT_WEIGHT_EXTRA_LIGHT,
    "ultralight": DWRITE_FONT_WEIGHT_ULTRA_LIGHT,
    "light": DWRITE_FONT_WEIGHT_LIGHT,
    "semilight": DWRITE_FONT_WEIGHT_SEMI_LIGHT,
    "normal": DWRITE_FONT_WEIGHT_NORMAL,
    "regular": DWRITE_FONT_WEIGHT_REGULAR,
    "medium": DWRITE_FONT_WEIGHT_MEDIUM,
    "demibold": DWRITE_FONT_WEIGHT_DEMI_BOLD,
    "semibold": DWRITE_FONT_WEIGHT_SEMI_BOLD,
    "bold": DWRITE_FONT_WEIGHT_BOLD,
    "extrabold": DWRITE_FONT_WEIGHT_EXTRA_BOLD,
    "ultrabold": DWRITE_FONT_WEIGHT_ULTRA_BOLD,
    "black": DWRITE_FONT_WEIGHT_BLACK,
    "heavy": DWRITE_FONT_WEIGHT_HEAVY,
    "extrablack": DWRITE_FONT_WEIGHT_EXTRA_BLACK,
}
name_to_stretch = {
    "undefined": DWRITE_FONT_STRETCH_UNDEFINED,
    "ultracondensed": DWRITE_FONT_STRETCH_ULTRA_CONDENSED,
    "extracondensed": DWRITE_FONT_STRETCH_EXTRA_CONDENSED,
    "condensed": DWRITE_FONT_STRETCH_CONDENSED,
    "semicondensed": DWRITE_FONT_STRETCH_SEMI_CONDENSED,
    "normal": DWRITE_FONT_STRETCH_NORMAL,
    "medium": DWRITE_FONT_STRETCH_MEDIUM,
    "semiexpanded": DWRITE_FONT_STRETCH_SEMI_EXPANDED,
    "expanded": DWRITE_FONT_STRETCH_EXPANDED,
    "extraexpanded": DWRITE_FONT_STRETCH_EXTRA_EXPANDED,
    "narrow": DWRITE_FONT_STRETCH_CONDENSED,
}
name_to_style = {
    "normal": DWRITE_FONT_STYLE_NORMAL,
    "oblique": DWRITE_FONT_STYLE_OBLIQUE,
    "italic": DWRITE_FONT_STYLE_ITALIC,
}


class DWRITE_GLYPH_IMAGE_FORMAT_FLAG(Flag):
    NONE = 0x00000000
    TRUETYPE = 0x00000001
    CFF = 0x00000002
    COLR = 0x00000004
    SVG = 0x00000008
    PNG = 0x00000010
    JPEG = 0x00000020
    TIFF = 0x00000040
    PREMULTIPLIED_B8G8R8A8 = 0x00000080
    COLR_PAINT_TREE = 0x00000100





def get_clusters(text: str) -> list[int]:
    """
    Computes the clusters (pre-shaped) for a string,
    i.e. the starting UTF-16 code unit index for each character.
    """
    clusters = []
    index = 0
    for char in text:
        clusters.append(index)
        # Characters outside the BMP are surrogate pairs (2 code units)
        if ord(char) > 0xFFFF:
            index += 2
        else:
            index += 1
    return clusters


def get_utf16_indice(text):
    """Computes UTF-16 logical cluster indices for each character in `text`."""
    utf16_indices = []
    utf16_pos = 0

    for char in text:
        codepoint = ord(char)
        utf16_indices.append(utf16_pos)

        if 0xD800 <= codepoint <= 0xDFFF:  # Surrogate range (shouldn't appear in input)
            raise ValueError(f"Unexpected surrogate character: U+{codepoint:X}")

        if codepoint > 0x10FFFF:  # Replace invalid Unicode characters
            utf16_pos += 1  # U+FFFD is a single UTF-16 code unit
        elif codepoint >= 0x10000:
            utf16_pos += 2  # Surrogate pair
        else:
            utf16_pos += 1  # Single UTF-16 code unit

    print("SIZE", len(utf16_indices))
    return utf16_indices


def get_logical_clusters(text: str):
    """Get logical cluster"""
    clusters = []
    sizes = []
    char_pos = 0
    for i, char in enumerate(text):
        codepoint = ord(char)
        clusters.append(char_pos)

        char_pos += 1
        size = 1

        if 0x10000 <= codepoint <= 0x10FFFF:
            char_pos += 1
            size += 1
        sizes.append(size)

    return clusters, sizes


def compute_insertion_indices(pre_clusters, post_clusters):
    """
    Determine the indices in the pre-shape (original character order) where the zero-width
    glyphs need to be inserted.
      1. Finding all positions where the pre-shape cluster is missing from the post-shape clusters.
      2. Grouping consecutive missing indices (from post shape)
      3. From each group, selecting every other index (starting with the first) to serve as
         the insertion point.
    """
    # Find indices where the pre-shape cluster doesn't appear in the post-shape clusters.
    missing_indices = [
        i for i, cl in enumerate(pre_clusters)
        if cl not in post_clusters
    ]

    # Group the missing indices into consecutive groups.
    groups = []
    current = []
    for i in missing_indices:
        if not current or i == current[-1] + 1:
            current.append(i)
        else:
            groups.append(current)
            current = [i]
    if current:
        groups.append(current)

    # For each group, select every other index (starting with the first)
    insertion_indices = []
    for group in groups:
        insertion_indices.extend(group[::2])
    return insertion_indices


def get_system_locale() -> str:
    """Retrieve the string representing the system locale."""
    local_name = create_unicode_buffer(LOCALE_NAME_MAX_LENGTH)
    kernel32.GetUserDefaultLocaleName(local_name, LOCALE_NAME_MAX_LENGTH)
    return local_name.value


class _DWriteTextRenderer(com.COMObject):
    """This implements a custom renderer for IDWriteTextLayout.

    This allows the use of DirectWrite shaping to offload manual shaping, fallback detection, glyph combining, and
    other complicated scenarios.
    """
    _interfaces_ = [IDWriteTextRenderer]

    def __init__(self) -> None:
        super().__init__()
        self.pixel_snapping = False
        self.pixels_per_dip = 1.0
        self.dmatrix = DWRITE_MATRIX()

    def _get_font_reference(self, font_face: IDWriteFontFace) -> tuple[c_void_p, int]:
        """Unique identifier for each font face."""
        font_file = _get_font_file(font_face)
        return _get_font_ref(font_file, release_file=True)

    def DrawUnderline(self, *_args) -> int:  # noqa: ANN002, N802
        return com.E_NOTIMPL

    def DrawStrikethrough(self, *_args)-> int:  # noqa: ANN002, N802
        return com.E_NOTIMPL

    def DrawInlineObject(self, *_args) -> int:  # noqa: ANN002, N802
        return com.E_NOTIMPL

    def IsPixelSnappingDisabled(self, _draw_ctx: c_void_p, is_disabled: POINTER(FLOAT)) -> int:
        is_disabled[0] = self.pixel_snapping
        return 0

    def GetPixelsPerDip(self, _draw_ctx: c_void_p, pixels_per_dip: POINTER(FLOAT)) -> int:
        pixels_per_dip[0] = self.pixels_per_dip
        return 0

    def GetCurrentTransform(self, _draw_ctx: c_void_p, transform: POINTER(DWRITE_MATRIX)) -> int:
        transform[0] = self.dmatrix
        return 0

    def DrawGlyphRun(self, drawing_context: c_void_p,
                     _baseline_x: float, _baseline_y: float, mode: int,
                     glyph_run_ptr: POINTER(DWRITE_GLYPH_RUN),
                     _run_des: POINTER(DWRITE_GLYPH_RUN_DESCRIPTION),
                     _effect: c_void_p) -> int:
        glyph_renderer: DirectWriteGlyphRenderer = ctypes.cast(drawing_context, ctypes.py_object).value
        glyph_run = glyph_run_ptr.contents

        # Process any glyphs we haven't rendered.
        missing = []
        for i in range(glyph_run.glyphCount):
            glyph_indice = glyph_run.glyphIndices[i]
            if glyph_indice not in glyph_renderer.font.glyphs:
                missing.append(glyph_indice)

        # Missing glyphs, get their info.
        if missing:
            metrics = get_glyph_metrics(glyph_run.fontFace, (UINT16 * len(missing))(*missing), len(missing))

            for idx, glyph_indice in enumerate(missing):
                glyph = glyph_renderer.render_single_glyph(glyph_run.fontFace, glyph_indice, metrics[idx], mode)
                glyph.base_advance = metrics[idx][3] * glyph_renderer.font.font_scale_ratio
                glyph_renderer.font.glyphs[glyph_indice] = glyph

        # Process and create glyphs for run.
        for i in range(glyph_run.glyphCount):
            glyph_indice = glyph_run.glyphIndices[i]
            glyph = glyph_renderer.font.glyphs[glyph_indice]
            offset = base.GlyphPosition(
                        (glyph_run.glyphAdvances[i] - glyph.base_advance),
                        0,
                        glyph_run.glyphOffsets[i].advanceOffset,
                        glyph_run.glyphOffsets[i].ascenderOffset
            )
            glyph_renderer.current_glyphs.append(glyph)
            glyph_renderer.current_offsets.append(offset)

        return 0


_renderer = _DWriteTextRenderer()

def get_glyph_metrics(font_face: IDWriteFontFace, indices: Array[UINT16], count: int) -> list[
        tuple[float, float, float, float, float]]:
        """Obtain metrics for the specific string.

        Returns:
            A list of tuples with the following metrics per indice:
        .       (glyph width, glyph height, left side bearing, advance width, bottom side bearing)
        """
        glyph_metrics = (DWRITE_GLYPH_METRICS * count)()
        font_face.GetDesignGlyphMetrics(indices, count, glyph_metrics, False)

        metrics_out = []
        for metric in glyph_metrics:
            glyph_width = (metric.advanceWidth + abs(metric.leftSideBearing) + abs(metric.rightSideBearing))
            glyph_height = (metric.advanceHeight - metric.topSideBearing - metric.bottomSideBearing)

            lsb = metric.leftSideBearing
            bsb = metric.bottomSideBearing

            advance_width = metric.advanceWidth

            metrics_out.append((glyph_width, glyph_height, lsb, advance_width, bsb))

        return metrics_out

class DirectWriteGlyphRenderer(base.GlyphRenderer):
    current_run: list[DWRITE_GLYPH_RUN]
    font: Win32DirectWriteFont
    antialias_mode = D2D1_TEXT_ANTIALIAS_MODE_DEFAULT if pyglet.options.text_antialiasing is True else D2D1_TEXT_ANTIALIAS_MODE_ALIASED
    draw_options = D2D1_DRAW_TEXT_OPTIONS_ENABLE_COLOR_FONT if WINDOWS_8_1_OR_GREATER else D2D1_DRAW_TEXT_OPTIONS_NONE
    measuring_mode = DWRITE_MEASURING_MODE_NATURAL

    def __init__(self, font: Win32DirectWriteFont) -> None:  # noqa: D107
        self._render_target = None
        self._ctx_supported = False
        self._bitmap = None
        self._brush = None
        self._bitmap_dimensions = (0, 0)
        self.current_glyphs = []
        self.current_offsets = []
        super().__init__(font)
        self.font = font

    def render(self, text: str) -> Glyph:
        pass

    def render_to_image(self, text: str, width: int, height: int) -> ImageData:
        """This process takes Pyglet out of the equation and uses only DirectWrite to shape and render text.

        This may allows more accurate fonts (bidi, rtl, etc) in very special circumstances.
        """
        raise Exception
        text_buffer = create_unicode_buffer(text)

        text_layout = IDWriteTextLayout()
        self.font._write_factory.CreateTextLayout(
            text_buffer,
            len(text_buffer),
            self.font._text_format,
            width,  # Doesn't affect bitmap size.
            height,
            byref(text_layout),
        )

        layout_metrics = DWRITE_TEXT_METRICS()
        text_layout.GetMetrics(byref(layout_metrics))

        width, height = int(math.ceil(layout_metrics.width)), int(math.ceil(layout_metrics.height))

        wic_fmt = GUID_WICPixelFormat32bppPBGRA
        bitmap = wic.get_bitmap(width, height, wic_fmt)

        rt = ID2D1RenderTarget()
        d2d_factory.CreateWicBitmapRenderTarget(bitmap, default_target_properties, byref(rt))

        # Font aliasing rendering quality.
        rt.SetTextAntialiasMode(self.antialias_mode)

        if not self._brush:
            self._brush = ID2D1SolidColorBrush()

        rt.CreateSolidColorBrush(white, None, byref(self._brush))

        rt.BeginDraw()

        rt.Clear(transparent)

        rt.DrawTextLayout(no_offset,
                          text_layout,
                          self._brush,
                          self.draw_options)

        rt.EndDraw(None, None)

        rt.Release()

        return wic.extract_image_data(bitmap, wic_fmt)

    def render_single_glyph(self, font_face: IDWriteFontFace, indice: int,
                            metrics: tuple[float, float, float, float, float],
                            mode: int) -> base.Glyph:
        """Renders a single glyph indice using Direct2D."""
        glyph_width, glyph_height, glyph_lsb, glyph_advance, glyph_bsb = metrics

        offset = DWRITE_GLYPH_OFFSET(0.0, 0.0)

        run = DWRITE_GLYPH_RUN(
            fontFace=font_face,
            fontEmSize=self.font._real_size,
            glyphCount=1,
            glyphIndices=(UINT16 * 1)(indice),  # indice,
            glyphAdvances=(FLOAT * 1)(0.0),  # advance,
            glyphOffsets=pointer(offset),  # offset,
            isSideways=False,
            bidiLevel=0,
        )

        # If color drawing is enabled, get a color enumerator.
        if self.draw_options & D2D1_DRAW_TEXT_OPTIONS_ENABLE_COLOR_FONT:
            enumerator = self._get_color_enumerator(run)
        else:
            enumerator = None

        # Use the glyph's advance as a width as bitmap width.
        # Some characters have no glyph width at all, just use a 1x1
        if glyph_width == 0 and glyph_height == 0:
            render_width = 1
            render_height = 1
        else:
            # Use the glyph width, or if the advance is larger, use that instead.
            # Diacritics usually have no proper sizing, but instead have an advance.
            render_width = int(math.ceil(max(glyph_width, glyph_advance) * self.font.font_scale_ratio))
            render_height = int(math.ceil(self.font.max_glyph_height))

        render_offset_x = 0
        if glyph_lsb < 0:
            # Negative LSB: we shift the offset, otherwise the glyph will be cut off.
            render_offset_x = glyph_lsb * self.font.font_scale_ratio

        # Create new bitmap.
        # TODO: We can probably adjust bitmap/baseline to reduce the whitespace and save a lot of texture space.
        # Note: Floating point precision makes this a giant headache, will need to be solved for this approach.
        self._create_bitmap(render_width + 1,  # Add 1, sometimes AA can add an extra pixel or so.
                            render_height + 1)

        # Glyphs are drawn at the baseline, and with LSB, so we need to offset it based on top left position.
        baseline_offset = D2D_POINT_2F(-render_offset_x,
                                       self.font.ascent)

        self._render_target.BeginDraw()

        self._render_target.Clear(transparent)

        if enumerator:
            temp_brush: None | ID2D1SolidColorBrush = None
            while True:
                has_run = BOOL(True)
                enumerator.MoveNext(byref(has_run))
                if not has_run.value:
                    break

                color_run = POINTER(DWRITE_COLOR_GLYPH_RUN1)()
                enumerator.GetCurrentRun1(byref(color_run))

                # Uses current color.
                if color_run.contents.paletteIndex == DWRITE_NO_PALETTE_INDEX:
                    brush = self._brush
                else:
                    # Need a temp brush for separate colors.
                    if not temp_brush:
                        temp_brush = ID2D1SolidColorBrush()
                        self._render_target.CreateSolidColorBrush(color_run.contents.runColor, None, byref(temp_brush))
                    else:
                        temp_brush.SetColor(color_run.contents.runColor)
                    brush = temp_brush

                glyph_image_fmt = color_run.contents.glyphImageFormat
                if glyph_image_fmt == DWRITE_GLYPH_IMAGE_FORMATS_SVG:
                    if self._ctx_supported:
                        self._render_target.DrawSvgGlyphRun(
                            baseline_offset,
                            color_run.contents.glyphRun,
                            self._brush,
                            None,
                            0,
                            mode
                        )
                elif glyph_image_fmt & DWRITE_GLYPH_IMAGE_FORMATS_BITMAP:
                    if self._ctx_supported:
                        self._render_target.DrawColorBitmapGlyphRun(
                            glyph_image_fmt,
                            baseline_offset,
                            color_run.contents.glyphRun,
                            self.measuring_mode
                    )
                else:
                    glyph_run = color_run.contents.glyphRun
                    self._render_target.DrawGlyphRun(baseline_offset,
                                                     glyph_run,
                                                     brush,
                                                     mode)
            enumerator.Release()
            if temp_brush:
                temp_brush.Release()
        else:
            self._render_target.DrawGlyphRun(baseline_offset,
                                             run,
                                             self._brush,
                                             mode)

        self._render_target.EndDraw(None, None)

        image = wic.extract_image_data(self._bitmap)

        glyph = self.font.create_glyph(image)

        glyph.set_bearings(-self.font.descent, render_offset_x,
                           glyph_advance * self.font.font_scale_ratio)

        return glyph

    def _get_color_enumerator(self, dwrite_run: DWRITE_GLYPH_RUN) -> IDWriteColorGlyphRunEnumerator | IDWriteColorGlyphRunEnumerator1 | None:
        """Obtain a color enumerator if possible."""
        try:
            if WINDOWS_10_CREATORS_UPDATE_OR_GREATER:
                enumerator = IDWriteColorGlyphRunEnumerator1()

                self.font._write_factory.TranslateColorGlyphRun4(
                    no_offset,
                    dwrite_run,
                    None,
                    DWRITE_GLYPH_IMAGE_FORMATS_ALL,
                    self.measuring_mode,
                    None,
                    0,
                    byref(enumerator),
                )
            elif WINDOWS_8_1_OR_GREATER:
                enumerator = IDWriteColorGlyphRunEnumerator()
                self.font._write_factory.TranslateColorGlyphRun(
                    0.0, 0.0,
                    dwrite_run,
                    None,
                    self.measuring_mode,
                    None,
                    0,
                    byref(enumerator),
                )
            else:
                return None

            return enumerator
        except OSError as dw_err:
            # HRESULT returns -2003283956 (DWRITE_E_NOCOLOR) if no color run is detected. Anything else is unexpected.
            if dw_err.winerror != -2003283956:
                raise dw_err

        return None

    def render_using_layout(self, text: str) -> Glyph | None:
        """This will render text given the built-in DirectWrite layout.

        This process allows us to take advantage of color glyphs and fallback handling that is built into DirectWrite.
        This can also handle shaping and many other features if you want to render directly to a texture.
        """
        text_layout = self.font.create_text_layout(text)

        layout_metrics = DWRITE_TEXT_METRICS()
        text_layout.GetMetrics(byref(layout_metrics))

        width = int(math.ceil(layout_metrics.width))
        height = int(math.ceil(layout_metrics.height))

        if width == 0 or height == 0:
            return None

        self._create_bitmap(width, height)

        # This offsets the characters if needed.
        point = D2D_POINT_2F(0, 0)

        self._render_target.BeginDraw()

        self._render_target.Clear(transparent)

        self._render_target.DrawTextLayout(point,
                                           text_layout,
                                           self._brush,
                                           self.draw_options)

        self._render_target.EndDraw(None, None)

        image = wic.extract_image_data(self._bitmap)

        glyph = self.font.create_glyph(image)
        glyph.set_bearings(-self.font.descent, 0, int(math.ceil(layout_metrics.width)))
        return glyph

    def _create_bitmap(self, width: int, height: int) -> None:
        """Creates a bitmap using Direct2D and WIC."""
        # Create a new bitmap, try to re-use the bitmap as much as we can to minimize creations.
        if self._bitmap_dimensions[0] != width or self._bitmap_dimensions[1] != height:
            # If dimensions aren't the same, release bitmap to create new ones.
            if self._render_target:
                self._render_target.Release()

            self._bitmap = wic.get_bitmap(width, height, GUID_WICPixelFormat32bppPBGRA)

            _render_target = ID2D1RenderTarget()
            d2d_factory.CreateWicBitmapRenderTarget(self._bitmap, default_target_properties, byref(_render_target))

            # Allows drawing SVG/Bitmap glyphs. Check if supported.
            dev_ctx = ID2D1DeviceContext4()
            if com.is_available(_render_target, IID_ID2D1DeviceContext4, dev_ctx):
                _render_target.Release()  # Release original.
                self._render_target = dev_ctx
                self._ctx_supported = True
            else:
                self._render_target = _render_target

            # Font aliasing rendering quality.
            self._render_target.SetTextAntialiasMode(self.antialias_mode)

            if not self._brush:
                self._brush = ID2D1SolidColorBrush()
                self._render_target.CreateSolidColorBrush(white, None, byref(self._brush))


def _get_font_file(font_face: IDWriteFontFace) -> IDWriteFontFile:
    """Get the font file associated with this face.

    Seems to give something, even for memory loaded fonts.

    .. note:: Caller is responsible for freeing the returned object.
    """
    file_ct = UINT32()
    font_face.GetFiles(byref(file_ct), None)

    font_files = (IDWriteFontFile * file_ct.value)()
    font_face.GetFiles(byref(file_ct), font_files)

    return font_files[font_face.GetIndex()]

def _get_font_ref(font_file: IDWriteFontFile, release_file: bool=True) -> tuple[c_void_p, int]:
    """Get a unique font reference for the font face.

    Callbacks will generate new addresses for the same IDWriteFontFace, so a unique value
    needs to be established to cache glyphs.

    Args:
        font_file:
            The target font file object to pull the unique key from.
        release_file:
            If ``True`` the font file will be released.
    """
    key_data = c_void_p()
    ff_key_size = UINT32()

    font_file.GetReferenceKey(byref(key_data), byref(ff_key_size))
    if release_file:
        font_file.Release()

    return key_data, ff_key_size.value


class Win32DirectWriteFont(base.Font):
    """DirectWrite Font object for Windows 7+."""
    # To load fonts from files, we need to produce a custom collection.
    _custom_collection = None

    # Shared loader values
    _write_factory = None  # Factory required to run any DirectWrite interfaces.
    _font_loader = None

    # Windows 10 loader values.
    _font_builder = None
    _font_set = None

    # Legacy loader values
    _font_collection_loader = None
    _font_cache = []
    _font_loader_key = None

    _default_name = "Segoe UI"  # Default font for Windows 7+

    _glyph_renderer = None
    _empty_glyph = None
    _zero_glyph = None

    glyph_renderer_class = DirectWriteGlyphRenderer
    texture_internalformat = pyglet.gl.GL_RGBA

    def __init__(self, name: str, size: float, weight: str = "normal", italic: bool | str = False,  # noqa: D107
                 stretch: bool | str = False, dpi: int | None = None, locale: str | None = None) -> None:
        self._filename: str | None = None

        super().__init__()

        if not name:
            name = self._default_name

        self._name = name
        self.weight = weight
        self.size = size
        self.italic = italic
        self.stretch = stretch
        self.dpi = dpi
        self.locale = locale

        if self.locale is None:
            self.locale = ""
            self.rtl = False  # Right to left should be handled by pyglet?
            # TODO: Use system locale string?

        if self.dpi is None:
            self.dpi = 96

        # From DPI to DIP (Device Independent Pixels) which is what the fonts rely on.
        self._real_size = (self.size * self.dpi) // 72

        self._weight = name_to_weight[self.weight]

        if self.italic:
            if isinstance(self.italic, str):
                self._style = name_to_style[self.italic]
            else:
                self._style = DWRITE_FONT_STYLE_ITALIC
        else:
            self._style = DWRITE_FONT_STYLE_NORMAL

        if self.stretch:
            if isinstance(self.stretch, str):
                self._stretch = name_to_stretch[self.stretch]
            else:
                self._stretch = DWRITE_FONT_STRETCH_EXPANDED
        else:
            self._stretch = DWRITE_FONT_STRETCH_NORMAL

        self._font_index, self._collection = self.get_collection(name)
        write_font = None
        # If not font found, search all collections for legacy GDI naming.
        if pyglet.options["dw_legacy_naming"] and (self._font_index is None and self._collection is None):
            write_font, self._collection = self.find_font_face(name, self._weight, self._style, self._stretch)

        assert self._collection is not None, f"Font: '{name}' not found in loaded or system font collection."

        if self._font_index is not None:
            font_family = IDWriteFontFamily1()
            self._collection.GetFontFamily(self._font_index, byref(font_family))

            write_font = IDWriteFont()
            font_family.GetFirstMatchingFont(
                self._weight,
                self._stretch,
                self._style,
                byref(write_font),
            )

        # Create the text format this font will use permanently.
        # Could technically be recreated, but will keep to be inline with other font objects.
        self._text_format = IDWriteTextFormat()
        self._write_factory.CreateTextFormat(
            self._name,
            self._collection,
            self._weight,
            self._style,
            self._stretch,
            self._real_size,
            create_unicode_buffer(self.locale),
            byref(self._text_format),
        )

        font_face = IDWriteFontFace()
        write_font.CreateFontFace(byref(font_face))

        # font_face4 = IDWriteFontFace4()
        # if com.is_available(font_face, IID_IDWriteFontFace4, font_face4):
        #     font_face = font_face4
        # else:
        #     font_face2 = IDWriteFontFace2()
        #     if com.is_available(font_face, IID_IDWriteFontFace2, font_face2):
        #         font_face = font_face2

        self.font_face = font_face
        self._font_metrics = DWRITE_FONT_METRICS()
        self.font_face.GetMetrics(byref(self._font_metrics))

        self.font_scale_ratio = (self._real_size / self._font_metrics.designUnitsPerEm)

        self.ascent = math.ceil(self._font_metrics.ascent * self.font_scale_ratio)
        self.descent = -round(self._font_metrics.descent * self.font_scale_ratio)
        self.max_glyph_height = (self._font_metrics.ascent + self._font_metrics.descent) * self.font_scale_ratio

        self.line_gap = self._font_metrics.lineGap * self.font_scale_ratio

    @property
    def filename(self) -> str:
        """Returns a filename associated with the font face.

        Note: Capable of returning more than 1 file in the future, but will do just one for now.
        """
        if self._filename is not None:
            return self._filename

        self._filename = "Not Available"

        font_file = _get_font_file(self.font_face)
        key_data, key_size = _get_font_ref(font_file, release_file=False)

        loader = IDWriteFontFileLoader()
        font_file.GetLoader(byref(loader))

        try:
            local_loader = IDWriteLocalFontFileLoader()
            loader.QueryInterface(IID_IDWriteLocalFontFileLoader, byref(local_loader))
        except OSError as e:
            int_error = e.winerror & 0xFFFFFFFF
            if int_error == com.E_NOTIMPL or int_error == com.E_NOINTERFACE:
                loader.Release()
                font_file.Release()
            else:
                raise e
            return self._filename

        path_len = UINT32()
        local_loader.GetFilePathLengthFromKey(key_data, key_size, byref(path_len))

        buffer = create_unicode_buffer(path_len.value + 1)
        local_loader.GetFilePathFromKey(key_data, key_size, buffer, len(buffer))

        loader.Release()
        local_loader.Release()
        font_file.Release()

        self._filename = pathlib.PureWindowsPath(buffer.value).as_posix()  # Convert to forward slashes.
        return self._filename

    @property
    def name(self) -> str:
        return self._name

    def render_to_image(self, text: str, width: int=10000, height: int=80) -> ImageData:
        """This process takes Pyglet out of the equation and uses only DirectWrite to shape and render text.
        This may allow more accurate fonts (bidi, rtl, etc) in very special circumstances at the cost of
        additional texture space.
        """
        if not self._glyph_renderer:
            self._glyph_renderer = self.glyph_renderer_class(self)

        return self._glyph_renderer.render_to_image(text, width, height)


    def get_glyphs_no_shape(self, text: str) -> list[Glyph]:
        """This differs in that it does not attempt to shape the text at all.

        May be useful in cases where your font has no special shaping requirements, spacing is the same, or some other
        reason where faster performance is wanted and you can get away with this.
        """
        if not self._glyph_renderer:
            self._glyph_renderer = self.glyph_renderer_class(self)
            self._empty_glyph = self._glyph_renderer.render_using_layout(" ")

        glyphs = []
        for c in text:
            if c == "\t":
                c = " "

            if c not in self.glyphs:
                self.glyphs[c] = self._glyph_renderer.render_using_layout(c)
                if not self.glyphs[c]:
                    self.glyphs[c] = self._empty_glyph

            glyphs.append(self.glyphs[c])

        return glyphs


    def get_glyphs(self, text: str) -> tuple[list[Glyph], list[base.GlyphPosition]]:
        if not self._glyph_renderer:
            self._glyph_renderer = self.glyph_renderer_class(self)
            #self._empty_glyph = self._glyph_renderer.render_using_layout(" ")
            self._zero_glyph = self._glyph_renderer.create_zero_glyph()

        text_layout = self.create_text_layout(text)

        self._glyph_renderer.current_glyphs.clear()
        self._glyph_renderer.current_offsets.clear()

        ptr = ctypes.cast(id(self._glyph_renderer), ctypes.c_void_p)
        text_layout.Draw(ptr, _renderer.as_interface(IDWriteTextRenderer), 0, 0)
        text_layout.Release()

        return self._glyph_renderer.current_glyphs, self._glyph_renderer.current_offsets

    def create_text_layout(self, text: str) -> IDWriteTextLayout:
        """Create a text layout that holds the specified text.

        .. note:: Caller is responsible for calling ``Release`` when finished.
        """
        text_buffer = create_unicode_buffer(text)

        text_layout = IDWriteTextLayout()
        hr = self._write_factory.CreateTextLayout(
            text_buffer, len(text_buffer), self._text_format,
            10000, 80, # Doesn't affect glyph, bitmap size.
            byref(text_layout),
        )

        return text_layout

    @classmethod
    def _initialize_direct_write(cls: type[Win32DirectWriteFont]) -> None:
        """All DirectWrite fonts needs factory access as well as the loaders."""
        if WINDOWS_10_1809_OR_GREATER:  # Added Bitmap based image glyphs.
            cls._write_factory = IDWriteFactory7()
            guid = IID_IDWriteFactory7
        elif WINDOWS_10_CREATORS_UPDATE_OR_GREATER:  # Added memory loader. Added SVG color glyphs.
            cls._write_factory = IDWriteFactory5()
            guid = IID_IDWriteFactory5
        elif WINDOWS_8_1_OR_GREATER:  # Added COLOR/CPAL color glyphs.
            cls._write_factory = IDWriteFactory2()
            guid = IID_IDWriteFactory2
        else:
            cls._write_factory = IDWriteFactory()
            guid = IID_IDWriteFactory

        DWriteCreateFactory(DWRITE_FACTORY_TYPE_SHARED, guid, byref(cls._write_factory))

    @classmethod
    def _initialize_custom_loaders(cls: type[Win32DirectWriteFont]) -> None:
        """Initialize the loaders needed to load custom fonts."""
        if WINDOWS_10_CREATORS_UPDATE_OR_GREATER:
            # Windows 10 finally has a built in loader that can take data and make a font out of it w/ COMs.
            cls._font_loader = IDWriteInMemoryFontFileLoader()
            cls._write_factory.CreateInMemoryFontFileLoader(byref(cls._font_loader))
            cls._write_factory.RegisterFontFileLoader(cls._font_loader)

            # Used for grouping fonts together.
            cls._font_builder = IDWriteFontSetBuilder1()
            cls._write_factory.CreateFontSetBuilder5(byref(cls._font_builder))
        else:
            cls._font_loader = LegacyFontFileLoader()

            # Note: RegisterFontLoader takes a pointer. However, for legacy we implement our own callback interface.
            # Therefore we need to pass to the actual pointer directly.
            cls._write_factory.RegisterFontFileLoader(cls._font_loader.as_interface(IDWriteFontFileLoader_LI))

            cls._font_collection_loader = LegacyCollectionLoader(cls._write_factory, cls._font_loader)
            cls._write_factory.RegisterFontCollectionLoader(cls._font_collection_loader)

            cls._font_loader_key = cast(create_unicode_buffer("legacy_font_loader"), c_void_p)

    @classmethod
    def add_font_data(cls: type[Win32DirectWriteFont], data: BinaryIO) -> None:
        if not cls._write_factory:
            cls._initialize_direct_write()

        if not cls._font_loader:
            cls._initialize_custom_loaders()

        if WINDOWS_10_CREATORS_UPDATE_OR_GREATER:
            font_file = IDWriteFontFile()
            hr = cls._font_loader.CreateInMemoryFontFileReference(cls._write_factory,
                                                                  data,
                                                                  len(data),
                                                                  None,
                                                                  byref(font_file))

            hr = cls._font_builder.AddFontFile(font_file)
            if hr != 0:
                raise Exception("This font file data is not not a font or unsupported.")

            # We have to rebuild collection everytime we add a font.
            # No way to add fonts to the collection once the FontSet and Collection are created.
            # Release old one and renew.
            if cls._custom_collection:
                cls._font_set.Release()
                cls._custom_collection.Release()

            cls._font_set = IDWriteFontSet()
            cls._font_builder.CreateFontSet(byref(cls._font_set))

            cls._custom_collection = IDWriteFontCollection1()
            cls._write_factory.CreateFontCollectionFromFontSet(cls._font_set, byref(cls._custom_collection))

        else:
            cls._font_cache.append(data)

            # If a collection exists, we need to completely remake the collection, delete everything and start over.
            if cls._custom_collection:
                cls._custom_collection = None

                cls._write_factory.UnregisterFontCollectionLoader(cls._font_collection_loader)
                cls._write_factory.UnregisterFontFileLoader(cls._font_loader)

                cls._font_loader = LegacyFontFileLoader()
                cls._font_collection_loader = LegacyCollectionLoader(cls._write_factory, cls._font_loader)

                cls._write_factory.RegisterFontCollectionLoader(cls._font_collection_loader)
                cls._write_factory.RegisterFontFileLoader(cls._font_loader.as_interface(IDWriteFontFileLoader_LI))

            cls._font_collection_loader.AddFontData(cls._font_cache)

            cls._custom_collection = IDWriteFontCollection()

            cls._write_factory.CreateCustomFontCollection(cls._font_collection_loader,
                                                          cls._font_loader_key,
                                                          sizeof(cls._font_loader_key),
                                                          byref(cls._custom_collection))

    @classmethod
    def get_collection(cls: type[Win32DirectWriteFont], font_name: str) -> tuple[int | None, IDWriteFontCollection1 | None]:
        """Obtain a collection of fonts based on the font name.

        Returns:
            Warnings collection this font belongs to (system or custom collection), as well as the index
            in the collection.
        """
        if not cls._write_factory:
            cls._initialize_direct_write()

        font_index = UINT()
        font_exists = BOOL()

        # Check custom loaded font collections.
        if cls._custom_collection:
            cls._custom_collection.FindFamilyName(create_unicode_buffer(font_name),
                                                  byref(font_index),
                                                  byref(font_exists))

            if font_exists.value:
                return font_index.value, cls._custom_collection

        # Check if font is in the system collection.
        # Do not cache these values permanently as system font collection can be updated during runtime.
        sys_collection = IDWriteFontCollection()
        if not font_exists.value:
            cls._write_factory.GetSystemFontCollection(byref(sys_collection), 1)
            sys_collection.FindFamilyName(create_unicode_buffer(font_name),
                                          byref(font_index),
                                          byref(font_exists))

            if font_exists.value:
                return font_index.value, sys_collection

        return None, None

    @classmethod
    def find_font_face(cls, font_name: str, weight: str, italic: bool | str, stretch: bool | str) -> tuple[
        IDWriteFont | None, IDWriteFontCollection | None]:
        """Search font collections for legacy RBIZ names.

        Matching to weight, italic, stretch is problematic in that there are many values. Attempt to parse the font
        name looking for matches to the name database, and pick the closest match.

        This will search all font faces in the system and custom collections.

        Returns:
            Returns a collection and IDWriteFont if successful.
        """
        p_weight, p_italic, p_stretch = cls.parse_name(font_name, weight, italic, stretch)

        _debug_print(f"directwrite: '{font_name}' not found. Attempting legacy name lookup in all collections.")
        if cls._custom_collection:
            collection_idx = cls.find_legacy_font(cls._custom_collection, font_name, p_weight, p_italic, p_stretch)
            if collection_idx is not None:
                return collection_idx, cls._custom_collection

        sys_collection = IDWriteFontCollection()
        cls._write_factory.GetSystemFontCollection(byref(sys_collection), 1)

        collection_idx = cls.find_legacy_font(sys_collection, font_name, p_weight, p_italic, p_stretch)
        if collection_idx is not None:
            return collection_idx, sys_collection

        return None, None

    def get_text_size(self, text: str) -> tuple[int, int]:
        layout = self.create_text_layout(text)
        metrics = DWRITE_TEXT_METRICS()
        layout.GetMetrics(byref(metrics))
        layout.Release()
        return round(metrics.width), round(metrics.height)

    @classmethod
    def have_font(cls: type[Win32DirectWriteFont], name: str) -> bool:
        return cls.get_collection(name)[0] is not None

    @staticmethod
    def parse_name(font_name: str, weight: str, style: int, stretch: int) -> tuple[str, int, int]:
        """Attempt at parsing any special names in a font for legacy checks. Takes the first found."""
        font_name = font_name.lower()
        split_name = font_name.split(" ")

        found_weight = weight
        found_style = style
        found_stretch = stretch

        # Only search if name is split more than once.
        if len(split_name) > 1:
            for name, value in name_to_weight.items():
                if name in split_name:
                    found_weight = value
                    break

            for name, value in name_to_style.items():
                if name in split_name:
                    found_style = value
                    break

            for name, value in name_to_stretch.items():
                if name in split_name:
                    found_stretch = value
                    break

        return found_weight, found_style, found_stretch

    @staticmethod
    def find_legacy_font(collection: IDWriteFontCollection, font_name: str, weight: str, italic: bool | str, stretch: bool | str, full_debug: bool=False) -> IDWriteFont | None:
        coll_count = collection.GetFontFamilyCount()

        assert _debug_print(f"directwrite: Found {coll_count} fonts in collection.")

        locale = get_system_locale()

        for i in range(coll_count):
            family = IDWriteFontFamily()
            collection.GetFontFamily(i, byref(family))

            # Just check the first character in Family Names to reduce search time. Arial -> A's only.
            family_name_str = IDWriteLocalizedStrings()
            family.GetFamilyNames(byref(family_name_str))

            family_names = Win32DirectWriteFont.unpack_localized_string(family_name_str, locale)
            family_name = family_names[0]

            if family_name[0] != font_name[0]:
                family.Release()
                continue

            assert _debug_print(f"directwrite: Inspecting family name: {family_name}")

            # Fonts in the family. Full search to search all font faces, typically the first will be good enough to tell
            ft_ct = family.GetFontCount()

            face_names = []
            matches = []
            for j in range(ft_ct):
                temp_ft = IDWriteFont()
                family.GetFont(j, byref(temp_ft))

                if _debug_font and full_debug:
                    fc_str = IDWriteLocalizedStrings()
                    temp_ft.GetFaceNames(byref(fc_str))

                    strings = Win32DirectWriteFont.unpack_localized_string(fc_str, locale)
                    face_names.extend(strings)

                    assert _debug_print(f"directwrite: Face names found: {strings}")

                # Check for GDI compatibility name
                compat_names = IDWriteLocalizedStrings()
                exists = BOOL()
                temp_ft.GetInformationalStrings(DWRITE_INFORMATIONAL_STRING_WIN32_FAMILY_NAMES,
                                                byref(compat_names),
                                                byref(exists))

                # Successful in finding GDI name.
                match_found = False
                if exists.value != 0:
                    for compat_name in Win32DirectWriteFont.unpack_localized_string(compat_names, locale):
                        if compat_name == font_name:
                            assert _debug_print(
                                f"Found legacy name '{font_name}' as '{family_name}' in font face '{j}' (collection "
                                f"id #{i}).")

                            match_found = True
                            matches.append((temp_ft.GetWeight(), temp_ft.GetStyle(), temp_ft.GetStretch(), temp_ft))
                            break

                # Release resource if not a match.
                if not match_found:
                    temp_ft.Release()

            family.Release()

            # If we have matches, we've already parsed through the proper family. Now try to match.
            if matches:
                write_font = Win32DirectWriteFont.match_closest_font(matches, weight, italic, stretch)

                # Cleanup other matches not used.
                for match in matches:
                    if match[3] != write_font:
                        match[3].Release()  # Release all other matches.

                return write_font

        return None

    @staticmethod
    def match_closest_font(font_list: list[tuple[int, int, int, IDWriteFont]], weight: str, italic: int, stretch: int) -> IDWriteFont | None:
        """Match the closest font to the parameters specified.

        If a full match is not found, a secondary match will be found based on similar features. This can probably
        be improved, but it is possible you could get a different font style than expected.
        """
        closest = []
        for match in font_list:
            (f_weight, f_style, f_stretch, writefont) = match

            # Found perfect match, no need for the rest.
            if f_weight == weight and f_style == italic and f_stretch == stretch:
                _debug_print(
                    f"directwrite: full match found. (weight: {f_weight}, italic: {f_style}, stretch: {f_stretch})")
                return writefont

            prop_match = 0
            similar_match = 0
            # Look for a full match, otherwise look for close enough.
            # For example, Arial Black only has Oblique, not Italic, but good enough if you want slanted text.
            if f_weight == weight:
                prop_match += 1
            elif weight != DWRITE_FONT_WEIGHT_NORMAL and f_weight != DWRITE_FONT_WEIGHT_NORMAL:
                similar_match += 1

            if f_style == italic:
                prop_match += 1
            elif italic != DWRITE_FONT_STYLE_NORMAL and f_style != DWRITE_FONT_STYLE_NORMAL:
                similar_match += 1

            if stretch == f_stretch:
                prop_match += 1
            elif stretch != DWRITE_FONT_STRETCH_NORMAL and f_stretch != DWRITE_FONT_STRETCH_NORMAL:
                similar_match += 1

            closest.append((prop_match, similar_match, *match))

        # If we get here, no perfect match, sort by highest perfect match, to secondary matches.
        closest.sort(key=lambda fts: (fts[0], fts[1]), reverse=True)

        if closest:
            # Take the first match after sorting.
            closest_match = closest[0]
            _debug_print(f"directwrite: falling back to partial match. "
                         f"(weight: {closest_match[2]}, italic: {closest_match[3]}, stretch: {closest_match[4]})")
            return closest_match[5]

        return None

    @staticmethod
    def unpack_localized_string(local_string: IDWriteLocalizedStrings, locale: str) -> list[str]:
        """Takes IDWriteLocalizedStrings and unpacks the strings inside of it into a list."""
        str_array_len = local_string.GetCount()

        strings = []
        for _ in range(str_array_len):
            string_size = UINT32()

            idx = Win32DirectWriteFont.get_localized_index(local_string, locale)

            local_string.GetStringLength(idx, byref(string_size))

            buffer_size = string_size.value

            buffer = create_unicode_buffer(buffer_size + 1)

            local_string.GetString(idx, buffer, len(buffer))

            strings.append(buffer.value)

        local_string.Release()

        return strings

    @staticmethod
    def get_localized_index(strings: IDWriteLocalizedStrings, locale: str) -> int:
        idx = UINT32()
        exists = BOOL()

        if locale:
            strings.FindLocaleName(locale, byref(idx), byref(exists))

            if not exists.value:
                # fallback to english.
                strings.FindLocaleName("en-us", byref(idx), byref(exists))

                if not exists:
                    return 0

            return idx.value

        return 0


d2d_factory = ID2D1Factory()
hr = D2D1CreateFactory(D2D1_FACTORY_TYPE_SINGLE_THREADED, IID_ID2D1Factory, None, byref(d2d_factory))
transparent = D2D1_COLOR_F(0.0, 0.0, 0.0, 0.0)
white = D2D1_COLOR_F(1.0, 1.0, 1.0, 1.0)
red = D2D1_COLOR_F(1.0, 0.0, 0.0, 1.0)
no_offset = D2D_POINT_2F(0, 0)


# If we are not shaping, monkeypatch to no shape function.
if pyglet.options["win32_disable_shaping"]:
    Win32DirectWriteFont.get_glyphs = Win32DirectWriteFont.get_glyphs_no_shape
