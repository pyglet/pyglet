"""Joystick, Game Controller, Tablet and USB HID device support.

This module provides a unified interface to almost any input device, besides
the regular mouse and keyboard support provided by
:py:class:`~pyglet.window.Window`.  At the lowest
level, :py:func:`get_devices` can be used to retrieve a list of all supported
devices, including joysticks, tablets, game controllers, wheels, pedals, remote
controls, keyboards and mice.  The set of returned devices varies greatly
depending on the operating system (and, of course, what's plugged in).  

At this level pyglet does not try to interpret *what* a particular device is,
merely what controls it provides.  A :py:class:`Control` can be either a button,
whose value is either ``True`` or ``False``, or a relative or absolute-valued
axis, whose value is a float.  Sometimes the name of a control can be provided
(for example, ``x``, representing the horizontal axis of a joystick), but often
not.  In these cases the device API may still be useful -- the user will have
to be asked to press each button in turn or move each axis separately to
identify them.

Higher-level interfaces are provided for joysticks, game controllers, tablets
and the Apple remote control. These devices can usually be identified by pyglet
positively, and a base level of functionality for each one provided through a
common interface.

To use an input device:

1. Call :py:func:`get_devices`, :py:func:`get_apple_remote`,
   :py:func:`get_controllers` or :py:func:`get_joysticks` to retrieve and
   identify the device.
2. For low-level devices (retrieved by :py:func:`get_devices`), query the
   devices list of controls and determine which ones you are interested in. For
   high-level interfaces the set of controls is provided by the interface.
3. Optionally attach event handlers to controls on the device. For high-level
   interfaces, additional events are available.
4. Call :py:meth:`Device.open` to begin receiving events on the device.  You can
   begin querying the control values after this time; they will be updated
   asynchronously.
5. Call :py:meth:`Device.close` when you are finished with the device (not
   needed if your application quits at this time).

To use a tablet, follow the procedure above using :py:func:`get_tablets`, but
note that no control list is available; instead, calling :py:meth:`Tablet.open`
returns a :py:class:`TabletCanvas` onto which you should set your event
handlers.

For game controllers, the :py:class:`ControllerManager` is available. This
provides a convenient way to handle hot-plugging of controllers.

.. versionadded:: 1.2

"""
from __future__ import annotations

import sys

from typing import TYPE_CHECKING

from .base import Device, Control, RelativeAxis, AbsoluteAxis, ControllerManager
from .base import Button, Joystick, AppleRemote, Tablet, Controller
from .base import DeviceException, DeviceOpenException, DeviceExclusiveException

if TYPE_CHECKING:
    from pyglet.display import Display

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run


def get_apple_remote(display: Display | None = None) -> AppleRemote | None:
    """Get the Apple remote control device, if it exists.

    The Apple remote is the small white 6-button remote control that
    accompanies most recent Apple desktops and laptops.  The remote can only
    be used with Mac OS X.

    Args:
        display:
            Currently ignored.
    """
    return None


if _is_pyglet_doc_run:
    def get_devices(display: Display | None = None) -> list[Device]:
        """Get a list of all attached input devices.

        Args:
            display:
                The display device to query for input devices.  Ignored on Mac
                OS X and Windows.  On Linux, defaults to the default display device.
        """


    def get_joysticks(display: Display | None = None) -> list[Joystick]:
        """Get a list of attached joysticks.

        Args:
            display:
                The display device to query for input devices.  Ignored on Mac
                OS X and Windows.  On Linux, defaults to the default display device.
        """


    def get_controllers(display: Display | None = None) -> list[Controller]:
        """Get a list of attached controllers.

        Args:
            display:
                The display device to query for input devices.  Ignored on Mac
                OS X and Windows.  On Linux, defaults to the default display device.
        """

    def get_tablets(display: Display | None = None) -> list[Tablet]:
        """Get a list of tablets.

        This function may return a valid tablet device even if one is not
        attached (for example, it is not possible on Mac OS X to determine if
        a tablet device is connected).  Despite returning a list of tablets,
        pyglet does not currently support multiple tablets, and the behaviour
        is undefined if more than one is attached.

        Args:
            display:
                The display device to query for input devices.  Ignored on Mac
                OS X and Windows.  On Linux, defaults to the default display device.
        """

else:

    from pyglet import compat_platform

    if compat_platform.startswith('linux'):
        from .linux import get_devices
        from .linux import get_joysticks
        from .linux import get_controllers
        from .linux import get_tablets
        from .linux import ControllerManager

    elif compat_platform in ('cygwin', 'win32'):
        from .win32 import get_devices
        from .win32 import get_joysticks
        from .win32 import get_controllers
        from .win32 import get_tablets
        from .win32 import Win32ControllerManager as ControllerManager

    elif compat_platform == 'darwin':
        from .macos import get_devices
        from .macos import get_joysticks
        from .macos import get_apple_remote
        from .macos import get_controllers
        from .macos import get_tablets
        from .macos import ControllerManager

__all__ = [
    'get_devices',
    'get_joysticks',
    'get_controllers',
    'get_tablets',
    'get_apple_remote',
    'ControllerManager',
    'Device',
    'Control',
    'RelativeAxis',
    'AbsoluteAxis',
    'Button',
    'Joystick',
    'AppleRemote',
    'Tablet',
    'Controller',
    'DeviceException',
    'DeviceOpenException',
    'DeviceExclusiveException',
]
