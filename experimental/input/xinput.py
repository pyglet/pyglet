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

class XInputDevice(object):
    def __init__(self, display, device_info):
        self._x_display = display._display
        self._device_id = device_info.id
        self.name = device_info.name

        self._open_device = None

        # TODO: retrieve inputclassinfo from device_info and expose / save
        # for valuator axes etc.

    def open(self):
        if self._open_device:
            return

        self._open_device = xi.XOpenDevice(self._x_display, self._device_id)
        if not self._open_device:
            raise Exception('Cannot open device')
        
    def close(self):
        if not self._open_device:
            return

        xi.XCloseDevice(self._x_display, self._open_device)

    def attach(self, window):
        assert window._x_display == self._x_display
        return XInputDeviceInstance(self, window)

class XInputDeviceInstance(pyglet.event.EventDispatcher):
    def __init__(self, device, window):
        '''Create an opened instance of a device on the given window.

        :Parameters:
            `device` : XInputDevice
                Device to open
            `window` : Window
                Window to open device on

        '''
        assert device._x_display == window._x_display
        assert device._open_device

        self.device = device
        self.window = window
        self._events = []

        try:
            dispatcher = window.__xinput_window_event_dispatcher
        except AttributeError:
            dispatcher = window.__xinput_window_event_dispatcher = \
                XInputWindowEventDispatcher()
        dispatcher.add_instance(self)

        device = device._open_device.contents
        if not device.num_classes:
            return

        # Bind matching extended window events to bound instance methods
        # on this object.
        #
        # This is inspired by test.c of xinput package by Frederic
        # Lepied available at x.org.
        #
        # In C, this stuff is normally handled by the macro DeviceKeyPress and
        # friends. Since we don't have access to those macros here, we do it
        # this way.

        for i in range(device.num_classes):
            class_info = device.classes[i]
            if class_info.input_class == xi.KeyClass:
                self._add(class_info, xi._deviceKeyPress,
                          dispatcher._event_xinput_key_press)
                self._add(class_info, xi._deviceKeyRelease,
                          dispatcher._event_xinput_key_release)

            elif class_info.input_class == xi.ButtonClass:
                self._add(class_info, xi._deviceButtonPress,
                          dispatcher._event_xinput_button_press)
                self._add(class_info, xi._deviceButtonRelease,
                          dispatcher._event_xinput_button_release)

            elif class_info.input_class == xi.ValuatorClass:
                self._add(class_info, xi._deviceMotionNotify,
                          dispatcher._event_xinput_motion)

            elif class_info.input_class == xi.ProximityClass:
                self._add(class_info, xi._proximityIn,
                          dispatcher._event_xinput_proximity_in)
                self._add(class_info, xi._proximityOut,
                          dispatcher._event_xinput_proximity_out)

            elif class_info.input_class == xi.FeedbackClass:
                pass

            elif class_info.input_class == xi.FocusClass:
                pass
                
            elif class_info.input_class == xi.OtherClass:
                pass

        array = (xi.XEventClass * len(self._events))(*self._events)
        xi.XSelectExtensionEvent(window._x_display,
                                 window._window,
                                 array,
                                 len(array))

    def _add(self, class_info, event, handler):
        _type = class_info.event_type_base + event
        _class = self.device._device_id << 8 | _type
        self._events.append(_class)
        self.window._event_handlers[_type] = handler

XInputDeviceInstance.register_event_type('on_button_press')
XInputDeviceInstance.register_event_type('on_button_release')
XInputDeviceInstance.register_event_type('on_motion')
XInputDeviceInstance.register_event_type('on_proximity_in')
XInputDeviceInstance.register_event_type('on_proximity_out')

class XInputWindowEventDispatcher(object):
    def __init__(self):
        self._instances = {}

    def add_instance(self, instance):
        self._instances[instance.device._device_id] = instance

    def remove_instance(self, instance):
        del self._instances[instance.device._device_id]

    def dispatch_instance_event(self, e, *args):
        try:
            instance = self._instances[e.deviceid]
        except KeyError:
            return

        instance.dispatch_event(*args)

    @pyglet.window.xlib.XlibEventHandler(0)
    def _event_xinput_key_press(self, ev):
        raise NotImplementedError('TODO')

    @pyglet.window.xlib.XlibEventHandler(0)
    def _event_xinput_key_release(self, ev):
        raise NotImplementedError('TODO')

    @pyglet.window.xlib.XlibEventHandler(0)
    def _event_xinput_button_press(self, ev):
        e = ctypes.cast(ctypes.byref(ev),
            ctypes.POINTER(xi.XDeviceButtonEvent)).contents

        self.dispatch_instance_event(e, 'on_button_press', e.button)

    @pyglet.window.xlib.XlibEventHandler(0)
    def _event_xinput_button_release(self, ev):
        e = ctypes.cast(ctypes.byref(ev),
            ctypes.POINTER(xi.XDeviceButtonEvent)).contents

        self.dispatch_instance_event(e, 'on_button_release', e.button)

    @pyglet.window.xlib.XlibEventHandler(0)
    def _event_xinput_motion(self, ev):
        e = ctypes.cast(ctypes.byref(ev),
            ctypes.POINTER(xi.XDeviceMotionEvent)).contents
        axis_data = []
        for i in range(e.axes_count):
            axis_data.append(e.axis_data[i])
        self.dispatch_instance_event(e, 'on_motion', axis_data, e.x, e.y)

    @pyglet.window.xlib.XlibEventHandler(0)
    def _event_xinput_proximity_in(self, ev):
        e = ctypes.cast(ctypes.byref(ev),
            ctypes.POINTER(xi.XProximityNotifyEvent)).contents
        self.dispatch_instance_event(e, 'on_proximity_in')

    @pyglet.window.xlib.XlibEventHandler(-1)
    def _event_xinput_proximity_out(self, ev):
        e = ctypes.cast(ctypes.byref(ev),
            ctypes.POINTER(xi.XProximityNotifyEvent)).contents
        self.dispatch_instance_event(e, 'on_proximity_out')

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

