from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Sequence, TYPE_CHECKING, Any, Callable

import pyglet.app
from pyglet.display.base import Display, Screen, ScreenMode
from pyglet.window import key, BaseWindow, MouseCursor, ImageMouseCursor


import js  # noqa
from pyodide.ffi import create_proxy  # noqa

if TYPE_CHECKING:
    from pyglet.graphics.api import GraphicsConfig
    from pyglet.graphics.api.base import WindowGraphicsContext


# Keymap using `event.code`
code_map = {
    "KeyA": key.A, "KeyB": key.B, "KeyC": key.C, "KeyD": key.D, "KeyE": key.E,
    "KeyF": key.F, "KeyG": key.G, "KeyH": key.H, "KeyI": key.I, "KeyJ": key.J,
    "KeyK": key.K, "KeyL": key.L, "KeyM": key.M, "KeyN": key.N, "KeyO": key.O,
    "KeyP": key.P, "KeyQ": key.Q, "KeyR": key.R, "KeyS": key.S, "KeyT": key.T,
    "KeyU": key.U, "KeyV": key.V, "KeyW": key.W, "KeyX": key.X, "KeyY": key.Y,
    "KeyZ": key.Z,

    "Digit0": key._0, "Digit1": key._1, "Digit2": key._2, "Digit3": key._3, "Digit4": key._4,
    "Digit5": key._5, "Digit6": key._6, "Digit7": key._7, "Digit8": key._8, "Digit9": key._9,

    "Backspace": key.BACKSPACE, "Tab": key.TAB, "Enter": key.RETURN, "ShiftLeft": key.LSHIFT, "ShiftRight": key.RSHIFT,
    "ControlLeft": key.LCTRL, "ControlRight": key.RCTRL, "AltLeft": key.LALT, "AltRight": key.RALT,
    "Escape": key.ESCAPE, "Space": key.SPACE,

    "ArrowLeft": key.LEFT, "ArrowUp": key.UP, "ArrowRight": key.RIGHT, "ArrowDown": key.DOWN,

    "F1": key.F1, "F2": key.F2, "F3": key.F3, "F4": key.F4, "F5": key.F5, "F6": key.F6, "F7": key.F7,
    "F8": key.F8, "F9": key.F9, "F10": key.F10, "F11": key.F11, "F12": key.F12,

    "Numpad0": key.NUM_0, "Numpad1": key.NUM_1, "Numpad2": key.NUM_2, "Numpad3": key.NUM_3,
    "Numpad4": key.NUM_4, "Numpad5": key.NUM_5, "Numpad6": key.NUM_6, "Numpad7": key.NUM_7,
    "Numpad8": key.NUM_8, "Numpad9": key.NUM_9, "NumpadMultiply": key.NUM_MULTIPLY,
    "NumpadAdd": key.NUM_ADD, "NumpadSubtract": key.NUM_SUBTRACT, "NumpadDecimal": key.NUM_DECIMAL,
    "NumpadDivide": key.NUM_DIVIDE,

    "CapsLock": key.CAPSLOCK, "NumLock": key.NUMLOCK, "ScrollLock": key.SCROLLLOCK,

}

# Special character mapping (needed for `event.key`)
chmap = {
    "!": key.EXCLAMATION, "@": key.AT, "#": key.HASH, "$": key.DOLLAR, "%": key.PERCENT,
    "^": key.ASCIICIRCUM, "&": key.AMPERSAND, "*": key.ASTERISK, "(": key.PARENLEFT,
    ")": key.PARENRIGHT, "-": key.MINUS, "_": key.UNDERSCORE, "=": key.EQUAL, "+": key.PLUS,
    "[": key.BRACKETLEFT, "]": key.BRACKETRIGHT, "{": key.BRACELEFT, "}": key.BRACERIGHT,
    ";": key.SEMICOLON, ":": key.COLON, "'": key.APOSTROPHE, "\"": key.DOUBLEQUOTE,
    "\\": key.BACKSLASH, "|": key.BAR, ",": key.COMMA, ".": key.PERIOD, "/": key.SLASH,
    "?": key.QUESTION, "`": key.GRAVE, "~": key.ASCIITILDE
}

def get_modifiers(event) -> int:
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
def js_key_to_pyglet(event):
    """Convert JS event code to the equivalent key mapping."""
    modifiers = 0

    # Use event.code if available
    if event.code in code_map:
        symbol = code_map[event.code]
    # Check special character mapping (needed for characters like `@`, `!`)
    elif event.key in chmap:
        symbol = chmap[event.key]
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

def translate_mouse_button(value: int) -> int:
    """Translate JavaScript mouse button values to match pyglet constants."""
    if value < 5:
        return 1 << value  # Shift like in Xlib
    return 0  # Ignore unsupported buttons

def BrowserWindowEventHandler(name: str):
    def _event_wrapper(f: Callable) -> Callable:
        f._platform_event = True  # noqa: SLF001
        if not hasattr(f, '_platform_event_data'):
            f._platform_event_data = []  # noqa: SLF001
        f._platform_event_data.append(name)  # noqa: SLF001
        return f

    return _event_wrapper

def CanvasEventHandler(name: str):
    def _event_wrapper(f: Callable) -> Callable:
        f._canvas = True
        f._platform_event = True  # noqa: SLF001
        if not hasattr(f, '_platform_event_data'):
            f._platform_event_data = []  # noqa: SLF001
        f._platform_event_data.append(name)  # noqa: SLF001
        return f

    return _event_wrapper

class JavascriptCursor(MouseCursor):
    api_drawable: bool = False
    hw_drawable: bool = True
    def __init__(self, name: str):
        self.name = name

class DefaultMouseCursor(JavascriptCursor):

    def __init__(self):
        super().__init__('default')


# Temporary
class EmscriptenWindow(BaseWindow):
    """The HTML5 Canvas."""
    _mouse_cursor: JavascriptCursor

    def __init__(self, width: int | None = None, height: int | None = None, caption: str | None = None,
                 resizable: bool = False, style: str | None = None, fullscreen: bool = False,
                 visible: bool = True, vsync: bool = True, file_drops: bool = False, display: Display | None = None,
                 screen: Screen | None = None, config: GraphicsConfig | None = None,
                 context: WindowGraphicsContext | None = None, mode: ScreenMode | None = None) -> None:
        self.canvas = None
        self._event_handlers: dict[int, Callable] = {}
        self._canvas_event_handlers: dict[int, Callable] = {}

        self._scale = js.window.devicePixelRatio
        super().__init__(width, height, caption, resizable, style, fullscreen, visible, vsync, file_drops, display,
                         screen, config, context, mode)
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

    def _set_event_handlers(self):
        assert self.canvas, "Canvas has not been created."
        for func_name in self._platform_event_names:
            if not hasattr(self, func_name):
                continue
            func = getattr(self, func_name)
            for message in func._platform_event_data:  # noqa: SLF001
                assert message not in self._event_handlers, f"event: '{message}' already exists."
                proxy = create_proxy(func)
                if hasattr(func, '_canvas'):
                    self._canvas_event_handlers[message] = func
                    self.canvas.addEventListener(message, proxy)
                else:
                    self._event_handlers[message] = func
                    js.window.addEventListener(message, proxy)

        self._proxy_resize = create_proxy(self._event_resized)
        self._observer = js.ResizeObserver.new(self._proxy_resize)
        self._observer.observe(self.canvas)

    def set_fullscreen(self, fullscreen: bool = True, _screen: Screen | None = None, mode: ScreenMode | None = None,
                       width: int | None = None, height: int | None = None) -> None:
        if (fullscreen == self._fullscreen and
                (_screen is None or _screen is self._screen) and
                (width is None or width == self._width) and
                (height is None or height == self._height)):
            return

        if not self._fullscreen:
            self._windowed_size = self.get_size()

        self._fullscreen = fullscreen
        if self._fullscreen:
            self.canvas.requestFullscreen()
        else:
            js.document.exitFullscreen()

    def _enter_fullscreen(self, event):
        self._fullscreen = True
        scale = js.window.devicePixelRatio
        self.canvas.width = js.window.innerWidth
        self.canvas.height = js.window.innerHeight

    def _exited_fullscreen(self, event, width: int | None = None,height: int | None = None):
        self._fullscreen = False
        self._width, self._height = self._windowed_size
        self.canvas.width = self._width
        self.canvas.height = self._height
        if width is not None:
            self._width = width
        if height is not None:
            self._height = height

    def flip(self) -> None:
        if self._context:
            self._context.flip()

    def switch_to(self) -> None:
        pass

    def before_draw(self) -> None:
        if self._context:
            self._context.before_draw()

    def set_caption(self, caption: str) -> None:
        js.document.title = caption

    def set_minimum_size(self, width: int | str, height: int | str) -> None:
        self._minimum_size = width, height
        if isinstance(width, int) or isinstance(width, float):
            width = f"{width}px"

        if isinstance(width, int) or isinstance(width, float):
            height = f"{width}px"

        self.canvas.style.minWidth = width
        self.canvas.style.minHeight = height

    def set_maximum_size(self, width: int | str, height: int | str) -> None:
        self._maximum_size = width, height
        if isinstance(width, int) or isinstance(width, float):
            width = f"{width}px"

        if isinstance(width, int) or isinstance(width, float):
            height = f"{width}px"

        self.canvas.style.maxWidth = width
        self.canvas.style.maxHeight = height

    def set_size(self, width: int, height: int) -> None:
        super().set_size(width, height)
        self.adjust_scale(width, height)

    def get_size(self) -> tuple[int, int]:
        if not self.canvas:
            return self._width, self._height

        return self.canvas.width, self.canvas.height

    def set_location(self, x: int, y: int) -> None:
        #self.canvas.style.setProperty("position", "absolute")
        self.canvas.style.setProperty("left", f"{x}px")
        self.canvas.style.setProperty("top", f"{x}px")

    def get_location(self) -> tuple[int, int]:
        rect = self.canvas.getBoundingClientRect()
        return rect.left, rect.top

    def activate(self) -> None:
        self.canvas.focus()

    def set_visible(self, visible: bool = True) -> None:
        if visible is False:
            if self.canvas.style.visibility != "hidden":
                self.canvas.visibility = "hidden"
        else:
            if self.canvas.style.visibility != "visible":
                self.canvas.visibility = "visible"

    def minimize(self) -> None:
        """While minimized, events will not occur."""
        self.canvas.style.display = "hidden"

    def maximize(self) -> None:
        self.canvas.style.display = "block"

    def set_vsync(self, vsync: bool) -> None:
        """A browser does not allow this."""

    @lru_cache  # noqa: B019
    def _create_data_url_from_image(self, cursor: ImageMouseCursor) -> str:
        """Create a cursor image from the data.

        Use a DATA URI as this allows converting the image into a cursor without fetching through HTTP.

        This does need to be in a PNG encoded format, so a temporary canvas is created to encode.
        """
        image = cursor.texture.get_image_data()
        canvas = js.document.createElement("canvas")

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

    def set_mouse_platform_visible(self, platform_visible: bool | None = None) -> None:
        if not self.canvas:
            return

        if platform_visible is None:
            platform_visible = (self._mouse_visible and
                                (not self._mouse_cursor.api_drawable or self._mouse_cursor.hw_drawable))

        if platform_visible is False:
            cursor_name = "none"
        elif isinstance(self._mouse_cursor, ImageMouseCursor) and self._mouse_cursor.hw_drawable:
            # Create a custom hardware cursor.
            cursor_name = self._create_data_url_from_image(self._mouse_cursor)
            cursor_name = f"url({cursor_name}) {self._mouse_cursor.hot_x} {self._mouse_cursor.hot_y}, default"
        else:
            # Restore a standard hardware cursor
            cursor_name = self._mouse_cursor.name

        self.canvas.style.cursor = cursor_name

    def set_exclusive_mouse(self, exclusive: bool = True) -> None:
        assert self.canvas
        # Requires a user gesture to lock it like a button.
        if exclusive is True:
            self.canvas.requestPointerLock()
        else:
            self.canvas.exitPointerLock()

    def set_exclusive_keyboard(self, exclusive: bool = True) -> None:
        """Not relevant."""

    def get_system_mouse_cursor(self, name: str) -> JavascriptCursor:
        if name == self.CURSOR_DEFAULT:
            return DefaultMouseCursor()

        return JavascriptCursor(name)

    async def dispatch_events(self) -> None:
        """Process input events asynchronously."""
        raise Exception("Not implemented.")

    @CanvasEventHandler("keydown")
    async def _event_key_down(self, event):
        if not event.repeat:
            symbol, modifier = js_key_to_pyglet(event)
            await pyglet.app.platform_event_loop.post_event(self, 'on_key_press', symbol, modifier)

    @CanvasEventHandler("keyup")
    async def _event_key_up(self, event):
        symbol, modifier = js_key_to_pyglet(event)
        await pyglet.app.platform_event_loop.post_event(self, 'on_key_release', symbol, modifier)

    @CanvasEventHandler("mousedown")
    async def _event_mouse_down(self, event):
        modifiers = get_modifiers(event)
        await pyglet.app.platform_event_loop.post_event(self, 'on_mouse_press',
                                                                 event.clientX,
                                                                 self.height - event.clientY,
                                                                 translate_mouse_button(event.button),
                                                                 modifiers)

    @CanvasEventHandler("mouseup")
    async def _event_mouse_up(self, event):
        modifiers = get_modifiers(event)
        await pyglet.app.platform_event_loop.post_event(self, 'on_mouse_release',
                                                                 event.clientX,
                                                                 self.height - event.clientY,
                                                                 translate_mouse_button(event.button),
                                                                 modifiers)

    @CanvasEventHandler("mousemove")
    async def _event_mouse_motion(self, event):
        await pyglet.app.platform_event_loop.post_event(self, 'on_mouse_motion',
                                                                 event.clientX,
                                                                 self.height - event.clientY,
                                                                 event.movementX,
                                                                 event.movementY)

    @CanvasEventHandler("wheel")
    async def _event_mouse_scroll(self, event):
        await pyglet.app.platform_event_loop.post_event(self, 'on_mouse_scroll',
                                                                 event.clientX,
                                                                 event.clientY,
                                                                 event.deltaX,
                                                                 event.deltaY)

    @CanvasEventHandler("mouseenter")
    async def _event_mouse_enter(self, event):
        await pyglet.app.platform_event_loop.post_event(self, 'on_mouse_enter',
                                                        event.clientX,
                                                        self.height - event.clientY)

    @CanvasEventHandler("mouseleave")
    async def _event_mouse_leave(self, event):
        await pyglet.app.platform_event_loop.post_event(self, 'on_mouse_leave',
                                                        event.clientX,
                                                        self.height - event.clientY)
    @CanvasEventHandler("contextlost")
    async def _event_context_lost(self, event):
        print("WebGL context lost!")

    @CanvasEventHandler("contextrestored")
    async def _event_context_restored(self, event):
        print("WebGL context restored!")

    @CanvasEventHandler("focus")
    async def _event_gain_focus(self, event):
        print("Focused!")

    @CanvasEventHandler("blur")
    async def _event_lose_focus(self, event):
        print("Lost focus!")

    @CanvasEventHandler("contextmenu")
    def _event_contextmenu(self, event):
        # Some keys or mouse presses (right click) can open the browser context menu. Disable this.
        event.preventDefault()

    @CanvasEventHandler("fullscreenchange")
    def _event_fullscreen_change(self, event):
        if js.document.fullscreenElement == self.canvas:
            self._enter_fullscreen(event)
        else:
            self._exited_fullscreen(event, *self._windowed_size)

    def get_framebuffer_size(self):
        return self._width, self._height

    def _event_resized(self, entries, observer):
        for entry in entries:
            rect = entry.contentRect
            print(f"Canvas resized to {rect.width}x{rect.height}")
            #Update internal resolution if needed

            self.dispatch_event('_on_internal_resize', 0, 0)

    def dispatch_pending_events(self) -> None:
        pass

    # copy, cut, paste, dragenter, dragleave,dragover, drop
    # touchmove, touchstart, touchend, touchcancel

    def adjust_scale(self, width, height):
        ratio = js.window.devicePixelRatio or 1.0

        # The framebuffer size.
        self.canvas.width = width * ratio
        self.canvas.height = height * ratio

        # How large the canvas appears visually. Browser automatically scales based on DPI.
        self.canvas.style.width = f"{width}px"
        self.canvas.style.height = f"{height}px"

    def _create(self) -> None:
        assert self.canvas is None
        canvas_name = "pygletCanvas"
        canvas = js.document.getElementById(canvas_name)
        if not self.canvas:
            self.canvas = js.document.createElement("canvas")
            self.canvas.id = canvas_name
            js.document.body.appendChild(self.canvas)
        else:
            self.canvas = canvas

        self.canvas.width = self._width * self.scale
        self.canvas.height = self._height * self.scale
        self.canvas.style.width = f"{self._width}px"
        self.canvas.style.height = f"{self._height}px"

        if not js.document.getElementById(canvas_name):
            raise Exception(f"Canvas: {canvas_name} could not be created.")

        # By default, the canvas does not receive keyboard events.
        self.canvas.setAttribute("tabindex", "0")
        self._set_event_handlers()

        # When the canvas gets focus, it gains a white outline around it. Remove it.
        style = js.document.createElement("style")
        style.innerHTML = "#%s:focus { outline: none; }" % canvas_name
        js.document.head.appendChild(style)

        # Context must be created after window is created.
        if pyglet.options.backend == "webgl":
            self._assign_config()

            self.context.attach(self)

            rect = self.canvas.getBoundingClientRect()
            self.adjust_scale(rect.width, rect.height)
            self.context.start_render()



__all__ = ['EmscriptenWindow']
