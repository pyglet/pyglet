from __future__ import annotations

import asyncio
import math
from asyncio import Task
from typing import ClassVar

import pyglet
from pyglet.enums import Stretch, Style, Weight
from pyglet.font.ttf import TruetypeInfoBytes
from pyglet.font import base, FontManager
from pyglet.font.base import Glyph, FontException, GlyphPosition

from pyglet.image import ImageData

_debug = pyglet.options.debug_font

try:
    import js  # noqa: F821
    import pyodide.ffi  # noqa: F401, F821
except ImportError:
    raise ImportError


_font_canvas = js.document.createElement("canvas")
_font_canvas.id = "font_canvas"
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
        return self._render(text)

    def render_stroke(self, text: str, size: float, join: str) -> Glyph | None:
        """Rasterize a text outline with CanvasRenderingContext2D.strokeText."""
        return self._render(text, size, join)

    def _render(self, text: str, stroke_size: float = 0, stroke_join: str = "round") -> Glyph | None:
        _font_context.font = self.font.js_name
        metrics = _font_context.measureText(text)
        padding = math.ceil(stroke_size * (10 if stroke_join == "miter" else 1)) + 1 if stroke_size else 0
        w = max(1, int(math.ceil(metrics.width)) + padding * 2)
        h = max(1, int(math.ceil(metrics.actualBoundingBoxAscent + metrics.actualBoundingBoxDescent)) + padding * 2)
        baseline_y = max(1, int(math.ceil(metrics.actualBoundingBoxAscent)) + padding)

        # Setting the canvas size seems to reset the context settings?
        _font_canvas.width = w
        _font_canvas.height = h
        _font_context.imageSmoothingEnabled = False  # Doesn't seem to make a difference with antialiasing?
        #_font_context.mozImageSmoothingEnabled = False
        #_font_context.webkitImageSmoothingEnabled = False
        #_font_context.msImageSmoothingEnabled = False
        _font_context.font = self.font.js_name
        _font_context.fillStyle = 'white'
        _font_context.strokeStyle = 'white'
        _font_context.lineWidth = stroke_size * 2
        _font_context.lineJoin = stroke_join
        _font_context.miterLimit = 10

        _font_context.translate(0, h)  # Move down
        _font_context.scale(1, -1)  # Flip vertically

        if stroke_size:
            _font_context.strokeText(text, padding, baseline_y)
        else:
            _font_context.fillText(text, 0, baseline_y)

        image_data = _font_context.getImageData(0, 0, w, h)
        if stroke_size:
            left, top, right, bottom = self._get_alpha_bounds(image_data.data, w, h)
            if right < left or bottom < top:
                return None
            image_data = _font_context.getImageData(left, top, right - left + 1, bottom - top + 1)
            # The context is flipped before drawing because ImageData is
            # supplied to pyglet with a positive (bottom-to-top) pitch.
            # Therefore Canvas's top rows are the glyph's bottom rows.
            baseline = int(math.ceil(metrics.actualBoundingBoxDescent)) + padding - top
            left_side_bearing = left - padding
        else:
            baseline = int(math.ceil(metrics.actualBoundingBoxDescent))
            left_side_bearing = 0

        image = ImageData(image_data.width, image_data.height, 'RGBA', image_data.data)
        glyph = self.font.create_glyph(image)
        glyph.set_bearings(baseline, left_side_bearing, math.ceil(metrics.width))
        return glyph

    @staticmethod
    def _get_alpha_bounds(pixel_data, width: int, height: int) -> tuple[int, int, int, int]:
        """Return the bounds of non-transparent Canvas pixels."""
        left, top, right, bottom = width, height, -1, -1
        for y in range(height):
            for x in range(width):
                if pixel_data[(y * width + x) * 4 + 3]:
                    left = min(left, x)
                    top = min(top, y)
                    right = max(right, x)
                    bottom = max(bottom, y)
        return left, top, right, bottom

def _measure_font_width(font_family: str) -> int:
    """Use a DOM element to measure the text width of a given string using a font family."""
    _hidden_div.style.fontSize = "32px"
    _hidden_div.style.fontFamily = font_family
    return _hidden_div.offsetWidth

# DIV element used for measuring width for font fallback behavior. Do not remove.
_hidden_div = js.document.createElement("div")
_hidden_div.textContent = "PYGLET_FONT_WIDTH"
_hidden_div.style.visibility  = "hidden"
_hidden_div.style.position = "absolute"
_hidden_div.id = "_font_resolver"
js.document.body.appendChild(_hidden_div)

class JavascriptPyodideFont(base.Font):
    glyph_renderer_class = PyodideGlyphRenderer
    _glyph_renderer: PyodideGlyphRenderer

    _default_serif_width = _measure_font_width("serif")
    _default_sans_serif_width = _measure_font_width("sans-serif")

    # Cache font data by the loaded name dict.
    _font_data_cache: ClassVar[dict] = {}
    _name_font_cache: ClassVar[dict] = {}
    _full_name_aliases: ClassVar[dict[str, tuple[str, int, str, str]]] = {}
    _custom_character_maps: ClassVar[dict[str, set[str]]] = {}

    def __init__(self, name: str, size: float, weight: Weight | str = Weight.NORMAL,
                 style: Style | str = Style.NORMAL, stretch: Stretch | str = Stretch.NORMAL,
                 dpi: int | None = None) -> None:
        self._glyph_renderer = None
        self._glyph_sources = {}
        self._stroke_glyphs = {}
        super().__init__(name, size, weight, style, stretch, dpi)

        full_name_alias = None
        if pyglet.options.font_name_compatibility:
            full_name_alias = self._full_name_aliases.get(name.casefold())

        if full_name_alias:
            family, self._weight, self._italic, self._stretch = full_name_alias
            # A full name identifies one concrete face. Use its canonical CSS
            # family and embedded traits, rather than synthesizing a different
            # face from separately requested traits.
            self._name = family
        else:
            if isinstance(weight, str):
                self._weight = name_to_weight.get(weight.lower(), "normal")
            else:
                self._weight = "bold" if weight is True else "normal"

            if isinstance(stretch, str):
                self._stretch = _name_to_stretch.get(stretch.lower(), "normal")
            else:
                self._stretch = "normal"

            if style is True:
                self._italic = "italic"
            elif isinstance(style, str) and style.lower() in ("italic", "oblique"):
                self._italic = style.lower()
            else:
                self._italic = "normal"

        self.js_name = f"{self._italic} {self._weight} {self.pixel_size}px '{self._name}'"

        _font_context.font = self.js_name
        metrics = _font_context.measureText("A")
        self.ascent = metrics.fontBoundingBoxAscent
        self.descent = -metrics.fontBoundingBoxDescent

    def get_text_size(self, text: str) -> tuple[int, int]:
        _font_context.font = self.js_name
        metrics = _font_context.measureText(text)
        w = max(1, int(math.ceil(metrics.width)))
        h = max(1, int(math.ceil(metrics.actualBoundingBoxAscent + metrics.actualBoundingBoxDescent)))
        return w, h

    @classmethod
    def add_font_data(cls, data: bytes, manager: FontManager) -> Task:
        ttf_info = TruetypeInfoBytes(data)
        family = ttf_info.get_font_family_name()
        if family is None:
            raise FontException("Could not read the font family name.")

        subfamily = ttf_info.get_name("subfamily")  # Contains words like Regular, Bold, etc.
        if subfamily is None:
            raise FontException("Could not read the font subfamily name.")

        fullname = ttf_info.get_full_font_name()
        supported_characters = set(ttf_info.get_character_map())

        weight = ttf_info.get_weight_class()  # TTF weight value like 700.
        clamped_weight = min(max(weight, 100), 900)  # clamp 100-900.

        ttf_stretch_id = ttf_info.get_width_class()
        italic = "italic" if ttf_info.is_italic() else "normal"
        js_arr = js.Uint8Array.new(data)

        weight_name = _ttf_weight_to_name.get(clamped_weight, "normal")
        stretch_name = _width_class_to_pyglet_stretch.get(ttf_stretch_id, "normal")

        # Specify family by the name and the weight.
        fam_font = js.window.FontFace.new(family, js_arr.buffer,
                                          weight=str(clamped_weight),
                                          stretch=_width_class_to_js_stretch.get(ttf_stretch_id, "normal"),
                                          style=italic,
                                          )

        if _debug:
            js.console.log(f"Loaded custom font (family: {family}, subfamily: {subfamily}, full name: {fullname}, "
                           f"weight: {weight}, stretch_width={ttf_stretch_id})")



        #if family != fullname:
            # Full font name may not always match the family name, add both to cover both.
       #     full_font = js.window.FontFace.new(fullname, js_arr.buffer)

        async def _load_fonts() -> bool:
            try:
                await fam_font.load()
            except Exception as e:  # noqa: BLE001
                print("Exception occurred loading Family Font:", e)
                return False

            js.document.fonts.add(fam_font)

            cls._custom_character_maps.setdefault(family.casefold(), set()).update(supported_characters)

            if fullname and fullname.casefold() != family.casefold():
                cls._full_name_aliases[fullname.casefold()] = (
                    family,
                    clamped_weight,
                    italic,
                    _width_class_to_js_stretch.get(ttf_stretch_id, "normal"),
                )

            manager._add_loaded_font({(family, weight_name, italic, stretch_name)})  # noqa: SLF001
            return True

        return asyncio.create_task(_load_fonts())

    def create_glyph(self, img: ImageData) -> Glyph:
        return super().create_glyph(img)

    def get_glyphs(self, text: str, shaping: bool = False) -> tuple[list[Glyph], list[GlyphPosition]]:
        self._initialize_renderer()

        glyphs = []  # glyphs that are committed.
        offsets = []
        for c in base.get_grapheme_clusters(str(text)):
            # Get the glyph for 'c'.  Hide tabs (Windows and Linux render boxes)
            if c == "\t":
                c = " "  # noqa: PLW2901
            if c not in self.glyphs:
                self.glyphs[c] = self._glyph_renderer.render(c)
                self._glyph_sources[id(self.glyphs[c])] = c
            glyphs.append(self.glyphs[c])
            offsets.append(GlyphPosition(0, 0, 0, 0))
        return glyphs, offsets

    def get_stroke_glyph(self, glyph: Glyph, size: float, join: str = "round") -> Glyph | None:
        if size <= 0 or (text := self._glyph_sources.get(id(glyph))) is None:
            return None
        cache_key = id(glyph), size, join
        if stroked := self._stroke_glyphs.get(cache_key):
            return stroked
        stroked = self._glyph_renderer.render_stroke(text, size, join)
        if stroked is not None:
            self._stroke_glyphs[cache_key] = stroked
        return stroked

    def get_glyphs_for_width(self, text: str, width: int) -> list[Glyph]:
        return super().get_glyphs_for_width(text, width)

    def has_character(self, character: str) -> bool:
        # Browser APIs do not expose a way to do this for system fonts.
        # For custom fonts, we utilize the glyph table from our ttf inspector.
        super().has_character(character)
        custom_characters = self._custom_character_maps.get(self._name.casefold())
        return custom_characters is None or character in custom_characters

    @classmethod
    def have_font(cls: type[JavascriptPyodideFont], name: str) -> bool:
        """A very round about way to determine if a font exists for JavaScript.

        JavaScript does not have any way to query system or custom loaded fonts without experimental or
        unreliable API's. Furthermore, you cannot determine what font is actually being used to render either.

        According to docs, CSS should guarantee the font families of "serif" and "sans-serif".

        Therefore, a hidden element will be used to measure a string to check for a size match between the above
        font families. If the text matches, then a fallback font was used.
        """
        if pyglet.options.font_name_compatibility and name.casefold() in cls._full_name_aliases:
            return True

        match_serif_name = f"'{name}', serif"
        match_sans_serif_name = f"'{name}', sans-serif"

        # Check if the font matches our serif.
        if (_measure_font_width(match_serif_name) == cls._default_serif_width and
            # Font might actually be the fallback serif, check if it matches a sans serif.
            _measure_font_width(match_sans_serif_name) == cls._default_sans_serif_width):
                return False

        # The font should theoretically be available.
        return True


    @property
    def name(self) -> str:
        return self._name

# JavaScript/CSS naming, not Pyglet naming.
_width_class_to_js_stretch = {
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

_width_class_to_pyglet_stretch = {
    1: "ultracondensed",
    2: "extracondensed",
    3: "condensed",
    4: "semicondensed",
    5: "normal",
    6: "semiexpanded",
    7: "expanded",
    8: "extraexpanded",
    9: "ultraexpanded",
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
_ttf_weight_to_name = {
    100: 'thin',
    200: 'extralight',
    300: 'light',
    400: 'normal',
    500: 'medium',
    600: 'semibold',
    700: 'bold',
    800: 'extrabold',
    900: 'black',
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
