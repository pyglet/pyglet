from pyglet.window import BaseWindow, _PlatformEventHandler, _ViewEventHandler
from pyglet.window import WindowException, NoSuchDisplayException, MouseCursorException
from pyglet.window import MouseCursor, DefaultMouseCursor, ImageMouseCursor


from pyglet.libs.egl import egl


from pyglet.canvas.headless import HeadlessCanvas

# from pyglet.window import key
# from pyglet.window import mouse
from pyglet.event import EventDispatcher

# Platform event data is single item, so use platform event handler directly.
HeadlessEventHandler = _PlatformEventHandler
ViewEventHandler = _ViewEventHandler


class HeadlessWindow(BaseWindow):
    _egl_display_connection = None
    _egl_surface = None

    def _recreate(self, changes):
        pass

    def flip(self):
        if self.context:
            self.context.flip()

    def switch_to(self):
        if self.context:
            self.context.set_current()

    def set_caption(self, caption):
        pass

    def set_minimum_size(self, width, height):
        pass

    def set_maximum_size(self, width, height):
        pass

    def set_size(self, width, height):
        pass

    def get_size(self):
        return self._width, self._height

    def set_location(self, x, y):
        pass

    def get_location(self):
        pass

    def activate(self):
        pass

    def set_visible(self, visible=True):
        pass

    def minimize(self):
        pass

    def maximize(self):
        pass

    def set_vsync(self, vsync):
        pass

    def set_mouse_platform_visible(self, platform_visible=None):
        pass

    def set_exclusive_mouse(self, exclusive=True):
        pass

    def set_exclusive_keyboard(self, exclusive=True):
        pass

    def get_system_mouse_cursor(self, name):
        pass

    def dispatch_events(self):
        while self._event_queue:
            EventDispatcher.dispatch_event(self, *self._event_queue.pop(0))

    def dispatch_pending_events(self):
        pass

    def _create(self):
        self._egl_display_connection = self.display._display_connection

        if not self._egl_surface:
            pbuffer_attribs = (egl.EGL_WIDTH, self._width, egl.EGL_HEIGHT, self._height, egl.EGL_NONE)
            pbuffer_attrib_array = (egl.EGLint * len(pbuffer_attribs))(*pbuffer_attribs)
            self._egl_surface = egl.eglCreatePbufferSurface(self._egl_display_connection,
                                                            self.config._egl_config,
                                                            pbuffer_attrib_array)

            self.canvas = HeadlessCanvas(self.display, self._egl_surface)

            self.context.attach(self.canvas)

            self.dispatch_event('on_resize', self._width, self._height)


__all__ = ["HeadlessWindow"]
