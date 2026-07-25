"""Highlight a drop zone while dragging files over a Window.

This example is intended for platforms that support file drag events.
"""

from __future__ import annotations

from pathlib import Path

import pyglet
from pyglet import shapes


class FileDragDropApp:
    zone_width = 460
    zone_height = 220

    zone_normal = (70, 70, 80, 255)
    zone_hover = (80, 170, 110, 255)
    zone_border_normal = (130, 130, 140, 255)
    zone_border_hover = (210, 240, 210, 255)

    def __init__(self) -> None:
        self.window = pyglet.window.Window(900, 600, caption="File Drag Drop Zone", file_drops=True)
        self.batch = pyglet.graphics.Batch()
        self.drag_paths: list[str] = []
        self.zone_hovered = False

        self.zone_x = (self.window.width - self.zone_width) // 2
        self.zone_y = (self.window.height - self.zone_height) // 2

        self.drop_zone = shapes.Rectangle(self.zone_x, self.zone_y,
                                          self.zone_width, self.zone_height,
                                          color=self.zone_normal, batch=self.batch)

        self.drop_zone_border = shapes.BorderedRectangle(self.zone_x, self.zone_y,
                                                        self.zone_width, self.zone_height,
                                                        border=4,
                                                        color=self.zone_normal,
                                                        border_color=self.zone_border_normal,
                                                        batch=self.batch)

        self.status_label = pyglet.text.Label("Drag one or more files into the window.",
                                              x=self.window.width // 2, y=self.window.height - 40,
                                              anchor_x='center', anchor_y='center',
                                              font_size=14, batch=self.batch)

        self.zone_label = pyglet.text.Label("Drop Inside This Area",
                                            x=self.window.width // 2, y=self.window.height // 2,
                                            anchor_x='center', anchor_y='center',
                                            font_size=18, weight="bold", batch=self.batch)

        self.result_label = pyglet.text.Label("",
                                              x=self.window.width // 2, y=70,
                                              width=self.window.width - 60,
                                              multiline=True,
                                              anchor_x='center', anchor_y='center',
                                              align='center',
                                              font_size=12, batch=self.batch)

        self.window.push_handlers(self)

    def _drop_hit_test(self, x: int, y: int) -> bool:
        """Returns True if the mouse coordinates intersect the drop zone area."""
        return (self.zone_x <= x <= self.zone_x + self.zone_width
                and self.zone_y <= y <= self.zone_y + self.zone_height)

    def _set_zone_hover(self, hovered: bool) -> None:
        self.zone_hovered = hovered

        if hovered:
            self.drop_zone.color = self.zone_hover
            self.drop_zone_border.border_color = self.zone_border_hover
        else:
            self.drop_zone.color = self.zone_normal
            self.drop_zone_border.border_color = self.zone_border_normal

    def on_draw(self) -> None:
        self.window.clear()
        self.batch.draw()

    def on_file_drag_enter(self, x: int, y: int, paths: list[str]) -> None:
        self.drag_paths = paths
        self._set_zone_hover(self._drop_hit_test(x, y))
        self.status_label.text = f"Dragging {len(paths)} file(s)..."

    def on_file_drag(self, x: int, y: int, paths: list[str]) -> None:
        self.drag_paths = paths
        self._set_zone_hover(self._drop_hit_test(x, y))

    def on_file_drag_exit(self) -> None:
        """Drag was lost or exited the window."""
        self.drag_paths = []
        self._set_zone_hover(False)
        self.status_label.text = "Drag one or more files into the window."

    def on_file_drop(self, x: int, y: int, paths: list[str]) -> None:
        self.drag_paths = []
        self._set_zone_hover(False)

        if self._drop_hit_test(x, y):
            basenames = ", ".join(Path(path).name for path in paths[:3])
            if len(paths) > 3:
                basenames += ", ..."
            self.status_label.text = "Drop accepted."
            self.result_label.text = f"Dropped {len(paths)} file(s): {basenames}"
        else:
            self.status_label.text = "Drop missed zone."
            self.result_label.text = "Drop happened outside the target area."


if __name__ == '__main__':
    file_drop = FileDragDropApp()
    pyglet.app.run()
