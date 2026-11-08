"""Browser interfaces used by the Emscripten window backend.

These objects are supplied by JavaScript through Pyodide, not instantiated
from Python. Keep imports of this module inside TYPE_CHECKING blocks.
"""
from collections.abc import Awaitable
from typing import Any, Literal, overload

from pyodide.ffi import JsProxy

from pyglet.graphics.api.webgl.webgl_js import WebGL2RenderingContext

class DOMRect:
    x: float
    y: float
    left: float
    top: float
    right: float
    bottom: float
    width: float
    height: float

class CSSStyleDeclaration:
    cssText: str
    width: str
    height: str
    minWidth: str
    minHeight: str
    maxWidth: str
    maxHeight: str
    visibility: str
    display: str
    cursor: str
    touchAction: str
    def setProperty(self, property: str, value: str, priority: str = "") -> None: ...

class Event:
    type: str
    isTrusted: bool
    def preventDefault(self) -> None: ...

class UIEvent(Event): ...

class KeyboardEvent(UIEvent):
    isComposing: bool
    key: str
    code: str
    repeat: bool
    ctrlKey: bool
    shiftKey: bool
    altKey: bool
    metaKey: bool

class MouseEvent(UIEvent):
    clientX: float
    clientY: float
    movementX: float
    movementY: float
    button: int
    buttons: int
    ctrlKey: bool
    shiftKey: bool
    altKey: bool
    metaKey: bool

class PointerEvent(MouseEvent):
    pointerId: int
    pointerType: str
    width: float
    height: float
    pressure: float
    tiltX: float
    tiltY: float
    twist: float

class WheelEvent(MouseEvent):
    deltaX: float
    deltaY: float

class InputEvent(UIEvent):
    isComposing: bool
    inputType: str
    data: str | None

class HTMLTextControl:
    type: str
    value: str
    inputMode: str
    enterKeyHint: str
    spellcheck: bool
    selectionStart: int
    selectionEnd: int
    selectionDirection: str
    style: CSSStyleDeclaration
    def setAttribute(self, name: str, value: str) -> None: ...
    def setSelectionRange(self, start: int, end: int, direction: str = ...) -> None: ...
    def focus(self, *, preventScroll: bool = ...) -> None: ...
    def remove(self) -> None: ...
    def addEventListener(self, type: str, callback: JsProxy, *, passive: bool = ...) -> None: ...
    def removeEventListener(self, type: str, callback: JsProxy) -> None: ...

class File:
    name: str
    def arrayBuffer(self) -> Awaitable[JsProxy]: ...

class FileList:
    length: int
    def item(self, index: int) -> File | None: ...

class DataTransferTypes:
    def includes(self, value: str) -> bool: ...
    def contains(self, value: str) -> bool: ...

class DataTransfer:
    types: DataTransferTypes
    files: FileList
    dropEffect: str
    def setData(self, format: str, data: str) -> None: ...
    def getData(self, format: str) -> str: ...

class DragEvent(MouseEvent):
    dataTransfer: DataTransfer | None

class ClipboardEvent(Event):
    clipboardData: DataTransfer | None

class Uint8ClampedArray:
    length: int
    def set(self, source: JsProxy, offset: int = 0) -> None: ...

class ImageData:
    width: int
    height: int
    data: Uint8ClampedArray

class CanvasRenderingContext2D:
    def createImageData(self, width: int, height: int) -> ImageData: ...
    def putImageData(self, image: ImageData, x: float, y: float) -> None: ...

class HTMLCanvasElement:
    def setPointerCapture(self, pointer_id: int) -> None: ...
    id: str
    # Assignments are coerced to unsigned integers by the browser.
    @property
    def width(self) -> int: ...
    @width.setter
    def width(self, value: float) -> None: ...
    @property
    def height(self) -> int: ...
    @height.setter
    def height(self, value: float) -> None: ...
    style: CSSStyleDeclaration
    def getBoundingClientRect(self) -> DOMRect: ...
    def setAttribute(self, name: str, value: str) -> None: ...
    def focus(self) -> None: ...
    def remove(self) -> None: ...
    def requestFullscreen(self) -> Awaitable[None]: ...
    def requestPointerLock(self) -> Awaitable[None] | None: ...
    def toDataURL(self, type: str = "image/png", quality: float = ...) -> str: ...
    @overload
    def getContext(self, context_id: Literal["2d"], **options: Any) -> CanvasRenderingContext2D | None: ...
    @overload
    def getContext(self, context_id: Literal["webgl2"], **options: Any) -> WebGL2RenderingContext | None: ...
    def addEventListener(self, type: str, callback: JsProxy, *, passive: bool = ...) -> None: ...
    def removeEventListener(self, type: str, callback: JsProxy) -> None: ...

class ResizeObserverEntry:
    target: HTMLCanvasElement
    contentRect: DOMRect

class ResizeObserver:
    def observe(self, target: HTMLCanvasElement) -> None: ...
    def disconnect(self) -> None: ...
