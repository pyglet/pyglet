"""Window pen events and contact lifecycle.

Used for all platforms.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from enum import IntFlag
from typing import Callable


class PenButton(IntFlag):
    """Pen button flags."""

    NONE = 0
    TIP = 1
    """Pen tip touching the surface."""
    SIDE = 2
    """Primary side button."""
    SECONDARY = 4
    """Secondary side button."""


@dataclass(slots=True)
class PenEvent:
    """A pen event dispatched from a platform."""
    # It's easier to dispatch this one event than 12 potential args

    pointer_id: int
    """Window local pen ID. May be reused after ``on_pen_leave``."""

    x: float
    """Horizontal position in window coordinates, measured from the left edge."""

    y: float
    """Vertical position in window coordinates, measured from the bottom edge."""

    pressure: float = 0.0
    """Tip pressure normalized to 0..1. (0 when unavailable or hovering)."""

    tilt_x: float = 0.0
    """Tilt from perpendicular in degrees, positive toward the display's right edge. 0 when unavailable."""

    tilt_y: float = 0.0
    """Tilt from perpendicular in degrees, positive toward the display's bottom edge. 0 when unavailable."""

    rotation: float = 0.0
    """Clockwise rotation in degrees. 0 when unavailable."""

    buttons: PenButton = PenButton.NONE
    """Combined :class:`PenButton` flags for tip contact and pen side buttons."""

    eraser: bool = False
    """Whether the tool is inverted or using an eraser tip."""

    in_contact: bool = False
    """Whether the tip touches the surface. Zero pressure does not necessarily mean hovering."""

    dx: float = 0.0
    """Horizontal movement since the previous pen event. 0 on entry."""

    dy: float = 0.0
    """Vertical movement since the previous pen event. 0 on entry."""


class PenState:
    """This object is to track different pen ID states separately from others.

    All pen states are tracked through this singular object in the Window.
    """

    pens: dict[int, PenEvent]

    def __init__(self) -> None:  # noqa: D107
        self.pens = {}

    def update(self, event: PenEvent, dispatch: Callable[[str, PenEvent], object]) -> None:
        previous = self.pens.get(event.pointer_id)
        event = replace(
            event, pressure=max(0.0, min(1.0, event.pressure)) if event.in_contact else 0.0,
            buttons=((PenButton(event.buttons) & ~PenButton.TIP)
                     | (PenButton.TIP if event.in_contact else PenButton.NONE)),
            dx=event.x - previous.x if previous else 0.0,
            dy=event.y - previous.y if previous else 0.0,
        )
        self.pens[event.pointer_id] = event
        if previous is None:
            dispatch('on_pen_enter', event)
            if self.pens.get(event.pointer_id) is not event:
                return
        if event.in_contact and (previous is None or not previous.in_contact):
            dispatch('on_pen_press', event)
        elif previous is not None and previous.in_contact and not event.in_contact:
            dispatch('on_pen_release', event)
        if self.pens.get(event.pointer_id) is not event:
            return
        dispatch('on_pen_motion', event)

    def leave(self, pointer_id: int, dispatch: Callable[[str, PenEvent], object]) -> None:
        event = self.pens.pop(pointer_id, None)
        if event is None:
            return
        released = replace(event, in_contact=False, pressure=0.0, buttons=PenButton.NONE, dx=0.0, dy=0.0)
        if event.in_contact:
            dispatch('on_pen_release', released)
        dispatch('on_pen_leave', released)

    def clear(self, dispatch: Callable[[str, PenEvent], object]) -> None:
        for pointer_id in tuple(self.pens):
            self.leave(pointer_id, dispatch)
