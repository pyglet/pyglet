# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2022 pyglet contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

"""Joystick, Game Controller, Tablet and USB HID device support.

This module provides a unified interface to almost any input device, besides
the regular mouse and keyboard support provided by
:py:class:`~pyglet.window.Window`.  At the lowest
level, :py:func:`get_devices` can be used to retrieve a list of all supported
devices, including joysticks, tablets, space controllers, wheels, pedals, remote
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

import sys

from .base import Device, Control, RelativeAxis, AbsoluteAxis, ControllerManager
from .base import Button, Joystick, AppleRemote, Tablet, Controller
from .base import DeviceException, DeviceOpenException, DeviceExclusiveException


_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run


def get_apple_remote(display=None):
    """Get the Apple remote control device.

    The Apple remote is the small white 6-button remote control that
    accompanies most recent Apple desktops and laptops.  The remote can only
    be used with Mac OS X.

    :Parameters:
        display : `~pyglet.canvas.Display`
            Currently ignored.

    :rtype: AppleRemote
    :return: The remote device, or `None` if the computer does not support it.
    """
    return None


if _is_pyglet_doc_run:
    def get_devices(display=None):
        """Get a list of all attached input devices.

        :Parameters:
            display : `~pyglet.canvas.Display`
                The display device to query for input devices.  Ignored on Mac
                OS X and Windows.  On Linux, defaults to the default display
                device.

        :rtype: list of :py:class:`Device`
        """

    def get_joysticks(display=None):
        """Get a list of attached joysticks.

        :Parameters:
            display : `~pyglet.canvas.Display`
                The display device to query for input devices.  Ignored on Mac
                OS X and Windows.  On Linux, defaults to the default display
                device.

        :rtype: list of :py:class:`Joystick`
        """

    def get_controllers(display=None):
        """Get a list of attached controllers.

        :Parameters:
            display : `~pyglet.canvas.Display`
                The display device to query for input devices.  Ignored on Mac
                OS X and Windows.  On Linux, defaults to the default display
                device.

        :rtype: list of :py:class:`Controller`
        """

    def get_tablets(display=None):
        """Get a list of tablets.

        This function may return a valid tablet device even if one is not
        attached (for example, it is not possible on Mac OS X to determine if
        a tablet device is connected).  Despite returning a list of tablets,
        pyglet does not currently support multiple tablets, and the behaviour
        is undefined if more than one is attached.

        :Parameters:
            display : `~pyglet.canvas.Display`
                The display device to query for input devices.  Ignored on Mac
                OS X and Windows.  On Linux, defaults to the default display
                device.

        :rtype: list of :py:class:`Tablet`
        """

else:
    def get_tablets(display=None):
        return []

    from pyglet import compat_platform, options

    if compat_platform.startswith('linux'):
        from .x11_xinput_tablet import get_tablets
        from .x11_xinput import get_devices as x11xinput_get_devices
        from .evdev import get_devices as evdev_get_devices
        from .evdev import get_joysticks
        from .evdev import get_controllers
        from .evdev import EvdevControllerManager as ControllerManager

        def get_devices(display=None):
            return evdev_get_devices(display) + x11xinput_get_devices(display)

    elif compat_platform in ('cygwin', 'win32'):
        from .directinput import get_devices as dinput_get_devices
        from .directinput import get_controllers as dinput_get_controllers
        from .directinput import get_joysticks
        try:
            from .wintab import get_tablets
        except:
            pass
        if options["xinput_controllers"] is False:
            get_devices = dinput_get_devices
            get_controllers = dinput_get_controllers
        else:
            from .xinput import get_devices as xinput_get_devices
            from .xinput import get_controllers as xinput_get_controllers
            from .xinput import XInputControllerManager as ControllerManager

            def get_devices(display=None):
                return xinput_get_devices() + dinput_get_devices(display)

            def get_controllers(display=None):
                return xinput_get_controllers() + dinput_get_controllers(display)

    elif compat_platform == 'darwin':
        from .darwin_hid import get_devices
        from .darwin_hid import get_joysticks
        from .darwin_hid import get_apple_remote
        from .darwin_hid import get_controllers
        from .darwin_hid import DarwinControllerManager as ControllerManager
