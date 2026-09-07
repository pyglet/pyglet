from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

import pyglet
from pyglet.enums import GraphicsAPI
from pyglet.event import EventDispatcher
from pyglet.libs.darwin.cocoapy import (
    NSRectEncoding,
    ObjCClass,
    ObjCInstance,
    PyObjectEncoding,
    CGRect,
    objc_classmethod,
    objc_method,
    send_super,
)
from pyglet.window import BaseWindow

if TYPE_CHECKING:
    from pyglet.graphics.api.base import SurfaceContext


UIWindow = ObjCClass('UIWindow')
UIView = ObjCClass('UIView')
UIViewController = ObjCClass('UIViewController')
UIScreen = ObjCClass('UIScreen')
CAMetalLayer = ObjCClass('CAMetalLayer')
CAEAGLLayer = ObjCClass('CAEAGLLayer')


class PygletIOSView(UIView):

    @objc_classmethod(b'@')
    def layerClass(cls) -> ObjCClass:
        """Use the graphics API's native UIKit backing layer."""
        return CAEAGLLayer if pyglet.options.backend in (
                    GraphicsAPI.OPENGL_ES_2,
                    GraphicsAPI.OPENGL_ES_3,
                ) else CAMetalLayer

    @objc_method(b'@' + NSRectEncoding + PyObjectEncoding)
    def initWithFrame_iosWindow_(self, frame: CGRect, window: IOSWindow) -> ObjCInstance | None:
        self = ObjCInstance(send_super(self, 'initWithFrame:', frame, argtypes=[CGRect]))
        if not self:
            return None
        self._window = window
        return self

    @objc_method('v')
    def layoutSubviews(self) -> None:
        # Recreate the drawable area after UIKit has assigned the view its size.
        send_super(self, 'layoutSubviews')
        self._window._view_did_resize()

class IOSWindow(BaseWindow):
    """A UIKit-backed window.

    A UIKit window is always full screen. UIKit determines the visible size
    and reports resize events through ``layoutSubviews``.

    The following functions do nothing for UIKit windows and will be ignored:
       * Window sizing. Including initial size, setting size, or min/max sizes.
       * Setting or getting location
       * Changing decorations.
       * Minimizing/maximizing.
       * Exclusive behavior, such as exclusive mouse and keyboard.
    """

    context: SurfaceContext
    _uiwindow: ObjCInstance | None = None
    _uiview: ObjCInstance | None = None
    _view_controller: ObjCInstance | None = None
    _ios_layer: ObjCInstance | None = None

    def _create(self) -> None:
        if self._uiwindow is not None:
            self._uiwindow.setHidden_(True)
            self._uiwindow.release()
            self._uiwindow = None

        scale = self.screen.get_scale()
        # Use the UIKit screen bounds so the view fills that scene.
        # IGnore
        frame = UIScreen.mainScreen().bounds()
        self._width = round(frame.size.width * scale)
        self._height = round(frame.size.height * scale)
        self._uiwindow = UIWindow.alloc().initWithFrame_(frame)
        self._uiview = PygletIOSView.alloc().initWithFrame_iosWindow_(frame, self)
        self._uiview.setContentScaleFactor_(scale)

        self._view_controller = UIViewController.alloc().init()
        self._view_controller.setView_(self._uiview)
        self._uiwindow.setRootViewController_(self._view_controller)

        self._ios_layer = self._uiview.layer()
        self._ios_layer.setContentsScale_(scale)

        if pyglet.options.backend and not self._shadow:
            self._assign_config()
            self.context.attach(self)

    def _recreate(self, changes: Sequence[str]) -> None:
        # Recreate only if a caller changes a property that requires a native surface replacement.
        self._create()

    def _view_did_resize(self) -> None:
        if self._uiview is None:
            return
        bounds = self._uiview.bounds()
        scale = self.screen.get_scale()
        width, height = round(bounds.size.width * scale), round(bounds.size.height * scale)
        if (width, height) != (self._width, self._height):
            self._width, self._height = width, height
            if self._context:
                self.context.update_geometry()
            self.dispatch_event('_on_internal_resize', width, height)
            self.dispatch_event('on_expose')

    def switch_to(self) -> None:
        if self._context:
            self.context.set_current()

    def set_caption(self, caption: str) -> None:
        self._caption = caption

    def set_size(self, width: int, height: int) -> None:
        # The OS decides a UIWindow's size; retain the requested size until
        # UIKit's next layout pass reports the actual drawable dimensions.
        self._width, self._height = int(width), int(height)
        self.dispatch_event('_on_internal_resize', self._width, self._height)

    def get_size(self) -> tuple[int, int]:
        return self._width, self._height

    def set_location(self, x: int, y: int) -> None:
        """Behavior not available on iOS."""
        return None

    def get_location(self) -> tuple[int, int]:
        """Behavior not available on iOS."""
        return 0, 0

    def activate(self) -> None:
        if self._uiwindow is not None:
            self._uiwindow.makeKeyAndVisible()

    def set_visible(self, visible: bool = True) -> None:
        super().set_visible(visible)
        if self._uiwindow is None:
            return
        self._uiwindow.setHidden_(not visible)
        if visible:
            self.dispatch_event('_on_internal_resize', self._width, self._height)
            self.dispatch_event('on_show')
            self.dispatch_event('on_expose')
        else:
            self.dispatch_event('on_hide')

    def minimize(self) -> None:
        """Behavior not available on iOS."""
        return None

    def maximize(self) -> None:
        """Behavior not available on iOS."""
        return None

    def set_minimum_size(self, width: int, height: int) -> None:
        super().set_minimum_size(width, height)

    def set_maximum_size(self, width: int, height: int) -> None:
        super().set_maximum_size(width, height)

    def set_vsync(self, vsync: bool) -> None:
        super().set_vsync(vsync)
        if self._context:
            self.context.set_vsync(vsync)

    def set_mouse_cursor_platform_visible(self, platform_visible: bool | None = None) -> None:
        return None

    def set_exclusive_mouse(self, exclusive: bool = True) -> None:
        self._mouse_exclusive = exclusive

    def set_exclusive_keyboard(self, exclusive: bool = True) -> None:
        self._keyboard_exclusive = exclusive

    def get_system_mouse_cursor(self, name: str):
        return None

    def dispatch_events(self) -> None:
        while self._event_queue:
            EventDispatcher.dispatch_event(self, *self._event_queue.popleft())

    def dispatch_pending_events(self) -> None:
        self.dispatch_events()

    def close(self) -> None:
        if self._uiwindow is not None:
            self._uiwindow.setHidden_(True)
            self._uiwindow.setRootViewController_(None)
            self._uiwindow.release()
            self._uiwindow = None
        if self._view_controller is not None:
            self._view_controller.release()
            self._view_controller = None
        self._uiview = None
        self._ios_layer = None
        super().close()


__all__ = ['IOSWindow']
