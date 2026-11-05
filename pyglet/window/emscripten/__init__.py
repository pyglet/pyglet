from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any, TYPE_CHECKING, Callable, TypeVar, cast

import js  # noqa: F821

import pyglet.app
from pyglet.libs.emscripten.files import import_files
from pyglet.libs.emscripten.proxies import ProxyRegistry
from pyglet.window import BaseWindow, DefaultMouseCursor, ImageMouseCursor, MouseCursor, key, mouse

if TYPE_CHECKING:
    from pyglet.display.emscripten import EmscriptenScreen
    from collections.abc import Iterable

    from pyodide.ffi import JsProxy

    from pyglet.config import Config
    from pyglet.libs.emscripten.dom import (
        ClipboardEvent, DragEvent, Event, File, HTMLCanvasElement, KeyboardEvent,
        MouseEvent, PointerEvent, ResizeObserver, ResizeObserverEntry, WheelEvent,
    )
    from pyglet.display.base import Display, ScreenMode
    from pyglet.graphics.api.base import SurfaceContext
    from pyglet.graphics.api.webgl.context import WebGL2SurfaceContext

# Keymap using `event.code`
_key_map = {
    # Alpha
    "a": key.A,
    "b": key.B,
    "c": key.C,
    "d": key.D,
    "e": key.E,
    "f": key.F,
    "g": key.G,
    "h": key.H,
    "i": key.I,
    "j": key.J,
    "k": key.K,
    "l": key.L,
    "m": key.M,
    "n": key.N,
    "o": key.O,
    "p": key.P,
    "q": key.Q,
    "r": key.R,
    "s": key.S,
    "t": key.T,
    "u": key.U,
    "v": key.V,
    "w": key.W,
    "x": key.X,
    "y": key.Y,
    "z": key.Z,
    "A": key.A,
    "B": key.B,
    "C": key.C,
    "D": key.D,
    "E": key.E,
    "F": key.F,
    "G": key.G,
    "H": key.H,
    "I": key.I,
    "J": key.J,
    "K": key.K,
    "L": key.L,
    "M": key.M,
    "N": key.N,
    "O": key.O,
    "P": key.P,
    "Q": key.Q,
    "R": key.R,
    "S": key.S,
    "T": key.T,
    "U": key.U,
    "V": key.V,
    "W": key.W,
    "X": key.X,
    "Y": key.Y,
    "Z": key.Z,
    # Numeric
    "0": key._0,
    "1": key._1,
    "2": key._2,
    "3": key._3,
    "4": key._4,
    "5": key._5,
    "6": key._6,
    "7": key._7,
    "8": key._8,
    "9": key._9,
    # Whitespace and control keys
    "Backspace": key.BACKSPACE,
    "Tab": key.TAB,
    "Enter": key.RETURN,
    "Escape": key.ESCAPE,
    " ": key.SPACE,
    # Navication keys
    "Insert": key.INSERT,
    "Home": key.HOME,
    "End": key.END,
    "PageUp": key.PAGEUP,
    "PageDown": key.PAGEDOWN,
    "ArrowLeft": key.LEFT,
    "ArrowUp": key.UP,
    "ArrowRight": key.RIGHT,
    "ArrowDown": key.DOWN,
    # Modifier keys
    "Shift": key.LSHIFT,
    "ShiftLeft": key.LSHIFT,
    "ShiftRight": key.RSHIFT,
    "Control": key.LCTRL,
    "ControlLeft": key.LCTRL,
    "ControlRight": key.RCTRL,
    "Alt": key.LALT,
    "AltLeft": key.LALT,
    "AltRight": key.RALT,
    "Meta": key.LMETA,
    "MetaLeft": key.LMETA,
    "MetaRight": key.RMETA,
    "Pause": key.PAUSE,
    "PrintScreen": key.PRINT,
    "ContextMenu": key.MENU,
    # Locks
    "CapsLock": key.CAPSLOCK,
    "NumLock": key.NUMLOCK,
    "ScrollLock": key.SCROLLLOCK,
    # Function keys
    "F1": key.F1,
    "F2": key.F2,
    "F3": key.F3,
    "F4": key.F4,
    "F5": key.F5,
    "F6": key.F6,
    "F7": key.F7,
    "F8": key.F8,
    "F9": key.F9,
    "F10": key.F10,
    "F11": key.F11,
    "F12": key.F12,
    "Numpad0": key.NUM_0,
    "Numpad1": key.NUM_1,
    "Numpad2": key.NUM_2,
    "Numpad3": key.NUM_3,
    "Numpad4": key.NUM_4,
    "Numpad5": key.NUM_5,
    "Numpad6": key.NUM_6,
    "Numpad7": key.NUM_7,
    "Numpad8": key.NUM_8,
    "Numpad9": key.NUM_9,
    "NumpadMultiply": key.NUM_MULTIPLY,
    "NumpadAdd": key.NUM_ADD,
    "NumpadSubtract": key.NUM_SUBTRACT,
    "NumpadDecimal": key.NUM_DECIMAL,
    "NumpadDivide": key.NUM_DIVIDE,
    "NumpadEnter": key.NUM_ENTER,
    "!": key.EXCLAMATION,
    "@": key.AT,
    "#": key.HASH,
    "$": key.DOLLAR,
    "%": key.PERCENT,
    "^": key.ASCIICIRCUM,
    "&": key.AMPERSAND,
    "*": key.ASTERISK,
    "(": key.PARENLEFT,
    ")": key.PARENRIGHT,
    "-": key.MINUS,
    "_": key.UNDERSCORE,
    "=": key.EQUAL,
    "+": key.PLUS,
    "[": key.BRACKETLEFT,
    "]": key.BRACKETRIGHT,
    "{": key.BRACELEFT,
    "}": key.BRACERIGHT,
    ";": key.SEMICOLON,
    ":": key.COLON,
    "'": key.APOSTROPHE,
    "\"": key.DOUBLEQUOTE,
    "\\": key.BACKSLASH,
    "|": key.BAR,
    ",": key.COMMA,
    ".": key.PERIOD,
    "/": key.SLASH,
    "?": key.QUESTION,
    "`": key.GRAVE,
    "~": key.ASCIITILDE,
}

# symbol,ctrl -> motion mapping
_motion_map: dict[tuple[int | str, bool], int] = {
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
    (key.A, True): key.MOTION_SELECT_ALL,
    (key.C, True): key.MOTION_COPY,
    (key.V, True): key.MOTION_PASTE,
}


def get_modifiers(event: KeyboardEvent | MouseEvent) -> int:
    """Extract modifier flags from a JavaScript event."""
    modifiers = 0

    if event.ctrlKey:
        modifiers |= key.MOD_CTRL
    if event.shiftKey:
        modifiers |= key.MOD_SHIFT
    if event.altKey:
        modifiers |= key.MOD_ALT
        modifiers |= key.MOD_OPTION  # Alt is also "Option" on macOS
    if hasattr(event, "metaKey") and event.metaKey:  # Meta = Command on macOS
        modifiers |= key.MOD_COMMAND

    return modifiers


# Convert JavaScript key events to your format
def js_key_to_pyglet(event: KeyboardEvent) -> tuple[int | str, int]:
    """Convert JS event code to the equivalent key mapping."""
    modifiers = 0
    symbol: int | str

    # event.key of a numpad key is its character or its NumLock-off action ("1" or "End"), as for the main
    # keys: use event.code to report NUM_* keys, as on the other platforms.
    if event.code and event.code.startswith("Numpad") and event.code in _key_map:
        symbol = _key_map[event.code]
    elif event.key in _key_map:
        symbol = _key_map[event.key]
    # Doesn't exist in either mapping. Unknown.
    else:
        symbol = event.code if event.code else 0
        print(f"Warning: Unmapped key -> {symbol} ({event.key})")

    # Handle modifiers
    if event.ctrlKey:
        modifiers |= key.MOD_CTRL
    if event.shiftKey:
        modifiers |= key.MOD_SHIFT
    if event.altKey:
        modifiers |= key.MOD_ALT
        modifiers |= key.MOD_OPTION  # Alt is also "Option" on macOS
    if hasattr(event, "metaKey") and event.metaKey:  # Meta = Command on macOS
        modifiers |= key.MOD_COMMAND

    return symbol, modifiers


# Javascript Buttons Bitwise
JS_MOUSE_LEFT_BIT = 1 << 0  # 1
JS_MOUSE_RIGHT_BIT = 1 << 1  # 2
JS_MOUSE_MIDDLE_BIT = 1 << 2  # 4
JS_MOUSE_BACK_BIT = 1 << 3  # 8
JS_MOUSE_FORWARD_BIT = 1 << 4  # 16

JS_MOUSE_LEFT = 0
JS_MOUSE_MIDDLE = 1
JS_MOUSE_RIGHT = 2
JS_MOUSE_BACK = 3  # Mouse 4
JS_MOUSE_FORWARD = 4  # Mouse 5

# Normal button presses are not bitwise.
_mouse_map = {
    JS_MOUSE_LEFT: mouse.LEFT,
    JS_MOUSE_MIDDLE: mouse.MIDDLE,
    JS_MOUSE_RIGHT: mouse.RIGHT,
    JS_MOUSE_BACK: mouse.MOUSE4,
    JS_MOUSE_FORWARD: mouse.MOUSE5,
}


def translate_mouse_bits(buttons: int) -> int:
    """Translate JavaScript mouse button values to match pyglet constants."""
    result = 0
    if buttons & JS_MOUSE_LEFT_BIT:  # JavaScript Left button
        result |= mouse.LEFT
    if buttons & JS_MOUSE_RIGHT_BIT:  # JavaScript Right button
        result |= mouse.RIGHT
    if buttons & JS_MOUSE_MIDDLE_BIT:  # JavaScript Middle button (wheel)
        result |= mouse.MIDDLE
    if buttons & JS_MOUSE_BACK_BIT:  # JavaScript Back (X1)
        result |= mouse.MOUSE4
    if buttons & JS_MOUSE_FORWARD_BIT:  # JavaScript Forward (X2)
        result |= mouse.MOUSE5
    return result


_EventHandler = TypeVar("_EventHandler", bound=Callable[..., Any])


def CanvasEventHandler(
    name: str, passive: bool | None = None,
) -> Callable[[_EventHandler], _EventHandler]:
    def _event_wrapper(f: _EventHandler) -> _EventHandler:
        f._canvas = True  # type: ignore[attr-defined]
        f._passive = passive  # type: ignore[attr-defined]
        f._platform_event = True  # type: ignore[attr-defined]  # noqa: SLF001
        if not hasattr(f, '_platform_event_data'):
            f._platform_event_data = []  # type: ignore[attr-defined]  # noqa: SLF001
        f._platform_event_data.append(name)  # type: ignore[attr-defined]  # noqa: SLF001
        return f

    return _event_wrapper


class JavascriptCursor(MouseCursor):
    api_drawable: bool = False
    hw_drawable: bool = True

    name: str

    def __init__(self, name: str) -> None:
        self.name = name


# Temporary
class EmscriptenWindow(BaseWindow['EmscriptenScreen']):
    """The HTML5 Canvas."""

    _mouse_cursor: MouseCursor
    _canvas: HTMLCanvasElement | None
    _context: WebGL2SurfaceContext | None
    _event_handlers: dict[str, JsProxy]
    _canvas_event_handlers: dict[str, JsProxy]
    _observer: ResizeObserver | None
    _proxy_resize: JsProxy | None
    _proxies: ProxyRegistry
    _keys_down: set[int | str]
    _clipboard_text: str
    _file_import_tasks: set[asyncio.Task[None]]
    _scale: float

    def __init__(
        self,
        width: int | None = None,
        height: int | None = None,
        caption: str | None = None,
        resizable: bool = False,
        style: str | None = None,
        fullscreen: bool = False,
        visible: bool = True,
        vsync: bool = True,
        file_drops: bool = False,
        display: Display[EmscriptenScreen] | None = None,
        screen: EmscriptenScreen | None = None,
        config: Config | Iterable[Config] | None = None,
        context: SurfaceContext | None = None,
        mode: ScreenMode | None = None,
    ) -> None:
        self._canvas = None
        self._event_handlers = {}
        self._canvas_event_handlers = {}
        self._observer = None
        self._proxy_resize = None
        self._proxies = ProxyRegistry()
        self._keys_down = set()
        self._clipboard_text = ""
        self._file_import_tasks = set()

        self._scale = js.window.devicePixelRatio
        super().__init__(
            width,
            height,
            caption,
            resizable,
            style,
            fullscreen,
            visible,
            vsync,
            file_drops,
            display,
            screen,
            config,
            context,
            mode,
        )
        self._enable_event_queue = False

    @property
    def scale(self) -> float:
        """The scale of the window factoring in DPI.

        Read only.
        """
        return self._scale

    @property
    def dpi(self) -> int:
        """DPI values of the Window.

        Read only.
        """
        return int(self._scale * 96)

    @property
    def canvas(self) -> HTMLCanvasElement | None:
        """The underlying Javascript Canvas element, if available.

        Read only.
        """
        return self._canvas

    def _set_event_handlers(self) -> None:
        assert self._canvas, "Canvas has not been created."
        for func_name in self._platform_event_names:
            if not hasattr(self, func_name):  # type: ignore[attr-defined]
                continue
            func = getattr(self, func_name)  # type: ignore[attr-defined]
            for message in func._platform_event_data:  # noqa: SLF001
                assert message not in self._event_handlers, f"event: '{message}' already exists."
                if hasattr(func, '_canvas'):
                    proxy = self._proxies.add_event_listener(
                        self._canvas, message, func, passive=func._passive,
                    )
                    self._canvas_event_handlers[message] = proxy
                else:
                    proxy = self._proxies.add_event_listener(js.window, message, func)
                    self._event_handlers[message] = proxy

        self._proxy_resize = self._proxies.create(self._event_resized)
        self._observer = js.ResizeObserver.new(self._proxy_resize)
        self._observer.observe(self._canvas)

    def close(self) -> None:
        """Remove browser callbacks before releasing the pyglet window."""
        if not self._context:
            return

        if self._observer is not None:
            self._observer.disconnect()
            self._observer = None
        self._proxies.destroy()
        self._proxy_resize = None
        self._canvas_event_handlers.clear()
        self._event_handlers.clear()
        self._touch_positions.clear()

        super().close()

    # PyCharm incorrectly substitutes the optional ScreenT in BaseWindow[EmscriptenScreen].
    # noinspection PyMethodOverriding
    def set_fullscreen(
        self,
        fullscreen: bool = True,
        screen: EmscriptenScreen | None = None,
        mode: ScreenMode | None = None,
        width: int | None = None,
        height: int | None = None,
    ) -> None:
        if (
            fullscreen == self._fullscreen
            and (screen is None or screen is self._screen)
            and (width is None or width == self._width)
            and (height is None or height == self._height)
        ):
            return

        if not self._fullscreen:
            self._windowed_size = self.get_size()

        self._fullscreen = fullscreen
        if self._fullscreen:
            self._canvas.requestFullscreen()
        else:
            js.document.exitFullscreen()

    def _enter_fullscreen(self, event: Event) -> None:
        self._fullscreen = True
        scale = js.window.devicePixelRatio
        self._canvas.width = js.window.innerWidth
        self._canvas.height = js.window.innerHeight

    def _exited_fullscreen(self, event: Event, width: int | None = None, height: int | None = None) -> None:
        self._fullscreen = False
        assert self._windowed_size is not None
        self._width, self._height = self._windowed_size
        self._canvas.width = self._width
        self._canvas.height = self._height
        if width is not None:
            self._width = width
        if height is not None:
            self._height = height

    def switch_to(self) -> None:
        pass

    def set_caption(self, caption: str) -> None:
        js.document.title = caption

    def set_minimum_size(self, width: int | str, height: int | str) -> None:
        self._minimum_size = width, height
        if isinstance(width, int) or isinstance(width, float):
            width = f"{width}px"

        if isinstance(width, int) or isinstance(width, float):
            height = f"{width}px"

        self._canvas.style.minWidth = width
        self._canvas.style.minHeight = height

    def set_maximum_size(self, width: int | str, height: int | str) -> None:
        self._maximum_size = width, height
        if isinstance(width, int) or isinstance(width, float):
            width = f"{width}px"

        if isinstance(width, int) or isinstance(width, float):
            height = f"{width}px"

        self._canvas.style.maxWidth = width
        self._canvas.style.maxHeight = height

    def set_size(self, width: int, height: int) -> None:
        super().set_size(width, height)
        self.adjust_scale(width, height)

    def get_size(self) -> tuple[int, int]:
        if not self._canvas:
            return self._width, self._height

        return self._canvas.width, self._canvas.height

    def set_location(self, x: int, y: int) -> None:
        # self.canvas.style.setProperty("position", "absolute")
        self._canvas.style.setProperty("left", f"{x}px")
        self._canvas.style.setProperty("top", f"{x}px")

    def get_location(self) -> tuple[int, int]:
        rect = self._canvas.getBoundingClientRect()
        return round(rect.left), round(rect.top)

    def activate(self) -> None:
        self._canvas.focus()

    def set_visible(self, visible: bool = True) -> None:
        if visible is False:
            if self._canvas.style.visibility != "hidden":
                self._canvas.visibility = "hidden"
        else:
            if self._canvas.style.visibility != "visible":
                self._canvas.visibility = "visible"

    def minimize(self) -> None:
        """While minimized, events will not occur."""
        self._canvas.style.display = "hidden"

    def maximize(self) -> None:
        self._canvas.style.display = "block"

    def set_vsync(self, vsync: bool) -> None:
        """A browser does not allow this."""

    @lru_cache  # noqa: B019
    def _create_data_url_from_image(self, cursor: ImageMouseCursor) -> str:
        """Create a cursor image from the data.

        Use a DATA URI as this allows converting the image into a cursor without fetching through HTTP.

        This does need to be in a PNG encoded format, so a temporary canvas is created to encode.
        """
        image = cursor.texture.get_image_data()
        canvas: HTMLCanvasElement = js.document.createElement("canvas")

        canvas.width = image.width
        canvas.height = image.height
        data = image.get_bytes('RGBA')
        pixel_array = js.Uint8ClampedArray.new(data)

        ctx = canvas.getContext("2d")
        image_data = ctx.createImageData(image.width, image.height)
        image_data.data.set(pixel_array)
        ctx.putImageData(image_data, 0, 0)

        data_url = canvas.toDataURL("image/png")
        canvas.remove()
        return data_url

    def set_mouse_cursor_platform_visible(self, platform_visible: bool | None = None) -> None:
        if not self._canvas:
            return

        if platform_visible is None:
            platform_visible = self._mouse_visible and (
                not self._mouse_cursor.api_drawable or self._mouse_cursor.hw_drawable
            )

        if platform_visible is False:
            cursor_name = "none"
        elif isinstance(self._mouse_cursor, ImageMouseCursor) and self._mouse_cursor.hw_drawable:
            # Create a custom hardware cursor.
            cursor_name = self._create_data_url_from_image(self._mouse_cursor)
            cursor_name = f"url({cursor_name}) {self._mouse_cursor.hot_x} {self._mouse_cursor.hot_y}, default"
        else:
            # Restore a standard hardware cursor
            if isinstance(self._mouse_cursor, DefaultMouseCursor):
                cursor_name = "default"
            elif isinstance(self._mouse_cursor, JavascriptCursor):
                cursor_name = self._mouse_cursor.name

        self._canvas.style.cursor = cursor_name

    def set_exclusive_mouse(self, exclusive: bool = True) -> None:
        assert self._canvas
        # Requires a user gesture to lock it like a button.
        if exclusive is True:
            self._canvas.requestPointerLock()
        else:
            js.document.exitPointerLock()

    def set_exclusive_keyboard(self, exclusive: bool = True) -> None:
        """Not relevant."""

    def get_clipboard_text(self) -> str:
        """Return the latest clipboard text received by the browser."""
        return self._clipboard_text

    def set_clipboard_text(self, text: str) -> None:
        """Set clipboard text when permitted, and retain it for a copy event."""
        self._clipboard_text = text
        try:
            js.navigator.clipboard.writeText(text)
        except Exception:
            # Browsers may deny programmatic clipboard access outside a user gesture.
            pass

    def get_system_mouse_cursor(self, name: str) -> DefaultMouseCursor | JavascriptCursor:
        if name == self.CURSOR_DEFAULT:
            return DefaultMouseCursor()

        return JavascriptCursor(name)

    def dispatch_events(self) -> None:
        """Process input events asynchronously."""
        raise Exception("Not implemented.")

    @staticmethod
    def _event_text_motion(symbol: int | str, modifiers: int) -> int | None:
        if modifiers & key.MOD_ALT:
            return None
        ctrl = modifiers & (key.MOD_CTRL | key.MOD_COMMAND) != 0
        return _motion_map.get((symbol, ctrl), None)

    @CanvasEventHandler("keydown")
    def _event_key_down(self, event: KeyboardEvent) -> None:
        if not event.repeat:
            text = None
            if len(event.key) == 1:
                text = event.key
            symbol, modifiers = js_key_to_pyglet(event)
            motion = self._event_text_motion(symbol, modifiers)
            modifiers_ctrl = modifiers & (key.MOD_CTRL | key.MOD_ALT)
            # If key A is pressed, then key B is pressed, if key A is released, key B will trigger a keydown.
            if symbol in self._keys_down:
                return
            if symbol:
                self._keys_down.add(symbol)  # Keep track of pressed internally.
                self.dispatch_event('on_key_press', symbol, modifiers)
            if motion and motion != key.MOTION_PASTE:
                if modifiers & key.MOD_SHIFT:
                    motion_event = 'on_text_motion_select'
                else:
                    motion_event = 'on_text_motion'
                self.dispatch_event(motion_event, motion)
            elif text and not modifiers_ctrl:
                self.dispatch_event('on_text', text)

    @CanvasEventHandler("keyup")
    def _event_key_up(self, event: KeyboardEvent) -> None:
        symbol, modifiers = js_key_to_pyglet(event)
        if symbol in self._keys_down:
            self._keys_down.remove(symbol)
        else:
            js.console.log(f"{event.key} was released but was not down. This should not occur.")

        self.dispatch_event('on_key_release', symbol, modifiers)

    def _dispatch_pointer_touch(self, dispatch_name: str, event: PointerEvent) -> None:
        rect = self._canvas.getBoundingClientRect()
        scale_x = self._canvas.width / rect.width if rect.width else self._scale
        scale_y = self._canvas.height / rect.height if rect.height else self._scale
        self._dispatch_touch_event(
            dispatch_name, event.pointerId,
            (event.clientX - rect.left) * scale_x,
            self._canvas.height - (event.clientY - rect.top) * scale_y,
            event.width * scale_x, event.height * scale_y, event.pressure,
        )

    @CanvasEventHandler("pointerdown", passive=False)
    def _event_touch_start(self, event: PointerEvent) -> None:
        if event.pointerType != "touch":
            return
        # Touch pointers implicitly capture subsequent events, including outside the canvas.
        # Cancel compatibility mouse events so a contact is not also reported as a mouse press.
        event.preventDefault()
        self._dispatch_pointer_touch('on_touch_start', event)

    @CanvasEventHandler("pointermove")
    def _event_touch_move(self, event: PointerEvent) -> None:
        if event.pointerType == "touch" and event.pointerId in self._touch_positions:
            self._dispatch_pointer_touch('on_touch_move', event)

    @CanvasEventHandler("pointerup")
    @CanvasEventHandler("pointercancel")
    def _event_touch_end(self, event: PointerEvent) -> None:
        if event.pointerType == "touch" and event.pointerId in self._touch_positions:
            self._dispatch_pointer_touch('on_touch_end', event)

    @CanvasEventHandler("lostpointercapture")
    def _event_touch_capture_lost(self, event: PointerEvent) -> None:
        if event.pointerType == "touch" and event.pointerId in self._touch_positions:
            # Capture-loss events do not carry the contact's last coordinates.
            x, y = self._touch_positions[event.pointerId]
            self._dispatch_touch_event('on_touch_end', event.pointerId, x, y, 0, 0, 0.0)

    @CanvasEventHandler("mousedown")
    def _event_mouse_down(self, event: MouseEvent) -> None:
        rect = self._canvas.getBoundingClientRect()
        modifiers = get_modifiers(event)
        pos_x = (event.clientX - rect.left) * self._scale
        pos_y = self._canvas.height - (event.clientY - rect.top) * self._scale
        self.dispatch_event(
            'on_mouse_press', pos_x, pos_y, _mouse_map.get(event.button, 0), modifiers,
        )

    @CanvasEventHandler("mouseup")
    def _event_mouse_up(self, event: MouseEvent) -> None:
        rect = self._canvas.getBoundingClientRect()
        modifiers = get_modifiers(event)
        pos_x = (event.clientX - rect.left) * self._scale
        pos_y = self._canvas.height - (event.clientY - rect.top) * self._scale
        self.dispatch_event(
            'on_mouse_release', pos_x, pos_y, _mouse_map.get(event.button, 0), modifiers,
        )

    @CanvasEventHandler("mousemove")
    async def _event_mouse_motion(self, event: MouseEvent) -> None:
        rect = self._canvas.getBoundingClientRect()
        if event.buttons:
            modifiers = get_modifiers(event)
            pos_x = (event.clientX - rect.left) * self._scale
            pos_y = self._canvas.height - (event.clientY - rect.top) * self._scale
            self.dispatch_event(
                'on_mouse_drag',
                pos_x,
                pos_y,
                event.movementX,
                event.movementY,
                _mouse_map.get(event.button, 0),
                modifiers,
            )
        else:
            pos_x = (event.clientX - rect.left) * self._scale
            pos_y = self._canvas.height - (event.clientY - rect.top) * self._scale
            self.dispatch_event(
                'on_mouse_motion', pos_x, pos_y, event.movementX, event.movementY,
            )

    @CanvasEventHandler("wheel", passive=False)
    def _event_mouse_scroll(self, event: WheelEvent) -> None:
        event.preventDefault()
        self.dispatch_event('on_mouse_scroll', event.clientX, event.clientY, event.deltaX, event.deltaY)

    @CanvasEventHandler("mouseenter")
    async def _event_mouse_enter(self, event: MouseEvent) -> None:
        self.dispatch_event('on_mouse_enter', event.clientX, self.height - event.clientY)

    @CanvasEventHandler("mouseleave")
    async def _event_mouse_leave(self, event: MouseEvent) -> None:
        self.dispatch_event('on_mouse_leave', event.clientX, self.height - event.clientY)

    @CanvasEventHandler("contextlost")
    async def _event_context_lost(self, event: Event) -> None:
        print("WebGL context lost!")

    @CanvasEventHandler("contextrestored")
    async def _event_context_restored(self, event: Event) -> None:
        print("WebGL context restored!")

    @CanvasEventHandler("focus")
    def _event_gain_focus(self, event: Event) -> None:
        pyglet.app.platform_event_loop.post_event(self, 'on_activate')

    @CanvasEventHandler("blur")
    def _event_lose_focus(self, event: Event) -> None:
        pyglet.app.platform_event_loop.post_event(self, 'on_deactivate')

    @CanvasEventHandler("contextmenu", passive=False)
    def _event_contextmenu(self, event: MouseEvent) -> None:
        # Some keys or mouse presses (right click) can open the browser context menu. Disable this.
        event.preventDefault()

    @CanvasEventHandler("copy", passive=False)
    def _event_copy(self, event: ClipboardEvent) -> None:
        event.preventDefault()
        event.clipboardData.setData("text/plain", self._clipboard_text)

    @CanvasEventHandler("paste", passive=False)
    def _event_paste(self, event: ClipboardEvent) -> None:
        event.preventDefault()
        text = event.clipboardData.getData("text/plain")
        self._clipboard_text = text
        self.dispatch_event("on_text", text)

    def _drop_position(self, event: DragEvent) -> tuple[float, float]:
        rect = self._canvas.getBoundingClientRect()
        return (
            (event.clientX - rect.left) * self._scale,
            self._canvas.height - (event.clientY - rect.top) * self._scale,
        )

    @staticmethod
    def _contains_files(event: DragEvent) -> bool:
        if event.dataTransfer is None:
            return False
        file_types = event.dataTransfer.types
        try:
            return bool(file_types.includes("Files"))
        except AttributeError:
            return bool(file_types.contains("Files"))

    @CanvasEventHandler("dragenter", passive=False)
    def _event_file_drag_enter(self, event: DragEvent) -> None:
        if self._file_drops and self._contains_files(event):
            event.preventDefault()
            self.dispatch_event("on_file_drag_enter", *self._drop_position(event), [])

    @CanvasEventHandler("dragleave", passive=False)
    def _event_file_drag_leave(self, event: DragEvent) -> None:
        if self._file_drops and self._contains_files(event):
            event.preventDefault()
            self.dispatch_event("on_file_drag_exit")

    @CanvasEventHandler("dragover", passive=False)
    def _event_file_drag_over(self, event: DragEvent) -> None:
        if self._file_drops and self._contains_files(event):
            event.preventDefault()
            event.dataTransfer.dropEffect = "copy"
            self.dispatch_event("on_file_drag", *self._drop_position(event), [])

    @CanvasEventHandler("drop", passive=False)
    def _event_file_drop(self, event: DragEvent) -> None:
        if not self._file_drops or not self._contains_files(event):
            return
        event.preventDefault()
        files = [
            cast("File", event.dataTransfer.files.item(index))
            for index in range(event.dataTransfer.files.length)
        ]
        task = asyncio.create_task(self._import_dropped_files(*self._drop_position(event), files))
        self._file_import_tasks.add(task)
        task.add_done_callback(self._file_import_tasks.discard)
        self.dispatch_event("on_file_drag_exit")

    async def _import_dropped_files(self, x: float, y: float, files: list[File]) -> None:
        self.dispatch_event("on_file_drop", x, y, await import_files(files))

    @CanvasEventHandler("fullscreenchange")
    def _event_fullscreen_change(self, event: Event) -> None:
        if js.document.fullscreenElement == self._canvas:
            self._enter_fullscreen(event)
        else:
            if self._windowed_size is not None:
                self._exited_fullscreen(event, *self._windowed_size)

    def get_framebuffer_size(self) -> tuple[int, int]:
        if self._context:
            return self._context.gl.drawingBufferWidth, self._context.gl.drawingBufferHeight
        return self.get_size()

    def get_current_screen(self) -> EmscriptenScreen:
        """Return the single screen exposed by the browser display."""
        return self._screen

    def _event_resized(self, entries: Iterable[ResizeObserverEntry], observer: ResizeObserver) -> None:
        for entry in entries:
            rect = entry.contentRect
            self.dispatch_event('_on_internal_resize', 0, 0)

    def dispatch_pending_events(self) -> None:
        pass

    def adjust_scale(self, width: float, height: float) -> None:
        ratio = js.window.devicePixelRatio or 1.0

        # The framebuffer size.
        self._canvas.width = width * ratio
        self._canvas.height = height * ratio

        # How large the canvas appears visually. Browser automatically scales based on DPI.
        self._canvas.style.width = f"{width}px"
        self._canvas.style.height = f"{height}px"

    def _create(self) -> None:
        assert self._canvas is None
        canvas_name = pyglet.options.pyodide.canvas_id
        canvas = js.document.getElementById(canvas_name)
        if not canvas:
            self._canvas = js.document.createElement("canvas")
            self._canvas.id = canvas_name
            js.document.body.appendChild(self._canvas)
        else:
            self._canvas = canvas

        self._canvas.width = self._width * self.scale
        self._canvas.height = self._height * self.scale
        self._canvas.style.width = f"{self._width}px"
        self._canvas.style.height = f"{self._height}px"
        # Delivers touch gestures to pyglet canvas, instead of browser panning and zooming.
        self._canvas.style.touchAction = "none"

        if not js.document.getElementById(canvas_name):
            msg = f"Canvas: {canvas_name} could not be created."
            raise Exception(msg)

        # By default, the canvas does not receive keyboard events.
        self._canvas.setAttribute("tabindex", "0")
        self._set_event_handlers()

        # When the canvas gets focus, it gains a white outline around it. Remove it.
        style = js.document.createElement("style")
        style.innerHTML = "#%s:focus { outline: none; }" % canvas_name
        js.document.head.appendChild(style)

        # Context must be created after window is created.
        self._assign_config()

        self.context.attach(self)

        rect = self._canvas.getBoundingClientRect()
        self.adjust_scale(rect.width, rect.height)


__all__ = ['EmscriptenWindow']
