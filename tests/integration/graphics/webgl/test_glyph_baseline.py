from __future__ import annotations

import math
from types import SimpleNamespace

import pytest

import pyglet


class _FractionalMetricsContext:
    """Canvas context whose text metrics are fractional, as in Firefox or with display scaling."""

    def __init__(self, context, ascent_fraction: float, descent_fraction: float) -> None:
        object.__setattr__(self, "_context", context)
        object.__setattr__(self, "_fractions", (ascent_fraction, descent_fraction))

    def __getattr__(self, name):
        return getattr(self._context, name)

    def __setattr__(self, name, value) -> None:
        setattr(self._context, name, value)

    def measureText(self, text):  # noqa: N802
        metrics = self._context.measureText(text)
        ascent_fraction, descent_fraction = self._fractions
        return SimpleNamespace(
            width=metrics.width,
            actualBoundingBoxAscent=math.floor(metrics.actualBoundingBoxAscent) + ascent_fraction,
            actualBoundingBoxDescent=math.floor(metrics.actualBoundingBoxDescent) + descent_fraction,
        )


@pytest.mark.parametrize(("ascent_fraction", "descent_fraction"), [(0.3, 0.4), (0.5, 0.5), (0.8, 0.6), (0, 0)])
def test_glyph_baseline_is_where_the_glyph_is_drawn(webgl_window, monkeypatch, ascent_fraction, descent_fraction):
    from pyglet.font import pyodide_js

    renderer = pyodide_js.PyodideGlyphRenderer(pyglet.font.load(None, 16))
    context = _FractionalMetricsContext(pyodide_js._font_context, ascent_fraction, descent_fraction)
    monkeypatch.setattr(pyodide_js, "_font_context", context)

    for text in "Agjx":
        metrics = context.measureText(text)
        glyph = renderer.render(text)

        # The text is drawn ceil(ascent) below the top of the glyph image: the baseline declared from the
        # bottom of the image must be at the same height.
        assert glyph.height - glyph.baseline == math.ceil(metrics.actualBoundingBoxAscent), text
