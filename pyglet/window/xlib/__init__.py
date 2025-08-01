from __future__ import annotations

import locale
import sys
import unicodedata
import urllib.parse
from ctypes import (
    POINTER,
    Structure,
    byref,
    c_buffer,
    c_char_p,
    c_int,
    c_int32,
    c_ubyte,
    c_uint,
    c_uint32,
    c_ulong,
    c_void_p,
    cast,
    create_string_buffer,
    memmove,
    pointer,
    sizeof,
    string_at,
)
from functools import lru_cache
from typing import TYPE_CHECKING, Sequence

import pyglet
from pyglet.display.xlib import XlibCanvas
from pyglet.event import EventDispatcher
from pyglet.libs.x11 import cursorfont, xlib
from pyglet.util import asbytes
from pyglet.window import (
    BaseWindow,
    DefaultMouseCursor,
    ImageMouseCursor,
    MouseCursor,
    MouseCursorException,
    WindowException,
    _PlatformEventHandler,
    _ViewEventHandler,
    key,
    mouse,
)

if TYPE_CHECKING:
    from _ctypes import _Pointer
    from pyglet.gl.xlib import XlibDisplayConfig

try:
    from pyglet.libs.x11 import xsync

    _have_xsync = True
except ImportError:
    _have_xsync = False

_debug = pyglet.options['debug_x11']


class mwmhints_t(Structure):
    _fields_ = [
        ('flags', c_uint32),
        ('functions', c_uint32),
        ('decorations', c_uint32),
        ('input_mode', c_int32),
        ('status', c_uint32),
    ]


# XXX: wraptypes can't parse the header this function is in yet
XkbSetDetectableAutoRepeat = xlib._lib.XkbSetDetectableAutoRepeat  # noqa: SLF001
XkbSetDetectableAutoRepeat.restype = c_int
XkbSetDetectableAutoRepeat.argtypes = [POINTER(xlib.Display), c_int, POINTER(c_int)]
_can_detect_autorepeat = None

XA_CARDINAL = 6  # Xatom.h:14
XA_ATOM = 4
XA_STRING = 31

XDND_VERSION = 5

_have_utf8: bool = locale.getlocale()[1] == 'UTF-8'

# symbol,ctrl -> motion mapping
_motion_map: dict[tuple[int, bool], int] = {
    (key.UP, False): key.MOTION_UP,
    (key.RIGHT, False): key.MOTION_RIGHT,
    (key.DOWN, False): key.MOTION_DOWN,
    (key.LEFT, False): key.MOTION_LEFT,
    (key.RIGHT, True): key.MOTION_NEXT_WORD,
    (key.LEFT, True): key.MOTION_PREVIOUS_WORD,
    (key.HOME, False): key.MOTION_BEGINNING_OF_LINE,
    (key.END, False): key.MOTION_END_OF_LINE,
    (key.PAGEUP, False): key.MOTION_PREVIOUS_PAGE,
    (key.PAGEDOWN, False): key.MOTION_NEXT_PAGE,
    (key.HOME, True): key.MOTION_BEGINNING_OF_FILE,
    (key.END, True): key.MOTION_END_OF_FILE,
    (key.BACKSPACE, False): key.MOTION_BACKSPACE,
    (key.DELETE, False): key.MOTION_DELETE,
    (key.C, True): key.MOTION_COPY,
    (key.V, True): key.MOTION_PASTE,
}


class XlibException(WindowException):
    """An X11-specific exception.

    This exception is probably a programming error in pyglet."""


class XlibMouseCursor(MouseCursor):
    gl_drawable: bool = False
    hw_drawable: bool = True

    def __init__(self, cursor: xlib.Cursor) -> None:
        self.cursor = cursor


# Platform event data is single item, so use platform event handler directly.
XlibEventHandler = _PlatformEventHandler
ViewEventHandler = _ViewEventHandler


class XlibWindow(BaseWindow):
    config: XlibDisplayConfig
    _x_display: xlib.Display | None = None  # X display connection
    _x_screen_id: int | None = None  # X screen index
    _x_ic: xlib.XIC | None = None  # X input context
    _window: xlib.Window | None = None  # Xlib window handle
    _override_redirect: bool = False

    _x: int = 0
    _y: int = 0  # Last known window position
    _mouse_exclusive_client: tuple[int, int] | None = None  # x,y of "real" mouse during exclusive
    _mouse_buttons: list[bool] = [False] * 6  # State of each xlib button
    _active: bool = True
    _applied_mouse_exclusive: bool | None = False
    _applied_keyboard_exclusive: bool = False
    _mapped: bool = False
    _lost_context: bool = False
    _lost_context_state: bool = False

    _enable_xsync: bool = False
    _current_sync_value: xsync.XSyncValue | None = None
    _current_sync_valid: bool = False

    _default_event_mask: int = (0x1ffffff & ~xlib.PointerMotionHintMask
                                & ~xlib.ResizeRedirectMask
                                & ~xlib.SubstructureNotifyMask)

    def __init__(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        # Bind event handlers
        self._event_handlers = {}
        self._view_event_handlers = {}
        for name in self._platform_event_names:
            if not hasattr(self, name):
                continue
            func = getattr(self, name)
            for message in func._platform_event_data:  # noqa: SLF001
                if hasattr(func, '_view'):
                    self._view_event_handlers[message] = func
                else:
                    self._event_handlers[message] = func

        super().__init__(*args, **kwargs)

        global _can_detect_autorepeat  # noqa: PLW0603
        if _can_detect_autorepeat is None:
            supported_rtrn = c_int()
            _can_detect_autorepeat = XkbSetDetectableAutoRepeat(self.display._display, c_int(1),  # noqa: SLF001
                                                                byref(supported_rtrn))
        if _can_detect_autorepeat:
            self.pressed_keys = set()

        # Store clipboard string to not query as much for pasting a lot.
        self._clipboard_str: str | None = None

    def _recreate(self, changes: Sequence[str]) -> None:
        # If flipping to/from fullscreen, need to recreate the window.  (This
        # is the case with both override_redirect method and
        # _NET_WM_STATE_FULLSCREEN).
        #
        # A possible improvement could be to just hide the top window,
        # destroy the GLX window, and reshow it again when leaving fullscreen.
        # This would prevent the floating window from being moved by the
        # WM.
        if 'fullscreen' in changes or 'resizable' in changes:
            # clear out the GLX context
            self.context.detach()
            xlib.XDestroyWindow(self._x_display, self._window)
            del self.display._window_map[self._window]  # noqa: SLF001
            del self.display._window_map[self._view]  # noqa: SLF001
            self._window = None
            self._mapped = False

        # TODO: detect state loss only by examining context share.
        if 'context' in changes:
            self._lost_context = True
            self._lost_context_state = True

        self._create()

    def _create_xdnd_atoms(self, display: xlib.Display) -> None:
        self._xdnd_atoms = {
            'XdndAware': xlib.XInternAtom(display, asbytes('XdndAware'), False),
            'XdndEnter': xlib.XInternAtom(display, asbytes('XdndEnter'), False),
            'XdndTypeList': xlib.XInternAtom(display, asbytes('XdndTypeList'), False),
            'XdndDrop': xlib.XInternAtom(display, asbytes('XdndDrop'), False),
            'XdndFinished': xlib.XInternAtom(display, asbytes('XdndFinished'), False),
            'XdndSelection': xlib.XInternAtom(display, asbytes('XdndSelection'), False),
            'XdndPosition': xlib.XInternAtom(display, asbytes('XdndPosition'), False),
            'XdndStatus': xlib.XInternAtom(display, asbytes('XdndStatus'), False),
            'XdndActionCopy': xlib.XInternAtom(display, asbytes('XdndActionCopy'), False),
            'text/uri-list': xlib.XInternAtom(display, asbytes('text/uri-list'), False),
        }

    def _create(self) -> None:
        # Unmap existing window if necessary while we fiddle with it.
        if self._window and self._mapped:
            self._unmap()

        self._x_display = self.display._display  # noqa: SLF001
        self._x_screen_id = self.display.x_screen

        # Create X window if not already existing.
        if not self._window:
            root = xlib.XRootWindow(self._x_display, self._x_screen_id)

            visual_info = self.config.get_visual_info()

            visual = visual_info.visual
            visual_id = xlib.XVisualIDFromVisual(visual)
            default_visual = xlib.XDefaultVisual(self._x_display, self._x_screen_id)
            default_visual_id = xlib.XVisualIDFromVisual(default_visual)
            window_attributes = xlib.XSetWindowAttributes()
            if visual_id != default_visual_id:
                window_attributes.colormap = xlib.XCreateColormap(self._x_display, root,
                                                                  visual, xlib.AllocNone)
            else:
                window_attributes.colormap = xlib.XDefaultColormap(self._x_display,
                                                                   self._x_screen_id)
            window_attributes.bit_gravity = xlib.StaticGravity

            # Issue 287: Compiz on Intel/Mesa doesn't draw window decoration
            #            unless CWBackPixel is given in mask.  Should have
            #            no effect on other systems, so it's set
            #            unconditionally.
            mask = xlib.CWColormap | xlib.CWBitGravity | xlib.CWBackPixel

            self._dpi = self._screen.get_dpi()
            self._scale = self._screen.get_scale() if pyglet.options.dpi_scaling == "stretch" else 1.0

            if self.style in ('transparent', 'overlay'):
                mask |= xlib.CWBorderPixel
                window_attributes.border_pixel = 0
                window_attributes.background_pixel = 0

            if self._fullscreen:
                width, height = self.screen.width, self.screen.height
                self._view_x = (width - self._width) // 2
                self._view_y = (height - self._height) // 2
            else:
                width, height = self._width, self._height
                self._view_x = self._view_y = 0
                if pyglet.options.dpi_scaling in ("scaled", "stretch"):
                    w, h = self.get_requested_size()
                    self._width = width = int(w * self.scale)
                    self._height = height = int(h * self.scale)

            self._window = xlib.XCreateWindow(self._x_display, root,
                                              0, 0, width, height, 0, visual_info.depth,
                                              xlib.InputOutput, visual, mask,
                                              byref(window_attributes))
            self._view = xlib.XCreateWindow(self._x_display,
                                            self._window, self._view_x, self._view_y,
                                            self._width, self._height, 0, visual_info.depth,
                                            xlib.InputOutput, visual, mask,
                                            byref(window_attributes))
            xlib.XMapWindow(self._x_display, self._view)
            xlib.XSelectInput(self._x_display, self._view, self._default_event_mask)

            self.display._window_map[self._window] = self.dispatch_platform_event  # noqa: SLF001
            self.display._window_map[self._view] = self.dispatch_platform_event_view

            self.canvas = XlibCanvas(self.display, self._view)

            self.context.attach(self.canvas)
            self.context.set_vsync(self._vsync)  # XXX ?

            self._enable_xsync = self.display._enable_xsync and self.config.double_buffer

            # Set supported protocols
            protocols = list()
            protocols.append(xlib.XInternAtom(self._x_display, asbytes('WM_DELETE_WINDOW'), False))
            if self._enable_xsync:
                protocols.append(xlib.XInternAtom(self._x_display,
                                                  asbytes('_NET_WM_SYNC_REQUEST'),
                                                  False))
            protocols = (c_ulong * len(protocols))(*protocols)
            xlib.XSetWMProtocols(self._x_display, self._window, protocols, len(protocols))

            # Overlay should allow mouse to pass through and stay on top.
            if self._style == "overlay":
                self.set_mouse_passthrough(True)
                self._set_wm_state("_NET_WM_STATE_ABOVE")

            # Create window resize sync counter
            if self._enable_xsync:
                value = xsync.XSyncValue()
                self._sync_counter = xlib.XID(xsync.XSyncCreateCounter(self._x_display, value))
                atom = xlib.XInternAtom(self._x_display,
                                        asbytes('_NET_WM_SYNC_REQUEST_COUNTER'), False)
                ptr = pointer(self._sync_counter)

                xlib.XChangeProperty(self._x_display, self._window,
                                     atom, XA_CARDINAL, 32,
                                     xlib.PropModeReplace,
                                     cast(ptr, POINTER(c_ubyte)), 1)

            # Atoms required for Xdnd
            self._create_xdnd_atoms(self._x_display)

            # Clipboard related atoms
            self._clipboard_atom = xlib.XInternAtom(self._x_display, asbytes('CLIPBOARD'), False)
            self._utf8_atom = xlib.XInternAtom(self._x_display, asbytes('UTF8_STRING'), False)
            self._target_atom = xlib.XInternAtom(self._x_display, asbytes('TARGETS'), False)
            self._incr_atom = xlib.XInternAtom(self._x_display, asbytes('INCR'), False)

            # Support for drag and dropping files needs to be enabled.
            if self._file_drops:
                # Some variables set because there are 4 different drop events that need shared data.
                self._xdnd_source = None
                self._xdnd_version = None
                self._xdnd_format = None
                self._xdnd_position = (0, 0)  # For position callback.

                _version = c_ulong(int(XDND_VERSION))
                ptr = pointer(_version)

                xlib.XChangeProperty(self._x_display, self._window,
                                     self._xdnd_atoms['XdndAware'], XA_ATOM, 32,
                                     xlib.PropModeReplace,
                                     cast(ptr, POINTER(c_ubyte)), 1)

        # Set window attributes
        attributes = xlib.XSetWindowAttributes()
        attributes_mask = 0

        if self._fullscreen:
            self._set_wm_state('_NET_WM_STATE_FULLSCREEN')

        if self._fullscreen:
            xlib.XMoveResizeWindow(self._x_display, self._window,
                                   self.screen.x, self.screen.y,
                                   self.screen.width, self.screen.height)
        else:
            xlib.XResizeWindow(self._x_display, self._window, self._width, self._height)

        xlib.XChangeWindowAttributes(self._x_display, self._window,
                                     attributes_mask, byref(attributes))

        # Set style
        styles = {
            self.WINDOW_STYLE_DEFAULT: '_NET_WM_WINDOW_TYPE_NORMAL',
            self.WINDOW_STYLE_DIALOG: '_NET_WM_WINDOW_TYPE_DIALOG',
            self.WINDOW_STYLE_TOOL: '_NET_WM_WINDOW_TYPE_UTILITY',
        }
        if self._style in styles:
            self._set_atoms_property('_NET_WM_WINDOW_TYPE', (styles[self._style],))
        elif self._style in (self.WINDOW_STYLE_BORDERLESS, self.WINDOW_STYLE_OVERLAY):
            MWM_HINTS_DECORATIONS = 1 << 1
            PROP_MWM_HINTS_ELEMENTS = 5
            mwmhints = mwmhints_t()
            mwmhints.flags = MWM_HINTS_DECORATIONS
            mwmhints.decorations = 0
            name = xlib.XInternAtom(self._x_display, asbytes('_MOTIF_WM_HINTS'), False)
            xlib.XChangeProperty(self._x_display, self._window,
                                 name, name, 32, xlib.PropModeReplace,
                                 cast(pointer(mwmhints), POINTER(c_ubyte)),
                                 PROP_MWM_HINTS_ELEMENTS)

        # Set resizeable
        if not self._resizable and not self._fullscreen:
            self.set_minimum_size(self._width, self._height)
            self.set_maximum_size(self._width, self._height)

        # Set caption
        self.set_caption(self._caption)

        # Set WM_CLASS for modern desktop environments
        self.set_wm_class(self._caption)

        # this is supported by some compositors (ie gnome-shell), and more to come
        # see: http://standards.freedesktop.org/wm-spec/wm-spec-latest.html#idp6357888
        _NET_WM_BYPASS_COMPOSITOR_HINT_ON = c_ulong(int(self._fullscreen))
        name = xlib.XInternAtom(self._x_display, asbytes('_NET_WM_BYPASS_COMPOSITOR'), False)
        ptr = pointer(_NET_WM_BYPASS_COMPOSITOR_HINT_ON)

        xlib.XChangeProperty(self._x_display, self._window,
                             name, XA_CARDINAL, 32,
                             xlib.PropModeReplace,
                             cast(ptr, POINTER(c_ubyte)), 1)

        # Create input context.  A good but very outdated reference for this
        # is http://www.sbin.org/doc/Xlib/chapt_11.html
        if _have_utf8 and not self._x_ic:
            if not self.display._x_im:  # noqa: SLF001
                xlib.XSetLocaleModifiers(asbytes('@im=none'))
                self.display._x_im = xlib.XOpenIM(self._x_display, None, None, None)  # noqa: SLF001

            xlib.XFlush(self._x_display)

            # Need to set argtypes on this function because its vararg,
            # and ctypes guesses wrong.
            xlib.XCreateIC.argtypes = [xlib.XIM,
                                       c_char_p, c_int,
                                       c_char_p, xlib.Window,
                                       c_char_p, xlib.Window,
                                       c_void_p]
            self._x_ic = xlib.XCreateIC(self.display._x_im,  # noqa: SLF001
                                        asbytes('inputStyle'),
                                        xlib.XIMPreeditNothing | xlib.XIMStatusNothing,
                                        asbytes('clientWindow'), self._window,
                                        asbytes('focusWindow'), self._window,
                                        None)

            filter_events = c_ulong()
            xlib.XGetICValues(self._x_ic, 'filterEvents', byref(filter_events), None)
            self._default_event_mask |= filter_events.value
            xlib.XSetICFocus(self._x_ic)

        self.switch_to()
        if self._visible:
            self.set_visible(True)

        self.set_mouse_platform_visible()
        self._applied_mouse_exclusive = None
        self._update_exclusivity()

    def set_mouse_passthrough(self, state: bool) -> None:
        """Sets the clickable area in the application to an empty region if enabled."""
        if state:
            region = xlib.XCreateRegion()
            xsync.XShapeCombineRegion(self._x_display, self._window, xsync.ShapeInput, 0, 0, region, xsync.ShapeSet)
            xlib.XDestroyRegion(region)
        else:
            # Reset input shape to default
            xsync.XShapeCombineMask(self._x_display, self._window, xsync.ShapeInput, 0, 0, 0, xsync.ShapeSet)

    def _map(self) -> None:
        if self._mapped:
            return

        # Map the window, wait for map event before continuing.
        xlib.XSelectInput(self._x_display, self._window, xlib.StructureNotifyMask)
        xlib.XMapRaised(self._x_display, self._window)
        e = xlib.XEvent()
        while True:
            xlib.XNextEvent(self._x_display, e)
            if e.type == xlib.ConfigureNotify:
                self._width = e.xconfigure.width
                self._height = e.xconfigure.height
            elif e.type == xlib.MapNotify:
                break
        xlib.XSelectInput(self._x_display, self._window, self._default_event_mask)
        self._mapped = True

        self._update_view_size()

        self.dispatch_event('_on_internal_resize', self._width, self._height)
        self.dispatch_event('on_show')
        self.dispatch_event('on_expose')

    def _unmap(self) -> None:
        if not self._mapped:
            return

        xlib.XSelectInput(self._x_display, self._window, xlib.StructureNotifyMask)
        xlib.XUnmapWindow(self._x_display, self._window)
        e = xlib.XEvent()
        while True:
            xlib.XNextEvent(self._x_display, e)
            if e.type == xlib.UnmapNotify:
                break

        xlib.XSelectInput(self._x_display, self._window, self._default_event_mask)
        self._mapped = False

    def _get_root(self) -> xlib.Window:
        attributes = xlib.XWindowAttributes()
        xlib.XGetWindowAttributes(self._x_display, self._window, byref(attributes))
        return attributes.root

    def _is_reparented(self) -> bool:
        root = c_ulong()
        parent = c_ulong()
        children = pointer(c_ulong())
        n_children = c_uint()

        xlib.XQueryTree(self._x_display, self._window,
                        byref(root), byref(parent), byref(children),
                        byref(n_children))

        return root.value != parent.value

    def close(self) -> None:
        if not self._window:
            return

        self.context.destroy()
        self._unmap()
        if self._window:
            xlib.XDestroyWindow(self._x_display, self._window)

        del self.display._window_map[self._window]  # noqa: SLF001
        del self.display._window_map[self._view]
        self._window = None

        self._view_event_handlers.clear()
        self._event_handlers.clear()

        if _have_utf8:
            xlib.XDestroyIC(self._x_ic)
            self._x_ic = None

        super().close()

    def switch_to(self) -> None:
        if self.context:
            self.context.set_current()

    def flip(self):
        self.draw_mouse_cursor()

        # TODO canvas.flip?
        if self.context:
            self.context.flip()

        self._sync_resize()

    def set_vsync(self, vsync: bool) -> None:
        if pyglet.options['vsync'] is not None:
            vsync = pyglet.options['vsync']

        super().set_vsync(vsync)
        self.context.set_vsync(vsync)

    def set_caption(self, caption: str) -> None:
        if caption is None:
            caption = ''
        self._caption = caption
        self._set_text_property('WM_NAME', caption, allow_utf8=False)
        self._set_text_property('WM_ICON_NAME', caption, allow_utf8=False)
        self._set_text_property('_NET_WM_NAME', caption)
        self._set_text_property('_NET_WM_ICON_NAME', caption)

    def set_wm_class(self, name: str) -> None:
        # WM_CLASS can only contain Ascii characters
        try:
            name = name.encode('ascii')
        except UnicodeEncodeError:
            name = 'pyglet'

        hint = xlib.XAllocClassHint()
        hint.contents.res_class = asbytes(name)
        hint.contents.res_name = asbytes(name.lower())
        xlib.XSetClassHint(self._x_display, self._window, hint.contents)
        xlib.XFree(hint)

    def get_caption(self) -> str:
        return self._caption

    def set_size(self, width: int, height: int) -> None:
        super().set_size(width, height)
        if not self._resizable:
            self.set_minimum_size(width, height)
            self.set_maximum_size(width, height)
        xlib.XResizeWindow(self._x_display, self._window, width, height)
        self._update_view_size()
        self.dispatch_event('_on_internal_resize', width, height)

    def _update_view_size(self) -> None:
        xlib.XResizeWindow(self._x_display, self._view, self._width, self._height)

    def set_location(self, x: int, y: int) -> None:
        if self._is_reparented():
            # Assume the window manager has reparented our top-level window
            # only once, in which case attributes.x/y give the offset from
            # the frame to the content window.  Better solution would be
            # to use _NET_FRAME_EXTENTS, where supported.
            attributes = xlib.XWindowAttributes()
            xlib.XGetWindowAttributes(self._x_display, self._window, byref(attributes))
            # XXX at least under KDE's WM these attrs are both 0
            x -= attributes.x
            y -= attributes.y
        xlib.XMoveWindow(self._x_display, self._window, x, y)

    def get_location(self) -> tuple[int, int]:
        child = xlib.Window()
        x = c_int()
        y = c_int()
        xlib.XTranslateCoordinates(self._x_display,
                                   self._window,
                                   self._get_root(),
                                   0, 0,
                                   byref(x),
                                   byref(y),
                                   byref(child))
        return x.value, y.value

    def get_framebuffer_size(self) -> tuple[int, int]:
        return self._width, self._height

    def get_size(self) -> tuple[int, int]:
        if pyglet.options.dpi_scaling == "stretch":
            return int(self._width / self.scale), int(self._height / self.scale)

        return self._width, self._height

    def activate(self) -> None:
        # Issue 218
        if self._x_display and self._window:
            xlib.XSetInputFocus(self._x_display, self._window, xlib.RevertToParent, xlib.CurrentTime)

    def set_visible(self, visible: bool = True) -> None:
        super().set_visible(visible)

        if visible:
            self._map()
        else:
            self._unmap()

    def set_minimum_size(self, width: int, height: int) -> None:
        super().set_minimum_size(width, height)
        self._set_wm_normal_hints()

    def set_maximum_size(self, width: int, height: int) -> None:
        super().set_maximum_size(width, height)
        self._set_wm_normal_hints()

    def minimize(self) -> None:
        xlib.XIconifyWindow(self._x_display, self._window, self._x_screen_id)

    def maximize(self) -> None:
        self._set_wm_state('_NET_WM_STATE_MAXIMIZED_HORZ',
                           '_NET_WM_STATE_MAXIMIZED_VERT')

    @staticmethod
    def _downsample_1bit(pixelarray: list) -> bytes:
        byte_list = []
        value = 0

        for i, pixel in enumerate(pixelarray):
            index = i % 8
            if pixel:
                value |= 1 << index
            if index == 7:
                byte_list.append(value)
                value = 0

        return bytes(byte_list)

    @lru_cache  # noqa: B019
    def _create_cursor_from_image(self, cursor: ImageMouseCursor) -> xlib.Cursor:
        """Creates platform cursor from an ImageCursor instance."""
        texture = cursor.texture
        width = texture.width
        height = texture.height

        alpha_luma_bytes = texture.get_image_data().get_data('AL', -width * 2)
        mask_data = self._downsample_1bit(alpha_luma_bytes[0::2])
        bmp_data = self._downsample_1bit(alpha_luma_bytes[1::2])

        bitmap = xlib.XCreateBitmapFromData(self._x_display, self._window, bmp_data, width, height)
        mask = xlib.XCreateBitmapFromData(self._x_display, self._window, mask_data, width, height)
        white = xlib.XColor(red=65535, green=65535, blue=65535)  # background color
        black = xlib.XColor()  # foreground color

        # hot_x/y must be within the image dimension, or the cursor will not display:
        hot_x = min(max(0, int(self._mouse_cursor.hot_x)), width)
        hot_y = min(max(0, int(height - self._mouse_cursor.hot_y)), height)
        cursor = xlib.XCreatePixmapCursor(self._x_display, bitmap, mask, white, black, hot_x, hot_y)
        xlib.XFreePixmap(self._x_display, bitmap)
        xlib.XFreePixmap(self._x_display, mask)

        return cursor

    def set_mouse_platform_visible(self, platform_visible: bool | None = None) -> None:
        if not self._window:
            return
        if platform_visible is None:
            platform_visible = self._mouse_visible and not self._mouse_cursor.gl_drawable

        if platform_visible is False:
            # Hide pointer by creating an empty cursor:
            black = xlib.XColor()
            bitmap = xlib.XCreateBitmapFromData(self._x_display, self._window, bytes(8), 8, 8)
            cursor = xlib.XCreatePixmapCursor(self._x_display, bitmap, bitmap, black, black, 0, 0)
            xlib.XDefineCursor(self._x_display, self._window, cursor)
            xlib.XFreeCursor(self._x_display, cursor)
            xlib.XFreePixmap(self._x_display, bitmap)
        elif isinstance(self._mouse_cursor, ImageMouseCursor) and self._mouse_cursor.hw_drawable:
            # Create a custom hardware cursor:
            cursor = self._create_cursor_from_image(self._mouse_cursor)
            xlib.XDefineCursor(self._x_display, self._window, cursor)
        else:
            # Restore standard hardware cursor:
            if isinstance(self._mouse_cursor, XlibMouseCursor):
                xlib.XDefineCursor(self._x_display, self._window, self._mouse_cursor.cursor)
            else:
                xlib.XUndefineCursor(self._x_display, self._window)

    def set_mouse_position(self, x: int, y: int) -> None:
        xlib.XWarpPointer(self._x_display,
                          0,  # src window
                          self._window,  # dst window
                          0, 0,  # src x, y
                          0, 0,  # src w, h
                          x, self._height - y)

    def _update_exclusivity(self) -> None:
        mouse_exclusive = self._active and self._mouse_exclusive
        keyboard_exclusive = self._active and self._keyboard_exclusive

        if mouse_exclusive != self._applied_mouse_exclusive:
            if mouse_exclusive:
                self.set_mouse_platform_visible(False)

                # Restrict to client area
                xlib.XGrabPointer(self._x_display, self._window,
                                  True,
                                  0,
                                  xlib.GrabModeAsync,
                                  xlib.GrabModeAsync,
                                  self._window,
                                  0,
                                  xlib.CurrentTime)

                # Move pointer to center of window
                x = self._width // 2
                y = self._height // 2
                self._mouse_exclusive_client = x, y
                self.set_mouse_position(x, y)
            elif self._fullscreen and not self.screen._xinerama:  # noqa: SLF001
                # Restrict to fullscreen area (prevent viewport scrolling)
                self.set_mouse_position(0, 0)
                r = xlib.XGrabPointer(self._x_display, self._view,
                                      True, 0,
                                      xlib.GrabModeAsync,
                                      xlib.GrabModeAsync,
                                      self._view,
                                      0,
                                      xlib.CurrentTime)
                if r:
                    # Failed to grab, try again later
                    self._applied_mouse_exclusive = None
                    return
                self.set_mouse_platform_visible()
            else:
                # Unclip
                xlib.XUngrabPointer(self._x_display, xlib.CurrentTime)
                self.set_mouse_platform_visible()

            self._applied_mouse_exclusive = mouse_exclusive

        if keyboard_exclusive != self._applied_keyboard_exclusive:
            if keyboard_exclusive:
                xlib.XGrabKeyboard(self._x_display,
                                   self._window,
                                   False,
                                   xlib.GrabModeAsync,
                                   xlib.GrabModeAsync,
                                   xlib.CurrentTime)
            else:
                xlib.XUngrabKeyboard(self._x_display, xlib.CurrentTime)
            self._applied_keyboard_exclusive = keyboard_exclusive

    def set_exclusive_mouse(self, exclusive: bool = True) -> None:
        if exclusive == self._mouse_exclusive:
            return

        super().set_exclusive_mouse(exclusive)
        self._update_exclusivity()

    def set_exclusive_keyboard(self, exclusive: bool = True) -> None:
        if exclusive == self._keyboard_exclusive:
            return

        super().set_exclusive_keyboard(exclusive)
        self._update_exclusivity()

    def get_system_mouse_cursor(self, name: str) -> DefaultMouseCursor | XlibMouseCursor:
        if name == self.CURSOR_DEFAULT:
            return DefaultMouseCursor()

        # NQR means default shape is not pretty... surely there is another
        # cursor font?
        cursor_shapes = {
            self.CURSOR_CROSSHAIR: cursorfont.XC_crosshair,
            self.CURSOR_HAND: cursorfont.XC_hand2,
            self.CURSOR_HELP: cursorfont.XC_question_arrow,  # NQR
            self.CURSOR_NO: cursorfont.XC_pirate,  # NQR
            self.CURSOR_SIZE: cursorfont.XC_fleur,
            self.CURSOR_SIZE_UP: cursorfont.XC_top_side,
            self.CURSOR_SIZE_UP_RIGHT: cursorfont.XC_top_right_corner,
            self.CURSOR_SIZE_RIGHT: cursorfont.XC_right_side,
            self.CURSOR_SIZE_DOWN_RIGHT: cursorfont.XC_bottom_right_corner,
            self.CURSOR_SIZE_DOWN: cursorfont.XC_bottom_side,
            self.CURSOR_SIZE_DOWN_LEFT: cursorfont.XC_bottom_left_corner,
            self.CURSOR_SIZE_LEFT: cursorfont.XC_left_side,
            self.CURSOR_SIZE_UP_LEFT: cursorfont.XC_top_left_corner,
            self.CURSOR_SIZE_UP_DOWN: cursorfont.XC_sb_v_double_arrow,
            self.CURSOR_SIZE_LEFT_RIGHT: cursorfont.XC_sb_h_double_arrow,
            self.CURSOR_TEXT: cursorfont.XC_xterm,
            self.CURSOR_WAIT: cursorfont.XC_watch,
            self.CURSOR_WAIT_ARROW: cursorfont.XC_watch,  # NQR
        }
        if name not in cursor_shapes:
            msg = f'Unknown cursor name "{name}"'
            raise MouseCursorException(msg)
        cursor = xlib.XCreateFontCursor(self._x_display, cursor_shapes[name])
        return XlibMouseCursor(cursor)

    def set_icon(self, *images: pyglet.image.ImageData) -> None:
        # Careful!  XChangeProperty takes an array of long when data type
        # is 32-bit (but long can be 64 bit!), so pad high bytes of format if
        # necessary.

        import sys
        fmt = {
            ('little', 4): 'BGRA',
            ('little', 8): 'BGRAAAAA',
            ('big', 4): 'ARGB',
            ('big', 8): 'AAAAARGB',
        }[(sys.byteorder, sizeof(c_ulong))]

        data = asbytes('')
        for image in images:
            image = image.get_image_data()
            pitch = -(image.width * len(fmt))
            s = c_buffer(sizeof(c_ulong) * 2)
            memmove(s, cast((c_ulong * 2)(image.width, image.height), POINTER(c_ubyte)), len(s))
            data += s.raw + image.get_data(fmt, pitch)
        buffer = (c_ubyte * len(data))()
        memmove(buffer, data, len(data))
        atom = xlib.XInternAtom(self._x_display, asbytes('_NET_WM_ICON'), False)
        xlib.XChangeProperty(self._x_display, self._window, atom, XA_CARDINAL,
                             32, xlib.PropModeReplace, buffer, len(data) // sizeof(c_ulong))

    def set_clipboard_text(self, text: str) -> None:
        xlib.XSetSelectionOwner(self._x_display,
                                self._clipboard_atom,
                                self._window,
                                xlib.CurrentTime)

        if xlib.XGetSelectionOwner(self._x_display, self._clipboard_atom) == self._window:
            self._clipboard_str = text
            str_bytes = text.encode('utf-8')
            size = len(str_bytes)

            xlib.XChangeProperty(self._x_display, self._window,
                                 self._clipboard_atom, self._utf8_atom, 8, xlib.PropModeReplace,
                                 (c_ubyte * size).from_buffer_copy(str_bytes), size)
        else:
            if _debug:
                print("X11: Couldn't become owner of clipboard.")

    def get_clipboard_text(self) -> str:
        if self._clipboard_str is not None:
            return self._clipboard_str

        owner = xlib.XGetSelectionOwner(self._x_display, self._clipboard_atom)

        if not owner:
            return ''

        text = ''
        if owner == self._window:
            data, size, actual_atom = self.get_single_property(self._window, self._clipboard_atom,
                                                               self._utf8_atom)
        else:
            notification = xlib.XEvent()

            # Convert to selection notification.
            xlib.XConvertSelection(self._x_display,
                                   self._clipboard_atom,
                                   self._utf8_atom,
                                   self._clipboard_atom,
                                   self._window,
                                   xlib.CurrentTime)

            while not xlib.XCheckTypedWindowEvent(self._x_display, self._window, xlib.SelectionNotify,
                                                  byref(notification)):
                self.dispatch_platform_event(notification)

            if not notification.xselection.property:
                return ''

            data, size, actual_atom = self.get_single_property(notification.xselection.requestor,
                                                               notification.xselection.property,
                                                               self._utf8_atom)

        if actual_atom == self._incr_atom:
            # Not implemented.
            if _debug:
                print('X11: Clipboard data is too large, not implemented.')

        elif actual_atom == self._utf8_atom and data:
            text_bytes = string_at(data, size)

            text = text_bytes.decode('utf-8')

        xlib.XFree(data)
        return text

    # Private utility

    def _set_wm_normal_hints(self) -> None:
        hints = xlib.XAllocSizeHints().contents
        if self._minimum_size:
            hints.flags |= xlib.PMinSize
            hints.min_width, hints.min_height = self._minimum_size
        if self._maximum_size:
            hints.flags |= xlib.PMaxSize
            hints.max_width, hints.max_height = self._maximum_size
        xlib.XSetWMNormalHints(self._x_display, self._window, byref(hints))

    def _set_text_property(self, name: str, value: str, allow_utf8: bool = True) -> None:
        atom = xlib.XInternAtom(self._x_display, asbytes(name), False)
        if not atom:
            msg = f'Undefined atom "{name}"'
            raise XlibException(msg)
        text_property = xlib.XTextProperty()
        if _have_utf8 and allow_utf8:
            buf = create_string_buffer(value.encode('utf8'))
            result = xlib.Xutf8TextListToTextProperty(self._x_display,
                                                      cast(pointer(buf), c_char_p),
                                                      1, xlib.XUTF8StringStyle,
                                                      byref(text_property))
            if result < 0:
                msg = 'Could not create UTF8 text property'
                raise XlibException(msg)
        else:
            buf = create_string_buffer(value.encode('ascii', 'ignore'))
            result = xlib.XStringListToTextProperty(
                cast(pointer(buf), c_char_p), 1, byref(text_property))
            if result < 0:
                msg = 'Could not create text property'
                raise XlibException(msg)
        xlib.XSetTextProperty(self._x_display, self._window, byref(text_property), atom)
        # XXX <rj> Xlib doesn't like us freeing this
        # xlib.XFree(text_property.value)

    def _set_atoms_property(self, name: str, values: list[str], mode: int = xlib.PropModeReplace) -> None:
        name_atom = xlib.XInternAtom(self._x_display, asbytes(name), False)
        atoms = [xlib.XInternAtom(self._x_display, asbytes(value), False) for value in values]
        atom_type = xlib.XInternAtom(self._x_display, asbytes('ATOM'), False)
        if len(atoms):
            atoms_ar = (xlib.Atom * len(atoms))(*atoms)
            xlib.XChangeProperty(self._x_display, self._window,
                                 name_atom, atom_type, 32, mode,
                                 cast(pointer(atoms_ar), POINTER(c_ubyte)), len(atoms))
        else:
            net_wm_state = xlib.XInternAtom(self._x_display, asbytes('_NET_WM_STATE'), False)
            if net_wm_state:
                xlib.XDeleteProperty(self._x_display, self._window, net_wm_state)

    def _set_wm_state(self, *states: str) -> None:
        # Set property
        net_wm_state = xlib.XInternAtom(self._x_display, asbytes('_NET_WM_STATE'), False)
        atoms = [xlib.XInternAtom(self._x_display, asbytes(state), False) for state in states]
        atom_type = xlib.XInternAtom(self._x_display, asbytes('ATOM'), False)
        if len(atoms):
            atoms_ar = (xlib.Atom * len(atoms))(*atoms)
            xlib.XChangeProperty(self._x_display, self._window,
                                 net_wm_state, atom_type, 32, xlib.PropModePrepend,
                                 cast(pointer(atoms_ar), POINTER(c_ubyte)), len(atoms))
        else:
            xlib.XDeleteProperty(self._x_display, self._window, net_wm_state)

        # Nudge the WM
        e = xlib.XEvent()
        e.xclient.type = xlib.ClientMessage
        e.xclient.message_type = net_wm_state
        e.xclient.display = cast(self._x_display, POINTER(xlib.Display))
        e.xclient.window = self._window
        e.xclient.format = 32
        e.xclient.data.l[0] = xlib.PropModePrepend
        for i, atom in enumerate(atoms):
            e.xclient.data.l[i + 1] = atom
        xlib.XSendEvent(self._x_display, self._get_root(),
                        False, xlib.SubstructureRedirectMask, byref(e))

    # Event handling

    def dispatch_events(self) -> None:
        self.dispatch_pending_events()

        self._allow_dispatch_event = True

        e = xlib.XEvent()

        # Cache these in case window is closed from an event handler
        _x_display = self._x_display
        _window = self._window
        _view = self._view

        # Check for the events specific to this window
        while xlib.XCheckWindowEvent(_x_display, _window, 0x1ffffff, byref(e)):
            # Key events are filtered by the xlib window event
            # handler so they get a shot at the prefiltered event.
            if e.xany.type not in (xlib.KeyPress, xlib.KeyRelease):
                if xlib.XFilterEvent(e, 0):
                    continue
            self.dispatch_platform_event(e)

        # Check for the events specific to this view
        while xlib.XCheckWindowEvent(_x_display, _view, 0x1ffffff, byref(e)):
            # Key events are filtered by the xlib window event
            # handler so they get a shot at the prefiltered event.
            if e.xany.type not in (xlib.KeyPress, xlib.KeyRelease):
                if xlib.XFilterEvent(e, 0):
                    continue
            self.dispatch_platform_event_view(e)

        # Generic events for this window (the window close event).
        while xlib.XCheckTypedWindowEvent(_x_display, _window, xlib.ClientMessage, byref(e)):
            self.dispatch_platform_event(e)

        self._allow_dispatch_event = False

    def dispatch_pending_events(self) -> None:
        while self._event_queue:
            EventDispatcher.dispatch_event(self, *self._event_queue.pop(0))

        # Dispatch any context-related events
        if self._lost_context:
            self._lost_context = False
            EventDispatcher.dispatch_event(self, 'on_context_lost')
        if self._lost_context_state:
            self._lost_context_state = False
            EventDispatcher.dispatch_event(self, 'on_context_state_lost')

    def dispatch_platform_event(self, e: xlib.XEvent) -> None:
        if self._applied_mouse_exclusive is None:
            self._update_exclusivity()
        event_handler = self._event_handlers.get(e.type)
        if event_handler:
            event_handler(e)

    def dispatch_platform_event_view(self, e: xlib.XEvent) -> None:
        event_handler = self._view_event_handlers.get(e.type)
        if event_handler:
            event_handler(e)

    @staticmethod
    @lru_cache()
    def _translate_modifiers(state: int) -> int:
        modifiers = 0
        if state & xlib.ShiftMask:
            modifiers |= key.MOD_SHIFT
        if state & xlib.ControlMask:
            modifiers |= key.MOD_CTRL
        if state & xlib.LockMask:
            modifiers |= key.MOD_CAPSLOCK
        if state & xlib.Mod1Mask:
            modifiers |= key.MOD_ALT
        if state & xlib.Mod2Mask:
            modifiers |= key.MOD_NUMLOCK
        if state & xlib.Mod4Mask:
            modifiers |= key.MOD_WINDOWS
        if state & xlib.Mod5Mask:
            modifiers |= key.MOD_SCROLLLOCK
        return modifiers

    # Event handlers
    """
    def _event_symbol(self, event):
        # pyglet.self.key keysymbols are identical to X11 keysymbols, no
        # need to map the keysymbol.
        symbol = xlib.XKeycodeToKeysym(self._x_display, event.xkey.keycode, 0)
        if symbol == 0:
            # XIM event
            return None
        elif symbol not in key._key_names.keys():
            symbol = key.user_key(event.xkey.keycode)
        return symbol
    """

    def _event_text_symbol(self, ev: xlib.XEvent) -> tuple[str | None, int]:
        text = None
        symbol = xlib.KeySym()
        buffer = create_string_buffer(128)

        # Look up raw keysym before XIM filters it (default for keypress and
        # keyrelease)
        count = xlib.XLookupString(ev.xkey, buffer, len(buffer) - 1, byref(symbol), None)

        # Give XIM a shot
        filtered = xlib.XFilterEvent(ev, ev.xany.window)

        if ev.type == xlib.KeyPress and not filtered:
            status = c_int()
            if _have_utf8:
                encoding = 'utf8'
                count = xlib.Xutf8LookupString(self._x_ic,
                                               ev.xkey,
                                               buffer, len(buffer) - 1,
                                               byref(symbol), byref(status))
                if status.value == xlib.XBufferOverflow:
                    raise NotImplementedError('TODO: XIM buffer resize')

            else:
                encoding = 'ascii'
                count = xlib.XLookupString(ev.xkey, buffer, len(buffer) - 1, byref(symbol), None)
                if count:
                    status.value = xlib.XLookupBoth

            if status.value & (xlib.XLookupChars | xlib.XLookupBoth):
                text = buffer.value[:count].decode(encoding)

            # Don't treat Unicode command codepoints as text, except Return.
            if text and unicodedata.category(text) == 'Cc' and text != '\r':
                text = None

        symbol = symbol.value

        # If the event is a XIM filtered event, the keysym will be virtual
        # (e.g., aacute instead of A after a dead key).  Drop it, we don't
        # want these kind of key events.
        if ev.xkey.keycode == 0 and not filtered:
            symbol = None

        # pyglet.self.key keysymbols are identical to X11 keysymbols, no
        # need to map the keysymbol.  For keysyms outside the pyglet set, map
        # raw key code to a user key.
        if symbol and symbol not in key._key_names and ev.xkey.keycode:  # noqa: SLF001
            # Issue 353: Symbol is uppercase when shift key held down.
            try:
                symbol = ord(chr(symbol).lower())
            except ValueError:
                # Not a valid unichr, use the keycode
                symbol = key.user_key(ev.xkey.keycode)
            else:
                # If still not recognised, use the keycode
                if symbol not in key._key_names:  # noqa: SLF001
                    symbol = key.user_key(ev.xkey.keycode)

        if filtered:
            # The event was filtered, text must be ignored, but the symbol is
            # still good.
            return None, symbol

        return text, symbol

    @staticmethod
    def _event_text_motion(symbol: int, modifiers: int) -> int | None:
        if modifiers & key.MOD_ALT:
            return None
        ctrl = modifiers & key.MOD_CTRL != 0
        return _motion_map.get((symbol, ctrl), None)

    @ViewEventHandler
    @XlibEventHandler(xlib.KeyPress)
    @XlibEventHandler(xlib.KeyRelease)
    def _event_key_view(self, ev: xlib.XEvent) -> None:
        # Try to detect autorepeat ourselves if the server doesn't support it
        # XXX: Doesn't always work, better off letting the server do it
        global _can_detect_autorepeat  # noqa: PLW0602
        if not _can_detect_autorepeat and ev.type == xlib.KeyRelease:
            # Look in the queue for a matching KeyPress with same timestamp,
            # indicating an auto-repeat rather than actual key event.
            saved = []
            while True:
                auto_event = xlib.XEvent()
                result = xlib.XCheckWindowEvent(self._x_display,
                                                self._window, xlib.KeyPress | xlib.KeyRelease,
                                                byref(auto_event))
                if not result:
                    break
                saved.append(auto_event)
                if auto_event.type == xlib.KeyRelease:
                    # just save this off for restoration back to the queue
                    continue
                if ev.xkey.keycode == auto_event.xkey.keycode:
                    # Found a key repeat: dispatch EVENT_TEXT* event
                    text, symbol = self._event_text_symbol(auto_event)
                    modifiers = self._translate_modifiers(ev.xkey.state)
                    modifiers_ctrl = modifiers & (key.MOD_CTRL | key.MOD_ALT)
                    motion = self._event_text_motion(symbol, modifiers)
                    if motion:
                        if modifiers & key.MOD_SHIFT:
                            self.dispatch_event('on_text_motion_select', motion)
                        else:
                            self.dispatch_event('on_text_motion', motion)
                    elif text and not modifiers_ctrl:
                        self.dispatch_event('on_text', text)

                    ditched = saved.pop()
                    for auto_event in reversed(saved):
                        xlib.XPutBackEvent(self._x_display, byref(auto_event))
                    return
                else:
                    # Key code of press did not match, therefore no repeating
                    # is going on, stop searching.
                    break
            # Whoops, put the events back, it's for real.
            for auto_event in reversed(saved):
                xlib.XPutBackEvent(self._x_display, byref(auto_event))

        text, symbol = self._event_text_symbol(ev)
        modifiers = self._translate_modifiers(ev.xkey.state)
        modifiers_ctrl = modifiers & (key.MOD_CTRL | key.MOD_ALT)
        motion = self._event_text_motion(symbol, modifiers)

        if ev.type == xlib.KeyPress:
            if symbol and (not _can_detect_autorepeat or symbol not in self.pressed_keys):
                self.dispatch_event('on_key_press', symbol, modifiers)
                if _can_detect_autorepeat:
                    self.pressed_keys.add(symbol)
            if motion:
                if modifiers & key.MOD_SHIFT:
                    self.dispatch_event('on_text_motion_select', motion)
                else:
                    self.dispatch_event('on_text_motion', motion)
            elif text and not modifiers_ctrl:
                self.dispatch_event('on_text', text)
        elif ev.type == xlib.KeyRelease:
            if symbol:
                self.dispatch_event('on_key_release', symbol, modifiers)
                if _can_detect_autorepeat and symbol in self.pressed_keys:
                    self.pressed_keys.remove(symbol)

    @XlibEventHandler(xlib.KeyPress)
    @XlibEventHandler(xlib.KeyRelease)
    def _event_key(self, ev: xlib.XEvent) -> None:
        return self._event_key_view(ev)

    @ViewEventHandler
    @XlibEventHandler(xlib.MotionNotify)
    def _event_motionnotify_view(self, ev: xlib.XEvent) -> None:
        x = ev.xmotion.x / self._scale
        y = self.height - 1 - ev.xmotion.y / self._scale

        if self._mouse_in_window:
            dx = x - self._mouse_x
            dy = y - self._mouse_y
        else:
            dx = dy = 0

        if self._applied_mouse_exclusive and (ev.xmotion.x, ev.xmotion.y) == self._mouse_exclusive_client:
            # Ignore events caused by XWarpPointer
            self._mouse_x = x
            self._mouse_y = y
            return

        if self._applied_mouse_exclusive:
            # Reset pointer position
            ex, ey = self._mouse_exclusive_client
            xlib.XWarpPointer(self._x_display,
                              0,
                              self._window,
                              0, 0,
                              0, 0,
                              ex, ey)

        self._mouse_x = x
        self._mouse_y = y
        self._mouse_in_window = True

        buttons = 0
        if ev.xmotion.state & xlib.Button1MotionMask:
            buttons |= mouse.LEFT
        if ev.xmotion.state & xlib.Button2MotionMask:
            buttons |= mouse.MIDDLE
        if ev.xmotion.state & xlib.Button3MotionMask:
            buttons |= mouse.RIGHT
        # TODO: Determine how to implement drag support for mouse 4 and 5

        if buttons:
            # Drag event
            modifiers = self._translate_modifiers(ev.xmotion.state)
            self.dispatch_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)
        else:
            # Motion event
            self.dispatch_event('on_mouse_motion', x, y, dx, dy)

    @XlibEventHandler(xlib.MotionNotify)
    def _event_motionnotify(self, ev: xlib.XEvent) -> None:
        # Window motion looks for drags that are outside the view but within
        # the window.
        buttons = 0
        if ev.xmotion.state & xlib.Button1MotionMask:
            buttons |= mouse.LEFT
        if ev.xmotion.state & xlib.Button2MotionMask:
            buttons |= mouse.MIDDLE
        if ev.xmotion.state & xlib.Button3MotionMask:
            buttons |= mouse.RIGHT
        # TODO: Determine how to implement drag support for mouse 4 and 5

        if buttons:
            # Drag event
            x = (ev.xmotion.x - self._view_x) / self._scale
            y = self._height - 1 - self._view_y - ev.xmotion.y / self._scale

            if self._mouse_in_window:
                dx = x - self._mouse_x
                dy = y - self._mouse_y
            else:
                dx = dy = 0
            self._mouse_x = x
            self._mouse_y = y

            modifiers = self._translate_modifiers(ev.xmotion.state)
            self.dispatch_event('on_mouse_drag', x, y, dx, dy, buttons, modifiers)

    @XlibEventHandler(xlib.ClientMessage)
    def _event_clientmessage(self, ev: xlib.XEvent) -> None:
        atom = ev.xclient.data.l[0]
        if atom == xlib.XInternAtom(ev.xclient.display, asbytes('WM_DELETE_WINDOW'), False):
            self.dispatch_event('on_close')
        elif (self._enable_xsync and
              atom == xlib.XInternAtom(ev.xclient.display,
                                       asbytes('_NET_WM_SYNC_REQUEST'), False)):
            lo = ev.xclient.data.l[2]
            hi = ev.xclient.data.l[3]
            self._current_sync_value = xsync.XSyncValue(hi, lo)

        elif ev.xclient.message_type == self._xdnd_atoms['XdndPosition']:
            self._event_drag_position(ev)

        elif ev.xclient.message_type == self._xdnd_atoms['XdndDrop']:
            self._event_drag_drop(ev)

        elif ev.xclient.message_type == self._xdnd_atoms['XdndEnter']:
            self._event_drag_enter(ev)

    def _event_drag_drop(self, ev: xlib.XEvent) -> None:
        if self._xdnd_version > XDND_VERSION:
            return

        time = xlib.CurrentTime

        if self._xdnd_format:
            if self._xdnd_version >= 1:
                time = ev.xclient.data.l[2]

            # Convert to selection notification.
            xlib.XConvertSelection(self._x_display,
                                   self._xdnd_atoms['XdndSelection'],
                                   self._xdnd_format,
                                   self._xdnd_atoms['XdndSelection'],
                                   self._window,
                                   time)

            xlib.XFlush(self._x_display)

        elif self._xdnd_version >= 2:
            # If no format send finished with no data.
            e = xlib.XEvent()
            e.xclient.type = xlib.ClientMessage
            e.xclient.message_type = self._xdnd_atoms['XdndFinished']
            e.xclient.display = cast(self._x_display, POINTER(xlib.Display))
            e.xclient.window = self._window
            e.xclient.format = 32
            e.xclient.data.l[0] = self._window
            e.xclient.data.l[1] = 0
            e.xclient.data.l[2] = None

            xlib.XSendEvent(self._x_display, self._xdnd_source,
                            False, xlib.NoEventMask, byref(e))

            xlib.XFlush(self._x_display)

    def _event_drag_position(self, ev: xlib.XEvent) -> None:
        if self._xdnd_version > XDND_VERSION:
            return

        xoff = (ev.xclient.data.l[2] >> 16) & 0xffff
        yoff = (ev.xclient.data.l[2]) & 0xffff

        # Need to convert the position to actual window coordinates with the screen offset
        child = xlib.Window()
        x = c_int()
        y = c_int()
        xlib.XTranslateCoordinates(self._x_display,
                                   self._get_root(),
                                   self._window,
                                   xoff, yoff,
                                   byref(x),
                                   byref(y),
                                   byref(child))

        self._xdnd_position = (x.value, y.value)

        e = xlib.XEvent()
        e.xclient.type = xlib.ClientMessage
        e.xclient.message_type = self._xdnd_atoms['XdndStatus']
        e.xclient.display = cast(self._x_display, POINTER(xlib.Display))
        e.xclient.window = ev.xclient.data.l[0]
        e.xclient.format = 32
        e.xclient.data.l[0] = self._window
        e.xclient.data.l[2] = 0
        e.xclient.data.l[3] = 0

        if self._xdnd_format:
            e.xclient.data.l[1] = 1
            if self._xdnd_version >= 2:
                e.xclient.data.l[4] = self._xdnd_atoms['XdndActionCopy']

        xlib.XSendEvent(self._x_display, self._xdnd_source,
                        False, xlib.NoEventMask, byref(e))

        xlib.XFlush(self._x_display)

    def _event_drag_enter(self, ev: xlib.XEvent) -> None:
        self._xdnd_source = ev.xclient.data.l[0]
        self._xdnd_version = ev.xclient.data.l[1] >> 24
        self._xdnd_format = None

        if self._xdnd_version > XDND_VERSION:
            return

        three_or_more = ev.xclient.data.l[1] & 1

        # Search all of them (usually 8)
        if three_or_more:
            data, count, _ = self.get_single_property(self._xdnd_source, self._xdnd_atoms['XdndTypeList'], XA_ATOM)

            data = cast(data, POINTER(xlib.Atom))
        else:
            # Some old versions may only have 3? Needs testing.
            count = 3
            data = ev.xclient.data.l + 2

        # Check all of the properties we received from the dropped item and verify it support URI.
        for i in range(count):
            if data[i] == self._xdnd_atoms['text/uri-list']:
                self._xdnd_format = self._xdnd_atoms['text/uri-list']
                break

        if data:
            xlib.XFree(data)

    def get_single_property(self, window: xlib.Window, atom_property: xlib.Atom, atom_type: int) -> tuple[
        _Pointer[c_ubyte], int, int]:
        """ Returns the length, data, and actual atom of a window property. """
        actualAtom = xlib.Atom()
        actualFormat = c_int()
        itemCount = c_ulong()
        bytesAfter = c_ulong()
        data = POINTER(c_ubyte)()

        xlib.XGetWindowProperty(self._x_display, window,
                                atom_property, 0, 2147483647, False, atom_type,
                                byref(actualAtom),
                                byref(actualFormat),
                                byref(itemCount),
                                byref(bytesAfter),
                                data)

        return data, itemCount.value, actualAtom.value

    @XlibEventHandler(xlib.SelectionNotify)
    def _event_selection_notification(self, ev: xlib.XEvent) -> None:
        if ev.xselection.property != 0 and ev.xselection.selection == self._xdnd_atoms['XdndSelection']:
            if self._xdnd_format:
                # This will get the data
                data, count, _ = self.get_single_property(ev.xselection.requestor,
                                                          ev.xselection.property,
                                                          ev.xselection.target)

                buffer = create_string_buffer(count)
                memmove(buffer, data, count)

                formatted_paths = self.parse_filenames(buffer.value.decode())

                e = xlib.XEvent()
                e.xclient.type = xlib.ClientMessage
                e.xclient.message_type = self._xdnd_atoms['XdndFinished']
                e.xclient.display = cast(self._x_display, POINTER(xlib.Display))
                e.xclient.window = self._window
                e.xclient.format = 32
                e.xclient.data.l[0] = self._xdnd_source
                e.xclient.data.l[1] = 1
                e.xclient.data.l[2] = self._xdnd_atoms['XdndActionCopy']

                xlib.XSendEvent(self._x_display, self._get_root(),
                                False, xlib.NoEventMask, byref(e))

                xlib.XFlush(self._x_display)

                xlib.XFree(data)

                self.dispatch_event('on_file_drop', self._xdnd_position[0], self._height - self._xdnd_position[1],
                                    formatted_paths)

    @staticmethod
    def parse_filenames(decoded_string: str) -> list[str]:
        """All of the filenames from file drops come as one big string with
            some special characters (%20), this will parse them out.
        """
        different_files = decoded_string.splitlines()

        parsed = []
        encoding = sys.getfilesystemencoding()
        for filename in different_files:
            if filename:
                parsed_filename = urllib.parse.urlsplit(filename).path
                parsed.append(urllib.parse.unquote(parsed_filename, encoding))

        return parsed

    def _sync_resize(self) -> None:
        if self._enable_xsync and self._current_sync_valid:
            if xsync.XSyncValueIsZero(self._current_sync_value):
                self._current_sync_valid = False
                return
            xsync.XSyncSetCounter(self._x_display,
                                  self._sync_counter,
                                  self._current_sync_value)
            self._current_sync_value = None
            self._current_sync_valid = False

    @staticmethod
    @lru_cache()
    def _translate_button(value: int) -> int:
        """Translate mouse button values to match mouse constants.

        Given a Xevent.xbutton.button value, convert it to the mouse
        contents defined in :py:module:`~pyglet.window.mouse`. This
        means shifting the value, and also skipping over values of
        4~7, which are used for boolean scrolling.
        """
        new_value = value - 1
        if value > 7:
            new_value -= 4
        return 1 << new_value

    @ViewEventHandler
    @XlibEventHandler(xlib.ButtonPress)
    @XlibEventHandler(xlib.ButtonRelease)
    def _event_button(self, ev: xlib.XEvent) -> None:
        x = ev.xbutton.x / self._scale
        y = self.height - 1 - ev.xbutton.y / self._scale

        modifiers = self._translate_modifiers(ev.xbutton.state)

        if ev.type == xlib.ButtonPress:
            # override_redirect issue: manually activate this window if fullscreen.
            if self._override_redirect and not self._active:
                self.activate()

            if ev.xbutton.button == 4:
                self.dispatch_event('on_mouse_scroll', x, y, 0, 1)
            elif ev.xbutton.button == 5:
                self.dispatch_event('on_mouse_scroll', x, y, 0, -1)
            elif ev.xbutton.button == 6:
                self.dispatch_event('on_mouse_scroll', x, y, -1, 0)
            elif ev.xbutton.button == 7:
                self.dispatch_event('on_mouse_scroll', x, y, 1, 0)
            else:
                button = self._translate_button(ev.xbutton.button)
                self.dispatch_event('on_mouse_press', x, y, button, modifiers)

        elif ev.xbutton.button not in (4, 5, 6, 7):
            button = self._translate_button(ev.xbutton.button)
            self.dispatch_event('on_mouse_release', x, y, button, modifiers)

    @ViewEventHandler
    @XlibEventHandler(xlib.Expose)
    def _event_expose(self, ev: xlib.XEvent) -> None:
        # Ignore all expose events except the last one. We could be told
        # about exposure rects - but I don't see the point since we're
        # working with OpenGL and we'll just redraw the whole scene.
        if ev.xexpose.count > 0:
            return
        self.dispatch_event('on_expose')

    @ViewEventHandler
    @XlibEventHandler(xlib.EnterNotify)
    def _event_enternotify(self, ev: xlib.XEvent) -> None:
        # mouse position
        x = self._mouse_x = ev.xcrossing.x / self._scale
        y = self._mouse_y = self.height - 1 - ev.xcrossing.y / self._scale
        self._mouse_in_window = True

        # XXX there may be more we could do here
        self.dispatch_event('on_mouse_enter', x, y)

    @ViewEventHandler
    @XlibEventHandler(xlib.LeaveNotify)
    def _event_leavenotify(self, ev: xlib.XEvent) -> None:
        x = self._mouse_x = ev.xcrossing.x / self._scale
        y = self._mouse_y = self.height - 1 - ev.xcrossing.y / self._scale
        self._mouse_in_window = False
        self.dispatch_event('on_mouse_leave', x, y)

    @XlibEventHandler(xlib.ConfigureNotify)
    def _event_configurenotify(self, ev: xlib.XEvent) -> None:
        if self._enable_xsync and self._current_sync_value:
            self._current_sync_valid = True

        if self._fullscreen:
            return

        self.switch_to()

        w, h = ev.xconfigure.width, ev.xconfigure.height
        x, y = ev.xconfigure.x, ev.xconfigure.y
        if self._width != w or self._height != h:
            self._width = max(1, w)
            self._height = max(1, h)
            self._update_view_size()
            self.dispatch_event('_on_internal_resize', self._width, self._height)
        if self._x != x or self._y != y:
            self.dispatch_event('on_move', x, y)
            self._x = x
            self._y = y

    @XlibEventHandler(xlib.FocusIn)
    def _event_focusin(self, ev: xlib.XEvent) -> None:
        self._active = True
        self._update_exclusivity()
        self.dispatch_event('on_activate')
        if _have_utf8:
            xlib.XSetICFocus(self._x_ic)

    @XlibEventHandler(xlib.FocusOut)
    def _event_focusout(self, ev: xlib.XEvent) -> None:
        self._active = False
        self._update_exclusivity()
        self.dispatch_event('on_deactivate')
        if _have_utf8:
            xlib.XUnsetICFocus(self._x_ic)

    @XlibEventHandler(xlib.MapNotify)
    def _event_mapnotify(self, ev: xlib.XEvent) -> None:
        self._mapped = True
        self.dispatch_event('on_show')
        self._update_exclusivity()

    @XlibEventHandler(xlib.UnmapNotify)
    def _event_unmapnotify(self, ev: xlib.XEvent) -> None:
        self._mapped = False
        self.dispatch_event('on_hide')

    @XlibEventHandler(xlib.SelectionClear)
    def _event_selection_clear(self, ev: xlib.XEvent) -> None:
        if ev.xselectionclear.selection == self._clipboard_atom:
            # Another application cleared the clipboard.
            self._clipboard_str = None

    @XlibEventHandler(xlib.SelectionRequest)
    def _event_selection_request(self, ev: xlib.XEvent) -> None:
        request = ev.xselectionrequest

        if _debug:
            rt = xlib.XGetAtomName(self._x_display, request.target)
            rp = xlib.XGetAtomName(self._x_display, request.property)
            print(f'X11 debug: request target {rt}')
            print(f'X11 debug: request property {rp}')

        out_event = xlib.XEvent()
        out_event.xany.type = xlib.SelectionNotify
        out_event.xselection.selection = request.selection
        out_event.xselection.display = request.display
        out_event.xselection.target = 0
        out_event.xselection.property = 0
        out_event.xselection.requestor = request.requestor
        out_event.xselection.time = request.time

        if (xlib.XGetSelectionOwner(self._x_display, self._clipboard_atom) == self._window and
                ev.xselection.target == self._clipboard_atom):
            if request.target == self._target_atom:
                atoms_ar = (xlib.Atom * 1)(self._utf8_atom)
                ptr = cast(pointer(atoms_ar), POINTER(c_ubyte))

                xlib.XChangeProperty(self._x_display, request.requestor,
                                     request.property, XA_ATOM, 32,
                                     xlib.PropModeReplace,
                                     ptr, sizeof(atoms_ar) // sizeof(c_ulong))
                out_event.xselection.property = request.property
                out_event.xselection.target = request.target

            elif request.target == self._utf8_atom:
                # We are being requested for a UTF-8 string.
                text = self._clipboard_str.encode('utf-8')
                size = len(self._clipboard_str)
                xlib.XChangeProperty(self._x_display, request.requestor,
                                     request.property, request.target, 8,
                                     xlib.PropModeReplace,
                                     (c_ubyte * size).from_buffer_copy(text), size)

                out_event.xselection.property = request.property
                out_event.xselection.target = request.target

        # Send request event back to requestor with updated changes.
        xlib.XSendEvent(self._x_display, request.requestor, 0, 0, byref(out_event))

        # Seems to work find without it. May add later.
        # xlib.XSync(self._x_display, False)


__all__ = ['XlibEventHandler', 'XlibWindow']
