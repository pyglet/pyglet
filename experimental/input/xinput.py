# ----------------------------------------------------------------------------
# Copyright (c) 2008 Andrew D. Straw and Alex Holkner
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

# Based on pygxinput originally by Andrew D. Straw
# http://code.astraw.com/projects/motmot/wiki/pygxinput

import ctypes

import pyglet
from pyglet.window.xlib import xlib

import lib_xinput as xi

class XlibWithXinputWindow(pyglet.window.xlib.XlibWindow):
    def __init__(self, *args, **kwargs):
        super(XlibWithXinputWindow, self).__init__(*args, **kwargs)

    @pyglet.window.xlib.XlibEventHandler(-1)
    def _event_xinput_key_press(self, ev):
        raise NotImplementedError('TODO')

    @pyglet.window.xlib.XlibEventHandler(-1)
    def _event_xinput_key_release(self, ev):
        raise NotImplementedError('TODO')

    @pyglet.window.xlib.XlibEventHandler(-1)
    def _event_xinput_button_press(self, ev):
        e = ctypes.cast(ctypes.byref(ev),
            ctypes.POINTER(xi.XDeviceButtonEvent)).contents

        self.dispatch_event('on_xinput_button_press', e.deviceid, e.button)

    @pyglet.window.xlib.XlibEventHandler(-1)
    def _event_xinput_button_release(self, ev):
        e = ctypes.cast(ctypes.byref(ev),
            ctypes.POINTER(xi.XDeviceButtonEvent)).contents
        self.dispatch_event('on_xinput_button_release', e.deviceid, e.button)

    @pyglet.window.xlib.XlibEventHandler(-1)
    def _event_xinput_motion(self, ev):
        e = ctypes.cast(ctypes.byref(ev),
            ctypes.POINTER(xi.XDeviceMotionEvent)).contents
        axis_data = []
        for i in range(e.axes_count):
            axis_data.append(e.axis_data[i])
        self.dispatch_event('on_xinput_motion', e.deviceid, axis_data, e.x, e.y)

    @pyglet.window.xlib.XlibEventHandler(-1)
    def _event_xinput_proximity_in(self, ev):
        e = ctypes.cast(ctypes.byref(ev),
            ctypes.POINTER(xi.XProximityNotifyEvent)).contents
        self.dispatch_event('on_xinput_proximity_in', e.deviceid)

    @pyglet.window.xlib.XlibEventHandler(-1)
    def _event_xinput_proximity_out(self, ev):
        e = ctypes.cast(ctypes.byref(ev),
            ctypes.POINTER(xi.XProximityNotifyEvent)).contents
        self.dispatch_event('on_xinput_proximity_out', e.deviceid)

XlibWithXinputWindow.register_event_type('on_xinput_button_press')
XlibWithXinputWindow.register_event_type('on_xinput_button_release')
XlibWithXinputWindow.register_event_type('on_xinput_motion')
XlibWithXinputWindow.register_event_type('on_xinput_proximity_in')
XlibWithXinputWindow.register_event_type('on_xinput_proximity_out')

class _DeviceWindowEventList(object):
    def __init__(self, window, device):
        self.window = window
        self.device = device
        self.events = []

    def add(self, class_info, event, handler):
        _type = class_info.event_type_base + event
        _class = self.device.device_id << 8 | _type
        self.events.append(_class)
        self.window._event_handlers[_type] = handler

    def select(self):
        array = (xi.XEventClass * len(self.events))(*self.events)
        xi.XSelectExtensionEvent(self.window._x_display,
                                     self.window._window,
                                     array,
                                     len(array))

class XInputDevice(object):
    def __init__(self, display, device_info):
        self._display = display
        self._device_id = device_info.id
        self.name = device_info.name

        # TODO: retrieve inputclassinfo from device_info and expose / save
        # for valuator axes etc.

    def open(self, window):
        assert window.display == self._display

        self._window = window
        self._device = xi.XOpenDevice(window._x_display, self._device_id)
        if not self._device:
            raise Exception('Cannot open device')

        device = self._device.contents
        if not device.num_classes:
            return

        # This is inspired by test.c of xinput package by Frederic
        # Lepied available at x.org.

        # In C, this stuff is normally handled by the macro DeviceKeyPress and
        # friends. Since we don't have access to those macros here, we do it
        # this way.

        events = _DeviceWindowEventList(window, device)
        for i in range(device.num_classes):
            class_info = device.classes[i]
            if class_info.input_class == xi.KeyClass:
                events.add(class_info, xi._deviceKeyPress,
                           window._event_xinput_key_press)
                events.add(class_info, xi._deviceKeyRelease,
                           window._event_xinput_key_release)

            elif class_info.input_class == xi.ButtonClass:
                events.add(class_info, xi._deviceButtonPress,
                           window._event_xinput_button_press)
                events.add(class_info, xi._deviceButtonRelease,
                           window._event_xinput_button_release)

            elif class_info.input_class == xi.ValuatorClass:
                events.add(class_info, xi._deviceMotionNotify,
                           window._event_xinput_motion)

            elif class_info.input_class == xi.ProximityClass:
                events.add(class_info, xi._proximityIn,
                           window._event_xinput_proximity_in)
                events.add(class_info, xi._proximityOut,
                           window._event_xinput_proximity_out)

            elif class_info.input_class == xi.FeedbackClass:
                pass

            elif class_info.input_class == xi.FocusClass:
                pass
                
            elif class_info.input_class == xi.OtherClass:
                pass

        events.select()

def _check_extension(display):
    major_opcode = ctypes.c_int()
    first_event = ctypes.c_int()
    first_error = ctypes.c_int()
    xlib.XQueryExtension(display._display, 'XInputExtension', 
        ctypes.byref(major_opcode), 
        ctypes.byref(first_event),
        ctypes.byref(first_error))
    if not major_opcode.value:
        raise Exception('XInput extension not available')

def get_devices(display):
    _check_extension(display)

    devices = []
    count = ctypes.c_int(0)
    device_list = xi.XListInputDevices(display._display, count)

    for i in range(count.value):
        device_info = device_list[i]
        devices.append(XInputDevice(display, device_info))

    return devices

