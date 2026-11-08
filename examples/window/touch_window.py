"""A simple example for touch and pen events.

Demonstrates multitouch to draw with multiple fingers as well.
"""
from __future__ import annotations
from collections import deque
from typing import ClassVar, TYPE_CHECKING

import pyglet
from pyglet import shapes

if TYPE_CHECKING:
    from pyglet.window.pen import PenEvent


class TouchExample:
    COLORS: ClassVar[list[tuple[int, int, int]]] = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (0, 255, 255),
        (255, 255, 0),
        (255, 0, 255),
        (255, 255, 255),
        (128, 128, 128)
    ]
    window: pyglet.window.Window
    batch: pyglet.graphics.Batch
    touch_circles: dict[int, shapes.Circle]
    pen_circles: dict[int, shapes.Circle]
    trails: deque[tuple[shapes.Line, float]]

    def __init__(self) -> None:
        self.window = pyglet.window.Window(500, 500, caption="Touch Example", resizable=True)
        self.batch = pyglet.graphics.Batch()
        self._counter = 0
        self._elapsed = 0.0

        self.touch_circles = {}
        self.pen_circles = {}
        self.trails = deque()

        self.window.push_handlers(self)
        if pyglet.compat_platform == 'emscripten':
            # Fit to mobile screen.
            self.window.maximize()
        pyglet.clock.schedule_interval(self.update, 1 / 60)

    def on_draw(self) -> None:
        self.window.clear()
        self.batch.draw()

    def update(self, dt: float) -> None:
        self._elapsed += dt
        while self.trails and self._elapsed - self.trails[0][1] >= 2.0:
            line, _ = self.trails.popleft()
            line.delete()
        for line, created in self.trails:
            line.opacity = int(220 * (1 - (self._elapsed - created) / 2.0))

    def on_touch_start(self, pointer_id: int, x: float, y: float, dx: float, dy: float,
                       width: float, height: float, pressure: float, scale: float) -> None:
        if pointer_id not in self.touch_circles:
            color = self.COLORS[self._counter % len(self.COLORS)]
            # Some platforms report a tiny contact area, or no dimensions at all.
            radius = max(20.0, max(width, height) / 2)
            self.touch_circles[pointer_id] = shapes.Circle(x, y, radius, color=color, batch=self.batch)
            self._counter += 1
        else:
            self.touch_circles[pointer_id].position = x, y

    def on_touch_move(self, pointer_id: int, x: float, y: float, dx: float, dy: float,
                      width: float, height: float, pressure: float, scale: float) -> None:
        if pointer_id in self.touch_circles:
            circle = self.touch_circles[pointer_id]
            if circle.position != (x, y):
                line = shapes.Line(*circle.position, x, y, thickness=8, color=circle.color, batch=self.batch)
                self.trails.append((line, self._elapsed))
                if len(self.trails) > 512:
                    oldest, _ = self.trails.popleft()
                    oldest.delete()
            circle.position = x, y
            circle.radius = max(20.0, max(width, height) / 2)

    def on_touch_end(self, pointer_id: int, x: float, y: float, dx: float, dy: float,
                     width: float, height: float, pressure: float, scale: float) -> None:
        if pointer_id in self.touch_circles:
            circle = self.touch_circles[pointer_id]
            circle.delete()
            del self.touch_circles[pointer_id]

    def on_pen_enter(self, pen_event: PenEvent) -> None:
        self.pen_circles[pen_event.pointer_id] = shapes.Circle(
            pen_event.x, pen_event.y, 8, color=(255, 190, 70, 100), batch=self.batch,
        )

    def on_pen_press(self, pen_event: PenEvent) -> None:
        circle = self.pen_circles[pen_event.pointer_id]
        circle.position = pen_event.x, pen_event.y
        circle.opacity = 255

    def on_pen_motion(self, pen_event: PenEvent) -> None:
        circle = self.pen_circles[pen_event.pointer_id]
        if pen_event.in_contact and circle.position != (pen_event.x, pen_event.y):
            color = (220, 220, 220) if pen_event.eraser else (255, 190, 70)
            line = shapes.Line(*circle.position, pen_event.x, pen_event.y,
                               thickness=2 + 18 * pen_event.pressure, color=color, batch=self.batch)
            self.trails.append((line, self._elapsed))
            if len(self.trails) > 512:
                oldest, _ = self.trails.popleft()
                oldest.delete()
        circle.position = pen_event.x, pen_event.y
        circle.radius = 8 + 10 * pen_event.pressure

    def on_pen_release(self, pen_event: PenEvent) -> None:
        circle = self.pen_circles.get(pen_event.pointer_id)
        if circle is None:
            return
        circle.position = pen_event.x, pen_event.y
        circle.opacity = 100

    def on_pen_leave(self, pen_event: PenEvent) -> None:
        circle = self.pen_circles.pop(pen_event.pointer_id, None)
        if circle is not None:
            circle.delete()


touch_example = TouchExample()

pyglet.app.run()
