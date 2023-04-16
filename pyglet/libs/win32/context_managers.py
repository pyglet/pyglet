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
import pyglet
from typing import Optional


if pyglet.compat_platform in ('win32', 'cygwin'):
    from ctypes.wintypes import HANDLE
    from ctypes import WinError
    from pyglet.libs.win32 import _user32 as user32
    from pyglet.libs.win32 import _kernel32 as kernel32

else:  # Nasty local imports for testing on non-Win32 systems
    from ctypes import c_void_p as HANDLE
    from unittest.mock import Mock

    user32 = Mock()
    user32.GetDC = lambda a: HANDLE()
    user32.attach_callable_mock('ReleaseDC', Mock())


class DeviceContext(HANDLE):
    """
    A Win32 device context as a Python Context manager.

    This class sacrifices a tiny bit of speed to gain durability
    and readability. Performance-critical code should directly acquire
    & release win32 resources the old-fashioned way.
    """

    def __init__(self, handle: Optional[int] = None):
        super().__init__()
        self._is_ctx_manager: bool = False

        # Nasty trick: copy the handle value to this one
        self.value = self._acquire_handle(handle)

    def _acquire_handle(self, window_handle: Optional[int] = None) -> HANDLE:

        handle_dc = user32.GetDC(window_handle)
        if not handle_dc:
            raise WinError()

        return handle_dc

    def _close_handle(self) -> None:
        user32.ReleaseDC(self)

    def __enter__(self) -> HANDLE:
        self._is_ctx_manager = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._close_handle()

    def close(self) -> None:
        if self._is_ctx_manager:
            raise AttributeError(
                "Manual closing not allowed inside context manager")
