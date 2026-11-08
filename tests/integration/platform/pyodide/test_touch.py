from __future__ import annotations

import sys
from collections.abc import Iterator
from typing import Any

import pytest

if sys.platform != "emscripten":
    pytest.skip("requires the Emscripten/Pyodide runtime", allow_module_level=True)

from js import Object, PointerEvent
from pyodide.ffi import to_js

from pyglet.window import Window

TouchWindow = tuple[Window, list[tuple[Any, ...]]]


@pytest.fixture
def touch_window() -> Iterator[TouchWindow]:
    window = Window(width=200, height=100)
    events: list[tuple[Any, ...]] = []

    def record_start(*args: Any) -> None:
        events.append(('on_touch_start', *args))

    def record_move(*args: Any) -> None:
        events.append(('on_touch_move', *args))

    def record_end(*args: Any) -> None:
        events.append(('on_touch_end', *args))

    window.push_handlers(on_touch_start=record_start, on_touch_move=record_move, on_touch_end=record_end)
    try:
        yield window, events
    finally:
        window.close()


def dispatch_pointer(window: Window, name: str, pointer_id: int = 1, x: float = 10, y: float = 20,
                     pointer_type: str = "touch") -> Any:
    canvas = window.canvas
    rect = canvas.getBoundingClientRect()
    event = PointerEvent.new(name, to_js({
        "pointerId": pointer_id,
        "pointerType": pointer_type,
        "clientX": rect.left + x,
        "clientY": rect.top + y,
        "width": 4,
        "height": 6,
        "pressure": 0.75,
        "cancelable": True,
    }, dict_converter=Object.fromEntries))
    canvas.dispatchEvent(event)
    return event


def test_touch_coordinates_contact_geometry_and_mouse_suppression(touch_window: TouchWindow) -> None:
    window, events = touch_window
    canvas = window.canvas
    # Exercise CSS scaling independently of the browser's device pixel ratio.
    canvas.width = 400
    canvas.height = 300
    canvas.style.width = "200px"
    canvas.style.height = "100px"

    start = dispatch_pointer(window, "pointerdown")
    assert start.defaultPrevented
    assert canvas.style.touchAction == "none"
    assert events == [('on_touch_start', 1, 20, 240, 0, 0, 8, 18, 0.75, 1.0)]

    dispatch_pointer(window, "pointermove", x=15, y=25)
    assert events[-1] == ('on_touch_move', 1, 30, 225, 10, -15, 8, 18, 0.75, 1.0)
    dispatch_pointer(window, "pointerup", x=15, y=25)
    assert events[-1][0] == 'on_touch_end'
    assert window._touch_positions == {}


def test_touch_contacts_share_delta_and_pinch_calculation(touch_window: TouchWindow) -> None:
    window, events = touch_window
    dispatch_pointer(window, "pointerdown", pointer_id=1, x=10)
    dispatch_pointer(window, "pointerdown", pointer_id=2, x=20)
    dispatch_pointer(window, "pointermove", pointer_id=1, x=5)
    assert events[-1][0:2] == ('on_touch_move', 1)
    assert events[-1][-1] == pytest.approx(1.5)
    dispatch_pointer(window, "pointerup", pointer_id=1, x=5)
    dispatch_pointer(window, "pointermove", pointer_id=2, x=30)
    assert events[-1][-1] == 1.0


@pytest.mark.parametrize('ending', ['pointerup', 'pointercancel', 'lostpointercapture'])
def test_touch_ending_cleans_up_once(touch_window: TouchWindow, ending: str) -> None:
    window, events = touch_window
    dispatch_pointer(window, "pointerdown", x=35, y=45)
    dispatch_pointer(window, ending, x=35, y=45)
    assert [event[0] for event in events] == ['on_touch_start', 'on_touch_end']
    assert events[-1][2:6] == (*events[0][2:4], 0, 0)
    assert window._touch_positions == {}
    dispatch_pointer(window, "lostpointercapture")
    dispatch_pointer(window, "pointermove")
    dispatch_pointer(window, "pointerup")
    assert len(events) == 2


@pytest.mark.parametrize('pointer_type', ['mouse', 'pen'])
def test_other_pointer_types_do_not_dispatch_touch(touch_window: TouchWindow, pointer_type: str) -> None:
    window, events = touch_window
    event = dispatch_pointer(window, "pointerdown", pointer_type=pointer_type)
    dispatch_pointer(window, "pointermove", pointer_type=pointer_type)
    dispatch_pointer(window, "pointerup", pointer_type=pointer_type)
    assert event.defaultPrevented == (pointer_type == 'pen')
    assert events == []


def test_unknown_touch_contacts_are_ignored(touch_window: TouchWindow) -> None:
    window, events = touch_window
    for name in ('pointermove', 'pointerup', 'pointercancel', 'lostpointercapture'):
        dispatch_pointer(window, name)
    assert events == []
    assert window._touch_positions == {}
