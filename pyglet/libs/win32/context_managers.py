"""
Win32 resources as handy context managers.

These are intended to help keep loader code clean & stable at the price
of a tiny bit of execution speed. Performance-critical code should avoid
using these helpers in favor of direct win32 API calls.

Before::

    def loader_function(arg):
        context_handle = user32.GetResource(None)

        result = calculation(arg)

        # Easily forgotten!
        user32.ReleaseResource(context_handle)

        return result

After::

    def loader_function(arg):

        with resource_context() as context_handle:
            result = calculation(arg)

        return result

"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Callable, Generator, TYPE_CHECKING
from ctypes import WinError
from pyglet.libs.win32 import _user32 as user32

if TYPE_CHECKING:
    from pyglet.libs.win32.com import COMObject
    from ctypes.wintypes import HANDLE


@contextmanager
def device_context(window_handle: int | None = None) -> Generator[HANDLE, None, None]:
    """
    A Windows device context wrapped as a context manager.

    Args:
        window_handle: A specific window handle to use, if any.
    Raises:
        WinError: Raises if a device context cannot be acquired or released
    Yields:
        HANDLE: the managed drawing context handle to auto-close.

    """
    if not (_dc := user32.GetDC(window_handle)):
        raise WinError()

    try:
        yield _dc
    finally:
        if not user32.ReleaseDC(None, _dc):
            raise WinError()


@contextmanager
def com_context(com_object: COMObject) -> Generator[COMObject, None, None]:
    """A simple context manager for a COM object.

    This can help reduce missed release calls leading to leaks.
    """
    try:
        yield com_object
    finally:
        com_object.Release()


class _HResultManager:
    """Helper for managing multiple HRESULT ctypes calls.

    Typically, ctypes will output an ``OSError`` when the result < 0.
    """
    error: OSError | None
    last_result: int | None

    def __init__(self) -> None:
        self.last_result = None
        self.error = None

    def call(self, callback: Callable[..., int], *args: Any) -> int | None:
        """Invoke a ctypes callback and capture `OSError` as manager state."""
        self.error = None
        try:
            self.last_result = callback(*args)
            return self.last_result
        except OSError as err:
            self.error = err
            self.last_result = None
            return None

    @staticmethod
    def succeeded(result: int | None, acceptable: tuple[int, ...] = ()) -> bool:
        """Return success for a HRESULT value.

        Args:
            result:
                The value returned from a HRESULT-style API call.
            acceptable:
                Extra HRESULT values treated as acceptable for this call.
        """
        return result is not None and (result >= 0 or result in acceptable)

    def call_succeeded(self, callback: Callable[..., int], *args: Any, acceptable: tuple[int, ...] = ()) -> bool:
        """Call and check success in one step.

        Use `self.error` to inspect the captured `OSError` when this returns `False`.
        """
        return self.succeeded(self.call(callback, *args), acceptable=acceptable)

    def raise_if_failed(self, result: int | None, acceptable: tuple[int, ...] = ()) -> int:
        """Raise exception if the result is not successful.

        Raises:
            OSError:
                Re-raises captured ctypes `OSError`.
        """
        if self.succeeded(result, acceptable=acceptable):
            return int(result)

        if self.error is not None:
            raise self.error

        msg = f"HRESULT call failed with result {result}"
        raise OSError(msg)


@contextmanager
def hresult_context() -> Generator[_HResultManager, None, None]:
    """Context manager for grouped HRESULT checks."""
    yield _HResultManager()
