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
from contextlib import contextmanager
from typing import Optional, Generator
from ctypes.wintypes import HANDLE
from ctypes import WinError
from pyglet.libs.win32 import _user32 as user32


@contextmanager
def device_context(window_handle: Optional[int] = None) -> Generator[HANDLE, None, None]:
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
