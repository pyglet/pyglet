from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any, Literal

import pytest

if sys.platform != 'emscripten':
    pytest.skip('requires the Emscripten/Pyodide runtime', allow_module_level=True)

from js import Event, MouseEvent, Object, PointerEvent, window as browser_window
from pyodide.ffi import to_js

import pyglet
from pyglet.text.caret import Caret
from pyglet.text.document import UnformattedDocument
from pyglet.text.layout import IncrementalTextLayout
from pyglet.window import Window


@pytest.mark.parametrize('mode', ['platform', 'stretch'])
@pytest.mark.parametrize('ratio', [1, 2, 3])
def test_input_paths_share_window_coordinates(mode: Literal['platform', 'stretch'], ratio: int) -> None:
    descriptor = Object.getOwnPropertyDescriptor(browser_window, 'devicePixelRatio')
    previous_mode = pyglet.options.dpi_scaling
    Object.defineProperty(browser_window, 'devicePixelRatio', to_js(
        {'value': ratio, 'configurable': True}, dict_converter=Object.fromEntries,
    ))
    pyglet.options.dpi_scaling = mode
    window = Window(width=300, height=200, file_drops=True)
    try:
        canvas = window.canvas
        canvas.style.position = 'fixed'
        canvas.style.left = '40px'
        canvas.style.top = '60px'
        # Different CSS scaling on each axis must also be respected.
        canvas.style.width = '150px'
        canvas.style.height = '80px'
        event = SimpleNamespace(
            clientX=70, clientY=80, button=0, buttons=0, movementX=3, movementY=4,
            deltaX=1, deltaY=2, pointerId=42, width=5, height=6, pressure=0.5,
            shiftKey=False, ctrlKey=False, altKey=False, metaKey=False,
            preventDefault=lambda: None,
        )
        scale = 1 if mode == 'stretch' else ratio
        expected = (60 * scale, 150 * scale)
        events: list[tuple[Any, ...]] = []
        for handler, dispatch_name in (
            ('_event_mouse_down', 'on_mouse_press'),
            ('_event_mouse_up', 'on_mouse_release'),
            ('_event_mouse_scroll', 'on_mouse_scroll'),
            ('_event_mouse_motion', 'on_mouse_motion'),
            ('_event_mouse_enter', 'on_mouse_enter'),
            ('_event_mouse_leave', 'on_mouse_leave'),
        ):
            window.push_handlers(**{dispatch_name: lambda *args: events.append(args)})
            result = getattr(window, handler)(event)
            if result is not None:
                # These async handlers dispatch immediately and contain no awaits.
                with pytest.raises(StopIteration):
                    result.send(None)
            assert events[-1][:2] == pytest.approx(expected)
            if dispatch_name == 'on_mouse_motion':
                assert events[-1][2:] == pytest.approx((6 * scale, -10 * scale))
            window.pop_handlers()
        window.push_handlers(on_mouse_drag=lambda *args: events.append(args))
        event.buttons = 1
        with pytest.raises(StopIteration):
            window._event_mouse_motion(event).send(None)
        assert events[-1][:4] == pytest.approx((*expected, 6 * scale, -10 * scale))
        window.pop_handlers()
        assert window._drop_position(event) == pytest.approx(expected)
        event.dataTransfer = SimpleNamespace(types=SimpleNamespace(includes=lambda value: value == 'Files'))
        for handler, dispatch_name in (
            ('_event_file_drag_enter', 'on_file_drag_enter'),
            ('_event_file_drag_over', 'on_file_drag'),
        ):
            window.push_handlers(**{dispatch_name: lambda *args: events.append(args)})
            getattr(window, handler)(event)
            assert events[-1][:2] == pytest.approx(expected)
            window.pop_handlers()
        window.push_handlers(on_touch_start=lambda *args: events.append(args))
        window._dispatch_pointer_touch('on_touch_start', event)
        assert events[-1][1:3] == pytest.approx(expected)
        assert events[-1][5:7] == pytest.approx((10 * scale, 15 * scale))
    finally:
        window.close()
        pyglet.options.dpi_scaling = previous_mode
        Object.defineProperty(browser_window, 'devicePixelRatio', descriptor)


@pytest.mark.parametrize('mode', ['platform', 'stretch'])
def test_maximize_follows_browser_and_explicit_size_restores_layout(
    mode: Literal['platform', 'stretch'], monkeypatch: pytest.MonkeyPatch,
) -> None:
    descriptor = Object.getOwnPropertyDescriptor(browser_window, 'devicePixelRatio')
    previous_mode = pyglet.options.dpi_scaling
    pyglet.options.dpi_scaling = mode
    monkeypatch.setattr(pyglet.options.pyodide, 'canvas_id', f'maximize-test-{mode}')
    window = Window(width=300, height=200, resizable=True)
    canvas = window.canvas
    canvas.style.position = 'relative'
    canvas.style.left = '12px'
    events: list[str] = []
    window.push_handlers(on_resize=lambda *args: events.append('resize'),
                         on_scale=lambda *args: events.append('scale'))
    try:
        window.maximize()
        for ratio in (2, 3):
            Object.defineProperty(browser_window, 'devicePixelRatio', to_js(
                {'value': ratio, 'configurable': True}, dict_converter=Object.fromEntries,
            ))
            browser_window.dispatchEvent(Event.new('resize'))
            assert window.get_framebuffer_size() == (
                browser_window.innerWidth * ratio, browser_window.innerHeight * ratio,
            )
            size_scale = 1 if mode == 'stretch' else ratio
            assert window.get_size() == (
                browser_window.innerWidth * size_scale, browser_window.innerHeight * size_scale,
            )
            assert window.scale == ratio
            assert 'scale' in events
            assert 'resize' in events
            events.clear()
            window.maximize()
            browser_window.dispatchEvent(Event.new('resize'))
            assert events == []
        assert canvas.style.position == 'fixed'
        window.set_size(250, 150)
        assert canvas.style.position == 'relative'
        assert canvas.style.left == '12px'
        assert canvas.style.width == '250px'
        assert canvas.style.height == '150px'
        assert window.get_framebuffer_size() == (750, 450)
        browser_window.dispatchEvent(Event.new('resize'))
        assert window.get_framebuffer_size() == (750, 450)
    finally:
        window.close()
        canvas.remove()
        pyglet.options.dpi_scaling = previous_mode
        Object.defineProperty(browser_window, 'devicePixelRatio', descriptor)


def test_canvas_observer_updates_backing_buffer_without_changing_layout() -> None:
    from types import SimpleNamespace

    window = Window(width=300, height=200, resizable=True)
    try:
        canvas = window.canvas
        canvas.style.width = '150px'
        canvas.style.height = '100px'
        window._event_resized([SimpleNamespace(contentRect=SimpleNamespace(width=150, height=100))], None)
        assert window.get_framebuffer_size() == (round(150 * window.scale), round(100 * window.scale))
        assert canvas.style.width == '150px'
        assert canvas.style.height == '100px'
        window.camera.logical_size = (100, 100)
        assert window.camera.viewport[2:] == (round(100 * window.scale), round(100 * window.scale))
    finally:
        window.close()


@pytest.mark.parametrize('ratio', [1, 2, 3])
@pytest.mark.parametrize('mode', ['platform', 'stretch'])
def test_browser_dpi_scaling_preserves_drawing_input_and_caret(
    ratio: int, mode: Literal['platform', 'stretch'],
) -> None:
    descriptor = Object.getOwnPropertyDescriptor(browser_window, 'devicePixelRatio')
    previous_mode = pyglet.options.dpi_scaling
    Object.defineProperty(browser_window, 'devicePixelRatio', to_js(
        {'value': ratio, 'configurable': True}, dict_converter=Object.fromEntries,
    ))
    pyglet.options.dpi_scaling = mode
    window = Window(width=300, height=200)
    layout = IncrementalTextLayout(UnformattedDocument('hello'), width=200, height=40)
    caret = Caret(layout)
    try:
        scale = 1 if mode == 'stretch' else ratio
        assert window.get_size() == (300 * scale, 200 * scale)
        assert window.get_framebuffer_size() == (300 * ratio, 200 * ratio)
        assert window.camera.zoom == 1
        point = window.camera.world_to_screen(100, 50)
        assert (point.x, point.y) == pytest.approx((100 * ratio / scale, 50 * ratio / scale))
        points: list[tuple[Any, ...]] = []
        window.push_handlers(on_touch_start=lambda *args: points.append(args))
        rect = window.canvas.getBoundingClientRect()
        window.canvas.dispatchEvent(PointerEvent.new('pointerdown', to_js({
            'pointerId': 1, 'pointerType': 'touch', 'clientX': rect.left + rect.width / 2,
            'clientY': rect.top + rect.height / 2, 'cancelable': True,
        }, dict_converter=Object.fromEntries)))
        assert points[0][1:3] == pytest.approx((150 * scale, 100 * scale))
        layout.begin_text_input(window, caret)
        control = window._browser_text_input.control
        _, y, _, height = caret.rect
        assert control.getBoundingClientRect().top == pytest.approx(
            rect.top + rect.height - (y + height) / scale, abs=0.02,
        )
        # The hosted example also fits the canvas into a narrow phone viewport.
        window.canvas.style.width = '150px'
        window.canvas.style.height = '100px'
        rect = window.canvas.getBoundingClientRect()
        presses: list[tuple[Any, ...]] = []
        window.push_handlers(on_mouse_press=lambda *args: presses.append(args))
        window.canvas.dispatchEvent(MouseEvent.new('mousedown', to_js({
            'clientX': rect.left + 75, 'clientY': rect.top + 50, 'button': 0, 'cancelable': True,
        }, dict_converter=Object.fromEntries)))
        # MouseEvent rounds client coordinates to whole CSS pixels.
        assert presses[0][:2] == pytest.approx((150 * scale, 100 * scale), abs=2 * scale)
        window._browser_text_input.sync()
        assert control.getBoundingClientRect().top == pytest.approx(
            rect.top + rect.height - (y + height) / (2 * scale), abs=0.02,
        )
    finally:
        layout.end_text_input()
        caret.delete()
        layout.delete()
        window.close()
        pyglet.options.dpi_scaling = previous_mode
        Object.defineProperty(browser_window, 'devicePixelRatio', descriptor)
