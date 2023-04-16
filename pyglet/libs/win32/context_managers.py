"""
Win32 resources as handy context managers.

These are intended to help keep loader code clean & stable at the price
of a tiny bit of execution speed.

Before::

    def loader_function(arg):
        context_handle = user32.GetResource(0)

        result = calculation(arg)

        # Easily forgotten!
        user32.ReleaseResource(context_handle)

        return result

After::

    def loader_function(arg):

        with ResourceContext(0) as context_handle:
            result = calculation(arg)

        return result

Performance-critical code should avoid using these classes in favor of
direct win32 API calls.
"""
import contextlib

import pyglet
from typing import Optional, Generator

if pyglet.compat_platform in ('win32', 'cygwin'):
    from ctypes.wintypes import HANDLE
    from ctypes import WinError
    from pyglet.libs.win32 import _user32 as user32

else:  # Nasty local imports for testing on non-Win32 systems
    from ctypes import c_void_p as HANDLE
    from unittest.mock import Mock

    user32 = Mock()
    user32.GetDC = lambda a: HANDLE()
    user32.attach_callable_mock('ReleaseDC', Mock())


@contextlib.contextmanager
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
    if _dc := user32.GetDC(window_handle) is None:
        raise WinError()
    try:
        yield _dc
    finally:
        if not user32.ReleaseDC(None, _dc):
            raise WinError()
