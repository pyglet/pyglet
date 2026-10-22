from __future__ import annotations

import math

import pytest

import pyglet


def _ink_bounds(context, font, text: str) -> tuple[int, int, int]:
    """The ink of the text drawn at the origin: (left of the origin, right of the origin, advance), in pixels."""
    context.font = font.js_name
    metrics = context.measureText(text)
    return (math.ceil(metrics.actualBoundingBoxLeft), math.ceil(metrics.actualBoundingBoxRight),
            math.ceil(metrics.width))


@pytest.mark.parametrize("style", ["italic", "normal"])
def test_glyph_image_holds_the_ink_beyond_the_advance(webgl_window, style):
    from pyglet.font import pyodide_js

    font = pyglet.font.load(None, 32, style=style)
    renderer = pyodide_js.PyodideGlyphRenderer(font)

    overhangs = []
    for text in "iflfC":
        ink_left, ink_right, advance = _ink_bounds(pyodide_js._font_context, font, text)
        overhangs.append(ink_right - advance)
        glyph = renderer.render(text)

        # The glyph quad must cover the ink: the image was as wide as the advance, which cut the ink beyond it
        # (e.g. the dot of an italic i).
        x1, _, x2, _ = glyph.vertices
        assert x1 <= -ink_left, text
        assert x2 >= ink_right, text
        assert glyph.advance == advance, text

        stroked = renderer.render_stroke(text, 2, "round")
        x1, _, x2, _ = stroked.vertices
        assert x1 <= -ink_left, text
        assert x2 >= ink_right, text

    if style == "italic":
        assert max(overhangs) > 0  # The italic letters overhang their advance: the test exercises the fix
