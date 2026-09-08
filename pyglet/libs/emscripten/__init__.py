"""Shared helpers for the Emscripten platform."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

import js  # noqa: F821
from pyodide.ffi import create_proxy, to_js  # noqa: F821


def copy_to_js_uint8_array(data: Any) -> js.Uint8Array:
    """Return an independent JavaScript ``Uint8Array`` containing ``data``.

    Use this for browser APIs that may retain their input after the call.
    """
    if isinstance(data, (bytes, bytearray, memoryview)):
        view = data if isinstance(data, memoryview) else memoryview(data)
        return to_js(view)
    return js.Uint8Array.new(data)


class PersistentBufferView:
    """A retained zero-copy JavaScript view of a Python buffer.

    Release this view before the underlying Python buffer is resized or
    discarded. ``data`` and views returned by :meth:`subarray` are invalid
    after :meth:`release`.
    """

    def __init__(self, data: bytes | bytearray | memoryview) -> None:
        view = data if isinstance(data, memoryview) else memoryview(data)
        if not view.c_contiguous:
            raise ValueError("PersistentBufferView requires a C-contiguous buffer.")

        self._proxy = create_proxy(view)
        self._buffer = self._proxy.getBuffer("u8")
        self.data = self._buffer.data

    def subarray(self, offset: int, length: int) -> js.Uint8Array:
        """Return a zero-copy byte subview within the retained buffer."""
        return self.data.subarray(offset, offset + length)

    def release(self) -> None:
        """Release the borrowed view and its Python proxy."""
        self._buffer.release()
        self._proxy.destroy()


@contextmanager
def zero_copy(data: Any) -> Iterator[js.Uint8Array]:
    """Yield a temporary JavaScript byte view over a contiguous Python buffer.

    The yielded view is only valid inside this context. Browser APIs must
    consume it synchronously before the context exits and releases the buffer.
    JavaScript typed arrays already meet that requirement and are yielded
    unchanged.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        yield data
        return

    view = data if isinstance(data, memoryview) else memoryview(data)
    if not view.c_contiguous:
        raise ValueError("zero_copy requires a C-contiguous buffer.")

    proxy = create_proxy(view)
    buffer = proxy.getBuffer("u8")
    try:
        yield buffer.data
    finally:
        buffer.release()
        proxy.destroy()
