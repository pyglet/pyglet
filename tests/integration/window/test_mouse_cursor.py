"""Exercise the cursor API on desktop window backends."""
from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock

import pyglet
import pytest

from tests.annotations import Platform, require_platform

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pyglet.window import Window


pytestmark = [
    require_platform(Platform.WINDOWS + Platform.OSX + Platform.LINUX),
    pytest.mark.skipif(pyglet.options.headless or pyglet.options.wayland,
                       reason='Requires a desktop cursor backend'),
]


@pytest.fixture
def test_window() -> Iterator[Window]:
    window = pyglet.window.Window(visible=False)
    try:
        yield window
    finally:
        window.close()


def test_set_image_mouse_cursor(test_window: Window, monkeypatch: pytest.MonkeyPatch) -> None:
    from pyglet.image import ImageData
    from pyglet.window import DefaultMouseCursor, ImageMouseCursor

    image = ImageData(8, 5, 'RGBA', b'\xff\x80\x00\x80' * 40)
    create = Mock(wraps=test_window._create_cursor_from_image)
    monkeypatch.setattr(test_window, '_create_cursor_from_image', create)

    native = ImageMouseCursor(image, 2, 1, acceleration=True)
    assert native.hw_drawable and not native.api_drawable
    test_window.set_mouse_cursor(native)
    create.assert_called_once_with(native)
    test_window._mouse_in_window = True
    test_window.draw(0)
    assert test_window._software_cursor is None

    software = ImageMouseCursor(image, 2, 1, acceleration=False)
    assert software.api_drawable and not software.hw_drawable
    test_window.set_mouse_cursor(software)
    assert create.call_count == 1

    test_window.set_mouse_cursor(None)
    assert isinstance(test_window._mouse_cursor, DefaultMouseCursor)


def test_software_cursor_hotspot(test_window: Window) -> None:
    from pyglet.image import ImageData
    from pyglet.window import ImageMouseCursor

    image = ImageData(8, 5, 'RGBA', b'\xff\x80\x00\x80' * 40)
    test_window.set_mouse_cursor(ImageMouseCursor(image, 2, 1, acceleration=False))
    assert test_window._software_cursor is None

    # Simulate a pointer in window coordinates and a transformed scene camera.
    test_window.camera.position = (100, 100)
    if pyglet.compat_platform in Platform.WINDOWS:
        test_window._mouse_scale = 2
        test_window._mouse_x, test_window._mouse_y = 80, 60
    else:
        test_window._mouse_x, test_window._mouse_y = 40, 30
    test_window._mouse_in_window = True
    test_window.draw(0)

    software_cursor = test_window._software_cursor
    assert software_cursor is not None
    sprite = software_cursor.sprite
    assert sprite.position == (40, 30, 0)
    assert (sprite.anchor_x, sprite.anchor_y) == (2, 1)
    camera = software_cursor.camera
    width, height = test_window.get_size()
    fb_width, fb_height = test_window.get_framebuffer_size()
    assert tuple(camera.world_to_screen(40, 30))[:2] == pytest.approx(
        (40 * fb_width / width, 30 * fb_height / height),
    )

    test_window.set_mouse_cursor()
    assert test_window._software_cursor is software_cursor


def test_software_cursor_reuses_sprite_when_image_changes(test_window: Window) -> None:
    from pyglet.image import ImageData
    from pyglet.window import ImageMouseCursor

    first = ImageMouseCursor(ImageData(8, 5, 'RGBA', bytes(160)), 2, 1, acceleration=False)
    second = ImageMouseCursor(ImageData(4, 7, 'RGBA', bytes(112)), 1, 4, acceleration=False)
    test_window.set_mouse_cursor(first)
    test_window._mouse_in_window = True
    test_window.draw(0)

    software_cursor = test_window._software_cursor
    assert software_cursor is not None
    sprite = software_cursor.sprite
    original_texture = sprite.image

    test_window.set_mouse_cursor()
    test_window.draw(0)
    assert sprite.image is original_texture

    test_window.set_mouse_cursor(second)
    test_window.draw(0)

    assert test_window._software_cursor is software_cursor
    assert software_cursor.sprite is sprite
    assert sprite.image is not original_texture
    assert (sprite.width, sprite.height) == (4, 7)
    assert (sprite.anchor_x, sprite.anchor_y) == (1, 4)


def test_software_cursor_uses_supplied_batch(test_window: Window) -> None:
    from pyglet.graphics import Batch
    from pyglet.image import ImageData
    from pyglet.window import ImageMouseCursor

    batch = Batch(test_window.context)
    image = ImageData(8, 5, 'RGBA', bytes(160))
    test_window.set_mouse_cursor(ImageMouseCursor(image, acceleration=False, batch=batch))
    test_window._mouse_in_window = True
    test_window.draw(0)

    software_cursor = test_window._software_cursor
    assert software_cursor is not None
    sprite = software_cursor.sprite
    assert sprite.batch is batch
    assert software_cursor.private_batch is None
    assert sprite.group is not None and not sprite.group.visible

    test_window.set_mouse_cursor(ImageMouseCursor(image, acceleration=False))
    test_window.draw(0)
    assert software_cursor.sprite is sprite
    assert sprite.batch is software_cursor.private_batch
    assert sprite.batch is not batch


def test_software_cursor_shared_by_independent_windows(test_window: Window) -> None:
    from pyglet.image import ImageData
    from pyglet.window import ImageMouseCursor, Window

    image = ImageData(8, 5, 'RGBA', b'\xff\x80\x00\xff' * 40)
    cursor = ImageMouseCursor(image, 2, 1, acceleration=False)
    second = Window(visible=False)
    try:
        for window in (test_window, second):
            window.set_mouse_cursor(cursor)
            window._mouse_in_window = True
            window.draw(0)

        first_cursor, second_cursor = test_window._software_cursor, second._software_cursor
        assert first_cursor is not None and second_cursor is not None
        assert first_cursor.sprite is not second_cursor.sprite
        assert first_cursor.sprite.image is not second_cursor.sprite.image
        assert first_cursor.batch is not second_cursor.batch

        test_window.set_mouse_cursor()
        second.draw(0)
        assert second._software_cursor is second_cursor
    finally:
        second.close()


def test_image_cursor_falls_back_when_native_creation_fails(
    test_window: Window, monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pyglet.image import ImageData
    from pyglet.window import ImageMouseCursor

    if pyglet.compat_platform in Platform.OSX:
        from pyglet.window.apple.cocoa import SystemCursor

        monkeypatch.setattr(test_window, '_mouse_in_content_rect', lambda: True)
        monkeypatch.setattr(SystemCursor, 'hide', Mock())
    create = Mock(return_value=None)
    monkeypatch.setattr(test_window, '_create_cursor_from_image', create)

    cursor = ImageMouseCursor(ImageData(8, 5, 'RGBA', b'\xff\x80\x00\xff' * 40))
    test_window.set_mouse_cursor(cursor)
    create.assert_called_once_with(cursor)
    assert cursor.hw_drawable
    assert test_window._software_cursor is None

    test_window._mouse_in_window = True
    test_window.draw(0)
    assert test_window._software_cursor is not None


def test_set_system_mouse_cursors(test_window: Window) -> None:
    from pyglet.window import MouseCursor

    try:
        for attribute in dir(test_window):
            if attribute.startswith('CURSOR_'):
                cursor = test_window.get_system_mouse_cursor(getattr(test_window, attribute))
                assert isinstance(cursor, MouseCursor)
                assert cursor.hw_drawable and not cursor.api_drawable
                test_window.set_mouse_cursor(cursor)
    finally:
        test_window.set_mouse_cursor()


@require_platform(Platform.OSX)
@pytest.mark.parametrize(('hotspot', 'expected'), [((2, 1), (2, 3)), ((20, -1), (7, 4))])
def test_cocoa_image_cursor_hotspot_and_visibility(
    test_window: Window, monkeypatch: pytest.MonkeyPatch, hotspot: tuple[int, int], expected: tuple[int, int],
) -> None:
    from pyglet.image import ImageData
    from pyglet.window import ImageMouseCursor
    from pyglet.window.apple.cocoa import SystemCursor

    inside = Mock(return_value=False)
    monkeypatch.setattr(test_window, '_mouse_in_content_rect', inside)
    hide, unhide = Mock(), Mock()
    monkeypatch.setattr(SystemCursor, 'hide', hide)
    monkeypatch.setattr(SystemCursor, 'unhide', unhide)

    image = ImageData(8, 5, 'RGBA', b'\xff\x80\x00\x80' * 40)
    cursor = ImageMouseCursor(image, *hotspot)
    try:
        test_window.set_mouse_cursor(cursor)
        native = test_window._image_cursor
        assert native is not None
        point = native.hotSpot()
        assert (point.x, point.y) == expected
        size = native.image().size()
        assert (size.width, size.height) == (8, 5)

        install = Mock()
        monkeypatch.setattr(native, 'set', install)
        inside.return_value = True
        test_window.set_mouse_cursor(cursor)
        assert test_window._image_cursor is native
        install.assert_called_once_with()

        test_window.set_mouse_cursor_visible(False)
        hide.assert_called_once_with()
        install.assert_called_once_with()
        unhide.reset_mock()
        test_window.set_mouse_cursor_visible(True)
        unhide.assert_called_once_with()
        assert install.call_count == 2
    finally:
        test_window.set_mouse_cursor()
        test_window.set_mouse_cursor_visible(True)

    assert test_window._image_cursor is None
