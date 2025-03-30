from __future__ import annotations

import math
from typing import BinaryIO, TYPE_CHECKING

try:
    import js
    import pyodide.ffi
except ImportError:
    raise ImportError

from pyglet.font import base
from pyglet.font.base import Glyph

from pyglet.image import ImageData
if TYPE_CHECKING:
    from pyglet.image.base import TextureDescriptor
    from pyglet.image import AbstractImage


_font_canvas = js.document.createElement("canvas")
# Added desynchronized for testing. Supposedly lower latency, but may introduce artifacts?
# Doesn't seem to affect quality since we are just using this to get pixel data. Remove if problem in future.
_font_context = _font_canvas.getContext("2d", willReadFrequently=True, desynchronized=True, antialias=False)

class PyodideGlyphRenderer(base.GlyphRenderer):
    font: PyodideFont
    def __init__(self, font: PyodideFont) -> None:
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


class PyodideFont(base.Font):
    glyph_renderer_class = PyodideGlyphRenderer
    _glyph_renderer: PyodideGlyphRenderer

    def __init__(self, name: str, size: float, weight: str = "normal", italic: bool = False, stretch: bool = False,
                 dpi: int | None = None) -> None:
        self._glyph_renderer = None
        super().__init__()
        if not name:
            name = "Arial"
        self._name = name
        self.pixel_size = size * dpi / 72.0

        self.js_name = f"{self.pixel_size}px {name}"
        _font_context.font = self.js_name
        metrics = _font_context.measureText("A")
        self.ascent = metrics.fontBoundingBoxAscent
        self.descent = -metrics.fontBoundingBoxDescent

    @classmethod
    def add_font_data(cls: type[base.Font], data: BinaryIO) -> None:
        super().add_font_data(data)

    def create_glyph(self, img: AbstractImage, descriptor: TextureDescriptor | None = None) -> Glyph:
        return super().create_glyph(img, descriptor)

    def get_glyphs(self, text: str) -> list[Glyph]:
        if not self._glyph_renderer:
            self._glyph_renderer = self.glyph_renderer_class(self)
        glyphs = []  # glyphs that are committed.
        for c in base.get_grapheme_clusters(str(text)):
            # Get the glyph for 'c'.  Hide tabs (Windows and Linux render
            # boxes)
            if c == "\t":
                c = " "  # noqa: PLW2901
            if c not in self.glyphs:
                self.glyphs[c] = self._glyph_renderer.render(c)
            glyphs.append(self.glyphs[c])
        return glyphs

    def get_glyphs_for_width(self, text: str, width: int) -> list[Glyph]:
        return super().get_glyphs_for_width(text, width)

    @classmethod
    def have_font(cls: type[base.Font], name: str) -> bool:
        return super().have_font(name)

    @property
    def name(self) -> str:
        return self._name


# Load the font using JavaScript and get a FontFace reference
#font_face = js.eval('await loadFont("myfont.ttf", "MyCustomFont")')