from __future__ import annotations

from typing import Sequence

import pyglet
# from pyglet.window import key
# from pyglet.window import mouse
from pyglet.event import EventDispatcher
from pyglet.libs.egl import eglCreatePbufferSurface, EGLint, EGL_WIDTH, EGL_HEIGHT, EGL_NONE
from pyglet.window import (
    BaseWindow,
    _PlatformEventHandler,
    _ViewEventHandler,
)

# Platform event data is single item, so use platform event handler directly.
HeadlessEventHandler = _PlatformEventHandler
ViewEventHandler = _ViewEventHandler


class HeadlessWindow(BaseWindow):
    _egl_display_connection = None
    _egl_surface = None

    def _recreate(self, changes: Sequence[str]) -> None:
        pass

    def flip(self) -> None:
        if self.context:
            self.context.flip()

    def switch_to(self) -> None:
        if self.context:
            self.context.set_current()

    def before_draw(self) -> None:
        if self.context:
            self.context.before_draw()

    def set_caption(self, caption: str) -> None:
        pass

    def set_minimum_size(self, width: int, height: int) -> None:
        pass

    def set_maximum_size(self, width: int, height: int) -> None:
        pass

    def set_size(self, width: int, height: int) -> None:
        pass

    def get_size(self) -> tuple[int, int]:
        return self._width, self._height

    def set_location(self, x: int, y: int) -> None:
        pass

    def get_location(self) -> None:
        pass

    def activate(self) -> None:
        pass

    def set_visible(self, visible: bool = True) -> None:
        pass

    def minimize(self) -> None:
        pass

    def maximize(self) -> None:
        pass

    def set_vsync(self, vsync: bool) -> None:
        pass

    def set_mouse_cursor_platform_visible(self, platform_visible: bool | None = None) -> None:
        pass

    def set_exclusive_mouse(self, exclusive: bool = True) -> None:
        pass

    def set_exclusive_keyboard(self, exclusive: bool = True) -> None:
        pass

    def get_system_mouse_cursor(self, name: str) -> None:
        pass

    def dispatch_events(self) -> None:
        while self._event_queue:
            EventDispatcher.dispatch_event(self, *self._event_queue.pop(0))

    def dispatch_pending_events(self) -> None:
        pass

    def _create(self) -> None:
        self._egl_display_connection = self.display._display_connection  # noqa: SLF001
        if pyglet.options.backend and not self._egl_surface:
            self._assign_config()
            pbuffer_attribs = (EGL_WIDTH, self._width, EGL_HEIGHT, self._height, EGL_NONE)
            pbuffer_attrib_array = (EGLint * len(pbuffer_attribs))(*pbuffer_attribs)
            self._egl_surface = eglCreatePbufferSurface(self._egl_display_connection,
                                                            self.config._egl_config,  # noqa: SLF001
                                                            pbuffer_attrib_array)
            self.context.attach(self)

            self.dispatch_event('_on_internal_resize', self._width, self._height)


__all__ = ['HeadlessWindow']
