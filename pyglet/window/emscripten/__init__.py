from __future__ import annotations

import asyncio
from typing import Sequence, TYPE_CHECKING, Any

import pyglet.app
from pyglet.display.base import Display, Screen, ScreenMode
from pyglet.window import key
# from pyglet.window import mouse
from pyglet.event import EventDispatcher, EVENT_HANDLE_STATE

from pyglet.window import (
    BaseWindow,
)

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
    symbol = None
    modifiers = 0

    # Use event.code if available
    if event.code in code_map:
        symbol = code_map[event.code]
    # Check special character mapping (needed for characters like `@`, `!`)
    elif event.key in chmap:
        symbol = chmap[event.key]
    # If nothing found, use event.key as a fallback
    else:
        print(f"Warning: Unmapped key -> {event.code} ({event.key})")

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

# Temporary
class EmscriptenWindow(BaseWindow):
    """The HTML5 Canvas."""

    def __init__(self, width: int | None = None, height: int | None = None, caption: str | None = None,
                 resizable: bool = False, style: str | None = None, fullscreen: bool = False,
                 visible: bool = True, vsync: bool = True, file_drops: bool = False, display: Display | None = None,
                 screen: Screen | None = None, config: GraphicsConfig | None = None,
                 context: WindowGraphicsContext | None = None, mode: ScreenMode | None = None) -> None:
        self.canvas = None
        super().__init__(width, height, caption, resizable, style, fullscreen, visible, vsync, file_drops, display,
                         screen, config, context, mode)
        self._enable_event_queue = False

    def _recreate(self, changes: Sequence[str]) -> None:
        pass

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

    def set_minimum_size(self, width: int, height: int) -> None:
        pass

    def set_maximum_size(self, width: int, height: int) -> None:
        pass

    def set_size(self, width: int, height: int) -> None:
        self._width = width
        self._height = height
        self.canvas.width = width
        self.canvas.height = height

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

    def set_mouse_platform_visible(self, platform_visible: bool | None = None) -> None:
        pass

    def set_exclusive_mouse(self, exclusive: bool = True) -> None:
        pass

    def set_exclusive_keyboard(self, exclusive: bool = True) -> None:
        pass

    def get_system_mouse_cursor(self, name: str) -> None:
        pass

    async def dispatch_events(self) -> None:
        """Process input events asynchronously."""
        print("should not be called")
        # while True:
        #     event = await self._event_queue.get()
        #
        #     # Call corresponding event functions
        #     if event["type"] == "key_press":
        #         print(f"on_key_press(symbol={event['symbol']}, modifiers={event['modifiers']})")
        #     elif event["type"] == "key_release":
        #         print(f"on_key_release(symbol={event['symbol']}, modifiers={event['modifiers']})")
        #     elif event["type"] == "mouse_motion":
        #         print(f"on_mouse_motion(x={event['x']}, y={event['y']}, dx={event['dx']}, dy={event['dy']})")
        #     elif event["type"] == "mouse_press":
        #         print(
        #             f"on_mouse_press(x={event['x']}, y={event['y']}, button={event['buttons']}, modifiers={event['modifiers']})")
        #     elif event["type"] == "mouse_release":
        #         print(
        #             f"on_mouse_release(x={event['x']}, y={event['y']}, button={event['buttons']}, modifiers={event['modifiers']})")
        #     elif event["type"] == "mouse_scroll":
        #         print(
        #             f"on_mouse_scroll(x={event['x']}, y={event['y']}, scroll_x={event['scroll_x']}, scroll_y={event['scroll_y']})")
        #     elif event["type"] == "mouse_enter":
        #         print(f"on_mouse_enter(x={event['x']}, y={event['y']})")
        #     elif event["type"] == "mouse_leave":
        #         print(f"on_mouse_leave(x={event['x']}, y={event['y']})")

    def _add_listeners(self, canvas):
        print("ADD LISTENERS")
        async def on_key_down(event):
            """Handle key press event."""
            symbol, modifier = js_key_to_pyglet(event)
            await pyglet.app.platform_event_loop.post_event(self, 'on_key_press', symbol, modifier)


        async def on_key_up(event):
            """Handle key release event."""
            symbol, modifier = js_key_to_pyglet(event)
            await pyglet.app.platform_event_loop.post_event(self, 'on_key_release', symbol, modifier)

        async def on_mouse_up(event):
            """Handle key release event."""
            modifiers = get_modifiers(event)
            await pyglet.app.platform_event_loop.post_event(self, 'on_mouse_release',
                                                                     event.clientX,
                                                                     self.height - event.clientY,
                                                                     translate_mouse_button(event.button),
                                                                     modifiers)

        async def on_mouse_move(event):
            """Handle key release event."""
            await pyglet.app.platform_event_loop.post_event(self, 'on_mouse_motion',
                                                                     event.clientX,
                                                                     self.height - event.clientY,
                                                                     event.movementX,
                                                                     event.movementY)

        async def on_mouse_down(event):
            """Handle key release event."""
            modifiers = get_modifiers(event)
            await pyglet.app.platform_event_loop.post_event(self, 'on_mouse_press',
                                                                     event.clientX,
                                                                     self.height - event.clientY,
                                                                     translate_mouse_button(event.button),
                                                                     modifiers)
        async def on_mouse_scroll(event):
            """Handle key release event."""
            await pyglet.app.platform_event_loop.post_event(self, 'on_mouse_scroll',
                                                                     event.clientX,
                                                                     event.clientY,
                                                                     event.deltaX,
                                                                     event.deltaY)

        # def on_mouse_enter(event):
        #     """Handle mouse entering the canvas."""
        #     asyncio.create_task(self._event_queue.put({
        #         "type": "mouse_enter",
        #         "x": event.clientX,
        #         "y": event.clientY
        #     }))
        #
        # def on_mouse_leave(event):
        #     """Handle mouse leaving the canvas."""
        #     asyncio.create_task(self._event_queue.put({
        #         "type": "mouse_leave",
        #         "x": event.clientX,
        #         "y": event.clientY
        #     }))
        def on_context_lost(event):
            print("WebGL context lost!");

        # Attach event listeners to the canvas
        canvas.addEventListener("keydown", create_proxy(on_key_down))
        canvas.addEventListener("keyup", create_proxy(on_key_up))
        #canvas.addEventListener("mousemove", create_proxy(on_mouse_move))
        canvas.addEventListener("mousedown", create_proxy(on_mouse_down))
        canvas.addEventListener("mouseup", create_proxy(on_mouse_up))
        canvas.addEventListener("wheel", create_proxy(on_mouse_scroll))
        # canvas.addEventListener("mouseenter", create_proxy(on_mouse_enter))
        # canvas.addEventListener("mouseleave", create_proxy(on_mouse_leave))

        canvas.addEventListener("webglcontextlost", create_proxy(on_context_lost))

        print("REGISTERED EVENTS")

        # Ensure the canvas can receive keyboard input
        canvas.setAttribute("tabindex", "1")
        canvas.focus()

    def dispatch_pending_events(self) -> None:
        pass

    def _create(self) -> None:
        assert self.canvas is None
        self.canvas = js.document.getElementById("pygletCanvas")
        if self.canvas:
            self._add_listeners(self.canvas)

            # Context must be created after window is created.
            if pyglet.options.backend == "webgl":
                self._assign_config()
                self.context.attach(self)

                self.context.start_render()



__all__ = ['EmscriptenWindow']
