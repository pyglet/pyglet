from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

import pyglet

from tests.annotations import Platform, require_platform


pytestmark = require_platform(Platform.WINDOWS)


@contextmanager
def _gdi_backend() -> Iterator[None]:
    previous_gdi = pyglet.options.win32_gdi_font
    previous_shaping = pyglet.options.text_shaping
    try:
        pyglet.font.manager._invalidate()  # noqa: SLF001
        pyglet.options.win32_gdi_font = True
        pyglet.options.text_shaping = False
        pyglet.font._system_font_class = pyglet.font._get_system_font_class()  # noqa: SLF001
        yield
    finally:
        pyglet.font.manager._invalidate()  # noqa: SLF001
        pyglet.options.win32_gdi_font = previous_gdi
        pyglet.options.text_shaping = previous_shaping
        pyglet.font._system_font_class = pyglet.font._get_system_font_class()  # noqa: SLF001


def test_gdi_supports_text_size_and_non_binary_weights(test_window):
    with _gdi_backend():
        light = pyglet.font.load("Arial", 24, weight="light", dpi=96)
        black = pyglet.font.load("Arial", 24, weight="black", dpi=96)

        assert light.logfont.lfWeight == 300
        assert black.logfont.lfWeight == 900
        width, height = light.get_text_size("GDI text")
        assert width > 0
        assert height > 0


def test_gdi_does_not_crop_supplementary_characters(test_window):
    with _gdi_backend():
        font = pyglet.font.load("Segoe UI Emoji", 24, dpi=96)
        glyphs, positions = font.get_glyphs("\N{GRINNING FACE}", shaping=False)
        measured_width, _ = font.get_text_size("\N{GRINNING FACE}")

        assert len(glyphs) == len(positions) == 1
        assert glyphs[0].width >= measured_width
        assert any(glyphs[0].get_image_data().get_bytes("RGBA")[3::4])


def test_load_gdi(test_window):
    with _gdi_backend():
        myfont = pyglet.font.load(["Action Man", "Segoe UI"], size=12, dpi=96)

        from pyglet.font.win32 import GDIPlusFont  # noqa: PLC0415

        assert isinstance(myfont, GDIPlusFont)
        assert myfont.name == "Segoe UI"
        assert pyglet.font.manager.get_resolved_name(["Action Man", "Segoe UI"]) == "Segoe UI"


def test_load_no_custom_from_list_gdi(test_window, test_data):
    with _gdi_backend():
        myfont = pyglet.font.load(["Action Man", "Segoe UI"], size=12, dpi=96)

        from pyglet.font.win32 import GDIPlusFont  # noqa: PLC0415

        assert isinstance(myfont, GDIPlusFont)
        assert myfont.name == "Segoe UI"
        assert pyglet.font.manager.get_resolved_name(["Action Man", "Segoe UI"]) == "Segoe UI"

        file = test_data.get_file("fonts", "action_man.ttf")
        pyglet.font.add_file(file)
        assert pyglet.font.have_font("Action Man") is True
