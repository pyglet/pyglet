from __future__ import annotations

import asyncio
import math
from asyncio import Task
from typing import TYPE_CHECKING, ClassVar

import pyglet
from pyglet.font.ttf import TruetypeInfoBytes

_debug = pyglet.options.debug_font

try:
    import js
    import pyodide.ffi
except ImportError:
    raise ImportError

from pyglet.font import base
from pyglet.font.base import Glyph, FontException, GlyphPosition

from pyglet.image import ImageData

if TYPE_CHECKING:
    from pyglet.image.base import TextureDescriptor
    from pyglet.image import AbstractImage


_font_canvas = js.document.createElement("canvas")
# Added desynchronized for testing. Supposedly lower latency, but may introduce artifacts?
# Doesn't seem to affect quality since we are just using this to get pixel data. Remove if problem in the future.
_font_context = _font_canvas.getContext("2d", willReadFrequently=True, desynchronized=True, antialias=False)

class PyodideGlyphRenderer(base.GlyphRenderer):
    font: JavascriptPyodideFont
    def __init__(self, font: JavascriptPyodideFont) -> None:  # noqa: D107
        self.font = font
        super().__init__(font)
        self.temp_save = []

    def render(self, text: str) -> Glyph:
        _font_context.font = self.font.js_name
        metrics = _font_context.measureText(text)
        w = max(1, int(math.ceil(metrics.width)))
        h = max(1, int(math.ceil(metrics.actualBoundingBoxAscent + metrics.actualBoundingBoxDescent)))

        # Setting the canvas size seems to reset the context settings?
        _font_canvas.width = w
        _font_canvas.height = h
        _font_context.imageSmoothingEnabled = False  # Doesn't seem to make a difference with antialiasing?
        _font_context.mozImageSmoothingEnabled = False
        _font_context.webkitImageSmoothingEnabled = False
        _font_context.msImageSmoothingEnabled = False
        _font_context.font = self.font.js_name
        _font_context.fillStyle = 'white'

        _font_context.translate(0, h)  # Move down
        _font_context.scale(1, -1)  # Flip vertically

        # Draw to context
        _font_context.fillText(text, 0, max(1, int(math.ceil(metrics.actualBoundingBoxAscent))))

        image_data = _font_context.getImageData(0, 0, w, h)
        pixel_data = image_data.data  # Uint8Array

        image = ImageData(w, h, 'RGBA', pixel_data)

        glyph = self.font.create_glyph(image)
        glyph.set_bearings(int(math.ceil(metrics.actualBoundingBoxDescent)), 0, w)
        return glyph


class JavascriptPyodideFont(base.Font):
    glyph_renderer_class = PyodideGlyphRenderer
    _glyph_renderer: PyodideGlyphRenderer

    # Cache font data by the loaded name dict.
    _font_data_cache: ClassVar[dict] = {}
    _name_font_cache: ClassVar[dict] = {}

    def __init__(self, name: str, size: float, weight: str = "normal", italic: bool = False, stretch: bool = False,
                 dpi: int | None = None) -> None:
        self._glyph_renderer = None
        super().__init__()
        if not name:
            name = 'Arial'
        self._name = name
        self.size = size
        self.pixel_size = size * dpi / 72.0

        self.weight = weight
        self.italic = italic
        self.stretch = stretch
        self.dpi = dpi

        if isinstance(weight, str):
            self._weight = name_to_weight.get(weight.lower(), "normal")
        else:
            self._weight = "bold" if weight is True else "normal"

        if isinstance(stretch, str):
            self._stretch = _name_to_stretch.get(stretch.lower(), "normal")
        else:
            self._stretch = "normal"

        self._italic = "italic" if italic is True else "normal"

        self.js_name = f"{self._italic} {self._weight} {self.pixel_size}px '{name}'"
        if _debug:
            js.console.log(f"Selecting font: {self.js_name}")

        _font_context.font = self.js_name
        metrics = _font_context.measureText("A")
        self.ascent = metrics.fontBoundingBoxAscent
        self.descent = -metrics.fontBoundingBoxDescent

    @classmethod
    def add_font_data(cls, data: bytes) -> Task:
        ttf_info = TruetypeInfoBytes(data)
        family = ttf_info.get_name("family")  # Family Name
        if family is None:
            raise FontException("Could not read the font family name.")

        subfamily = ttf_info.get_name("subfamily")  # Contains words like Regular, Bold, etc.
        if subfamily is None:
            raise FontException("Could not read the font subfamily name.")

        fullname = ttf_info.get_name("name")  # Usually combines Family + Subfamily, but not always.
        if fullname is None:
            raise FontException("Could not read the font name.")

        weight = ttf_info.get_weight_class()
        stretch = ttf_info.get_width_class()
        italic = "italic" if ttf_info.is_italic() else "normal"
        js_arr = js.Uint8Array.new(data)

        # Specify family by the name and the weight.
        fam_font = js.window.FontFace.new(family, js_arr.buffer,
                                          weight=str(min(max(weight, 100), 900)),  # clamp 100-900.
                                          stretch=_width_class_to_stretch.get(stretch, "normal"),
                                          style=italic,
                                          )

        if _debug:
            js.console.log(f"Loaded custom font (family: {family}, subfamily: {subfamily}, full name: {fullname}, "
                           f"weight: {weight}, stretch_width={stretch})")

        if family != fullname:
            # Full font name may not always match the family name, add both to cover both.
            full_font = js.window.FontFace.new(fullname, js_arr.buffer)

        async def _load_fonts() -> bool:
            try:
                await fam_font.load()
            except Exception as e:  # noqa: BLE001
                print("Exception occurred loading Family Font:", e)
                return False

            js.document.fonts.add(fam_font)
            js.document.body.style.fontFamily = family
            if _debug:
                js.console.log(f"Loaded Family Font: {family}")

            if family != fullname:
                try:
                    await full_font.load()
                except Exception as e:  # noqa: BLE001
                    print("Exception occurred loading Name Font:", e)
                    return False
                js.document.fonts.add(full_font)
                if _debug:
                    js.console.log(f"Loaded Named Font: {fullname}")

            return True

        return asyncio.create_task(_load_fonts())

    def create_glyph(self, img: AbstractImage, descriptor: TextureDescriptor | None = None) -> Glyph:
        return super().create_glyph(img, descriptor)

    def get_glyphs(self, text: str) -> tuple[list[Glyph], list[GlyphPosition]]:
        if not self._glyph_renderer:
            self._glyph_renderer = self.glyph_renderer_class(self)
        glyphs = []  # glyphs that are committed.
        offsets = []
        for c in base.get_grapheme_clusters(str(text)):
            # Get the glyph for 'c'.  Hide tabs (Windows and Linux render
            # boxes)
            if c == "\t":
                c = " "  # noqa: PLW2901
            if c not in self.glyphs:
                self.glyphs[c] = self._glyph_renderer.render(c)
            glyphs.append(self.glyphs[c])
            offsets.append(GlyphPosition(0, 0, 0, 0))
        return glyphs, offsets

    def get_glyphs_for_width(self, text: str, width: int) -> list[Glyph]:
        return super().get_glyphs_for_width(text, width)

    @classmethod
    def have_font(cls: type[base.Font], name: str) -> bool:
        return super().have_font(name)

    @property
    def name(self) -> str:
        return self._name

_width_class_to_stretch = {
    1: "ultra-condensed",
    2: "extra-condensed",
    3: "condensed",
    4: "semi-condensed",
    5: "normal",
    6: "semi-expanded",
    7: "expanded",
    8: "extra-expanded",
    9: "ultra-expanded",
}

name_to_weight = {
    'thin': 100,
    'extralight': 200,
    'light': 300,
    'normal': 400,
    'medium': 500,
    'semibold': 600,
    'bold': 700,
    'extrabold': 800,
    'black': 900,
}

_name_to_stretch = {
    "undefined": "normal",
    "ultracondensed": "ultra-condensed",
    "extracondensed": "extra-condensed",
    "condensed": "condensed",
    "semicondensed": "semi-condensed",
    "normal": "normal",
    "medium": "normal",
    "semiexpanded": "semi-expanded",
    "expanded": "expanded",
    "extraexpanded": "extra-expanded",
    "narrow": "condensed",
    "ultraexpanded": "ultra-expanded",
}
