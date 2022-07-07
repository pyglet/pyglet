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

import os
import time
import fcntl
import ctypes

from ctypes import c_uint16 as _u16
from ctypes import c_int16 as _s16
from ctypes import c_uint32 as _u32
from ctypes import c_int32 as _s32
from ctypes import c_int64 as _s64
from concurrent.futures import ThreadPoolExecutor

from typing import List

import pyglet

from pyglet.app.xlib import XlibSelectDevice
from .base import Device, RelativeAxis, AbsoluteAxis, Button, Joystick, Controller
from .base import DeviceOpenException, ControllerManager
from .evdev_constants import *
from .controller import get_mapping, Relation

_IOC_NRBITS = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14
_IOC_DIRBITS = 2

_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = (_IOC_NRSHIFT + _IOC_NRBITS)
_IOC_SIZESHIFT = (_IOC_TYPESHIFT + _IOC_TYPEBITS)
_IOC_DIRSHIFT = (_IOC_SIZESHIFT + _IOC_SIZEBITS)

_IOC_NONE = 0
_IOC_WRITE = 1
_IOC_READ = 2


def _IOC(dir, type, nr, size):
    return ((dir << _IOC_DIRSHIFT) |
            (type << _IOC_TYPESHIFT) |
            (nr << _IOC_NRSHIFT) |
            (size << _IOC_SIZESHIFT))


def _IOR(type, nr, struct):
    request = _IOC(_IOC_READ, ord(type), nr, ctypes.sizeof(struct))

    def f(fileno):
        buffer = struct()
        fcntl.ioctl(fileno, request, buffer)
        return buffer

    return f


def _IOR_len(type, nr):
    def f(fileno, buffer):
        request = _IOC(_IOC_READ, ord(type), nr, ctypes.sizeof(buffer))
        fcntl.ioctl(fileno, request, buffer)
        return buffer

    return f


def _IOR_str(type, nr):
    g = _IOR_len(type, nr)

    def f(fileno, length=256):
        return g(fileno, ctypes.create_string_buffer(length)).value

    return f


def _IOW(type, nr):

    def f(fileno, buffer):
        request = _IOC(_IOC_WRITE, ord(type), nr, ctypes.sizeof(buffer))
        fcntl.ioctl(fileno, request, buffer)

    return f


# Structures from /linux/blob/master/include/uapi/linux/input.h

class Timeval(ctypes.Structure):
    _fields_ = (
        ('tv_sec', _s64),
        ('tv_usec', _s64)
    )


class InputEvent(ctypes.Structure):
    _fields_ = (
        ('time', Timeval),
        ('type', _u16),
        ('code', _u16),
        ('value', _s32)
    )


class InputID(ctypes.Structure):
    _fields_ = (
        ('bustype', _u16),
        ('vendor', _u16),
        ('product', _u16),
        ('version', _u16),
    )


class InputABSInfo(ctypes.Structure):
    _fields_ = (
        ('value', _s32),
        ('minimum', _s32),
        ('maximum', _s32),
        ('fuzz', _s32),
        ('flat', _s32),
    )


class FFReplay(ctypes.Structure):
    _fields_ = (
        ('length', _u16),
        ('delay', _u16)
    )


class FFTrigger(ctypes.Structure):
    _fields_ = (
        ('button', _u16),
        ('interval', _u16)
    )


class FFEnvelope(ctypes.Structure):
    _fields_ = [
        ('attack_length', _u16),
        ('attack_level', _u16),
        ('fade_length', _u16),
        ('fade_level', _u16),
    ]


class FFConstantEffect(ctypes.Structure):
    _fields_ = [
        ('level', _s16),
        ('ff_envelope', FFEnvelope),
    ]


class FFRampEffect(ctypes.Structure):
    _fields_ = [
        ('start_level', _s16),
        ('end_level', _s16),
        ('ff_envelope', FFEnvelope),
    ]


class FFConditionEffect(ctypes.Structure):
    _fields_ = [
        ('right_saturation', _u16),
        ('left_saturation', _u16),
        ('right_coeff', _s16),
        ('left_coeff', _s16),
        ('deadband', _u16),
        ('center', _s16),
    ]


class FFPeriodicEffect(ctypes.Structure):
    _fields_ = [
        ('waveform', _u16),
        ('period', _u16),
        ('magnitude', _s16),
        ('offset', _s16),
        ('phase', _u16),
        ('envelope', FFEnvelope),
        ('custom_len', _u32),
        ('custom_data', ctypes.POINTER(_s16)),
    ]


class FFRumbleEffect(ctypes.Structure):
    _fields_ = (
        ('strong_magnitude', _u16),
        ('weak_magnitude', _u16)
    )


class FFEffectType(ctypes.Union):
    _fields_ = (
        ('ff_constant_effect', FFConstantEffect),
        ('ff_ramp_effect', FFRampEffect),
        ('ff_periodic_effect', FFPeriodicEffect),
        ('ff_condition_effect', FFConditionEffect * 2),
        ('ff_rumble_effect', FFRumbleEffect),
    )


class FFEvent(ctypes.Structure):
    _fields_ = (
        ('type', _u16),
        ('id', _s16),
        ('direction', _u16),
        ('ff_trigger', FFTrigger),
        ('ff_replay', FFReplay),
        ('u', FFEffectType)
    )


EVIOCGVERSION = _IOR('E', 0x01, ctypes.c_int)
EVIOCGID = _IOR('E', 0x02, InputID)
EVIOCGNAME = _IOR_str('E', 0x06)
EVIOCGPHYS = _IOR_str('E', 0x07)
EVIOCGUNIQ = _IOR_str('E', 0x08)
EVIOCSFF = _IOW('E', 0x80)


def EVIOCGBIT(fileno, ev, buffer):
    return _IOR_len('E', 0x20 + ev)(fileno, buffer)


def EVIOCGABS(fileno, abs):
    buffer = InputABSInfo()
    return _IOR_len('E', 0x40 + abs)(fileno, buffer)


def get_set_bits(bytestring):
    bits = set()
    j = 0
    for byte in bytestring:
        for i in range(8):
            if byte & 1:
                bits.add(j + i)
            byte >>= 1
        j += 8
    return bits


_abs_names = {
    ABS_X: AbsoluteAxis.X,
    ABS_Y: AbsoluteAxis.Y,
    ABS_Z: AbsoluteAxis.Z,
    ABS_RX: AbsoluteAxis.RX,
    ABS_RY: AbsoluteAxis.RY,
    ABS_RZ: AbsoluteAxis.RZ,
    ABS_HAT0X: AbsoluteAxis.HAT_X,
    ABS_HAT0Y: AbsoluteAxis.HAT_Y,
}

_rel_names = {
    REL_X: RelativeAxis.X,
    REL_Y: RelativeAxis.Y,
    REL_Z: RelativeAxis.Z,
    REL_RX: RelativeAxis.RX,
    REL_RY: RelativeAxis.RY,
    REL_RZ: RelativeAxis.RZ,
    REL_WHEEL: RelativeAxis.WHEEL,
}


def _create_control(fileno, event_type, event_code):
    if event_type == EV_ABS:
        raw_name = abs_raw_names.get(event_code, 'EV_ABS(%x)' % event_code)
        name = _abs_names.get(event_code)
        absinfo = EVIOCGABS(fileno, event_code)
        value = absinfo.value
        minimum = absinfo.minimum
        maximum = absinfo.maximum
        control = AbsoluteAxis(name, minimum, maximum, raw_name)
        control.value = value
        if name == 'hat_y':
            control.inverted = True
    elif event_type == EV_REL:
        raw_name = rel_raw_names.get(event_code, 'EV_REL(%x)' % event_code)
        name = _rel_names.get(event_code)
        # TODO min/max?
        control = RelativeAxis(name, raw_name)
    elif event_type == EV_KEY:
        raw_name = key_raw_names.get(event_code, 'EV_KEY(%x)' % event_code)
        name = None
        control = Button(name, raw_name)
    else:
        value = minimum = maximum = 0  # TODO
        return None
    control._event_type = event_type
    control._event_code = event_code
    return control


event_types = {
    EV_KEY: KEY_MAX,
    EV_REL: REL_MAX,
    EV_ABS: ABS_MAX,
    EV_MSC: MSC_MAX,
    EV_LED: LED_MAX,
    EV_SND: SND_MAX,
    EV_FF: FF_MAX,
}


class EvdevDevice(XlibSelectDevice, Device):
    _fileno = None

    def __init__(self, display, filename):
        self._filename = filename

        fileno = os.open(filename, os.O_RDONLY)
        # event_version = EVIOCGVERSION(fileno).value

        self._id = EVIOCGID(fileno)
        self.id_bustype = self._id.bustype
        self.id_vendor = hex(self._id.vendor)
        self.id_product = hex(self._id.product)
        self.id_version = self._id.version

        name = EVIOCGNAME(fileno)
        try:
            name = name.decode('utf-8')
        except UnicodeDecodeError:
            try:
                name = name.decode('latin-1')
            except UnicodeDecodeError:
                pass

        try:
            self.phys = EVIOCGPHYS(fileno)
        except OSError:
            self.phys = ''
        try:
            self.uniq = EVIOCGUNIQ(fileno)
        except OSError:
            self.uniq = ''

        self.controls = []
        self.control_map = {}
        self.ff_types = []

        event_types_bits = (ctypes.c_byte * 4)()
        EVIOCGBIT(fileno, 0, event_types_bits)
        for event_type in get_set_bits(event_types_bits):
            if event_type not in event_types:
                continue
            max_code = event_types[event_type]
            nbytes = max_code // 8 + 1
            event_codes_bits = (ctypes.c_byte * nbytes)()
            EVIOCGBIT(fileno, event_type, event_codes_bits)
            if event_type == EV_FF:
                self.ff_types.extend(get_set_bits(event_codes_bits))
            else:
                for event_code in get_set_bits(event_codes_bits):
                    control = _create_control(fileno, event_type, event_code)
                    if control:
                        self.control_map[(event_type, event_code)] = control
                        self.controls.append(control)

        self.controls.sort(key=lambda c: c._event_code)
        os.close(fileno)

        super().__init__(display, name)

    def get_guid(self):
        """Generate an SDL2 style GUID from the device ID"""
        hex_bustype = format(self._id.bustype & 0xFF, '02x')
        hex_vendor = format(self._id.vendor & 0xFF, '02x')
        hex_product = format(self._id.product & 0xFF, '02x')
        hex_version = format(self._id.version & 0xFF, '02x')
        shifted_bustype = format(self._id.bustype >> 8, '02x')
        shifted_vendor = format(self._id.vendor >> 8, '02x')
        shifted_product = format(self._id.product >> 8, '02x')
        shifted_version = format(self._id.version >> 8, '02x')
        slug = "{:0>2}{:0>2}0000{:0>2}{:0>2}0000{:0>2}{:0>2}0000{:0>2}{:0>2}0000"
        return slug.format(hex_bustype, shifted_bustype, hex_vendor, shifted_vendor,
                           hex_product, shifted_product, hex_version, shifted_version)

    def open(self, window=None, exclusive=False):
        super().open(window, exclusive)

        try:
            self._fileno = os.open(self._filename, os.O_RDWR | os.O_NONBLOCK)
        except OSError as e:
            raise DeviceOpenException(e)

        pyglet.app.platform_event_loop.select_devices.add(self)

    def close(self):
        super().close()

        if not self._fileno:
            return

        pyglet.app.platform_event_loop.select_devices.remove(self)
        os.close(self._fileno)
        self._fileno = None

    def get_controls(self):
        return self.controls

    # Force Feedback methods

    def ff_upload_effect(self, structure):
        os.write(self._fileno, structure)

    # XlibSelectDevice interface

    def fileno(self):
        return self._fileno

    def poll(self):
        return False

    def select(self):
        if not self._fileno:
            return

        try:
            events = (InputEvent * 64)()
            bytes_read = os.readv(self._fileno, events)
        except OSError:
            self.close()
            return

        n_events = bytes_read // ctypes.sizeof(InputEvent)
        for event in events[:n_events]:
            try:
                control = self.control_map[(event.type, event.code)]
                control.value = event.value
            except KeyError:
                pass


class FFController(Controller):
    """Controller that supports force-feedback"""
    _fileno = None
    _weak_effect = None
    _play_weak_event = None
    _stop_weak_event = None
    _strong_effect = None
    _play_strong_event = None
    _stop_strong_event = None

    def open(self, window=None, exclusive=False):
        super().open(window, exclusive)
        self._fileno = self.device.fileno()
        # Create Force Feedback effects & events when opened:
        # https://www.kernel.org/doc/html/latest/input/ff.html
        self._weak_effect = FFEvent(FF_RUMBLE, -1)
        EVIOCSFF(self._fileno, self._weak_effect)
        self._play_weak_event = InputEvent(Timeval(), EV_FF, self._weak_effect.id, 1)
        self._stop_weak_event = InputEvent(Timeval(), EV_FF, self._weak_effect.id, 0)

        self._strong_effect = FFEvent(FF_RUMBLE, -1)
        EVIOCSFF(self._fileno, self._strong_effect)
        self._play_strong_event = InputEvent(Timeval(), EV_FF, self._strong_effect.id, 1)
        self._stop_strong_event = InputEvent(Timeval(), EV_FF, self._strong_effect.id, 0)

    def rumble_play_weak(self, strength=1.0, duration=0.5):
        effect = self._weak_effect
        effect.u.ff_rumble_effect.weak_magnitude = int(max(min(1.0, strength), 0) * 0xFFFF)
        effect.ff_replay.length = int(duration * 1000)
        EVIOCSFF(self._fileno, effect)
        self.device.ff_upload_effect(self._play_weak_event)

    def rumble_play_strong(self, strength=1.0, duration=0.5):
        effect = self._strong_effect
        effect.u.ff_rumble_effect.strong_magnitude = int(max(min(1.0, strength), 0) * 0xFFFF)
        effect.ff_replay.length = int(duration * 1000)
        EVIOCSFF(self._fileno, effect)
        self.device.ff_upload_effect(self._play_strong_event)

    def rumble_stop_weak(self):
        self.device.ff_upload_effect(self._stop_weak_event)

    def rumble_stop_strong(self):
        self.device.ff_upload_effect(self._stop_strong_event)


class EvdevControllerManager(ControllerManager, XlibSelectDevice):

    def __init__(self, display=None):
        super().__init__()
        self._display = display
        self._devices_file = open('/proc/bus/input/devices')
        self._device_names = self._get_device_names()
        self._controllers = {}
        self._thread_pool = ThreadPoolExecutor(max_workers=1)

        for name in self._device_names:
            path = os.path.join('/dev/input', name)
            try:
                device = EvdevDevice(self._display, path)
            except OSError:
                continue
            controller = _create_controller(device)
            if controller:
                self._controllers[name] = controller

        pyglet.app.platform_event_loop.select_devices.add(self)

    def __del__(self):
        self._devices_file.close()

    def fileno(self):
        """Allow this class to be Selectable"""
        return self._devices_file.fileno()

    @staticmethod
    def _get_device_names():
        return {name for name in os.listdir('/dev/input') if name.startswith('event')}

    def _make_device_callback(self, future):
        name, device = future.result()
        if not device:
            return

        if name in self._controllers:
            controller = self._controllers.get(name)
        else:
            controller = _create_controller(device)
            self._controllers[name] = controller

        if controller:
            # Dispatch event in main thread:
            pyglet.app.platform_event_loop.post_event(self, 'on_connect', controller)

    def _make_device(self, name, count=1):
        path = os.path.join('/dev/input', name)
        while count > 0:
            try:
                return name, EvdevDevice(self._display, path)
            except OSError:
                if count > 0:
                    time.sleep(0.1)
                count -= 1
        return None, None

    def select(self):
        """Triggered whenever the devices_file changes."""
        new_device_files = self._get_device_names()
        appeared = new_device_files - self._device_names
        disappeared = self._device_names - new_device_files
        self._device_names = new_device_files

        for name in appeared:
            future = self._thread_pool.submit(self._make_device, name, count=10)
            future.add_done_callback(self._make_device_callback)

        for name in disappeared:
            controller = self._controllers.get(name)
            if controller:
                self.dispatch_event('on_disconnect', controller)

    def get_controllers(self) -> List[Controller]:
        return list(self._controllers.values())


def get_devices(display=None):
    _devices = {}
    base = '/dev/input'
    for filename in os.listdir(base):
        if filename.startswith('event'):
            path = os.path.join(base, filename)
            if path in _devices:
                continue

            try:
                _devices[path] = EvdevDevice(display, path)
            except OSError:
                pass

    return list(_devices.values())


def _create_joystick(device):
    # Look for something with an ABS X and ABS Y axis, and a joystick 0 button
    have_x = False
    have_y = False
    have_button = False
    for control in device.controls:
        if control._event_type == EV_ABS and control._event_code == ABS_X:
            have_x = True
        elif control._event_type == EV_ABS and control._event_code == ABS_Y:
            have_y = True
        elif control._event_type == EV_KEY and control._event_code in (BTN_JOYSTICK, BTN_GAMEPAD):
            have_button = True
    if not (have_x and have_y and have_button):
        return

    return Joystick(device)


def get_joysticks(display=None):
    return [joystick for joystick in
            [_create_joystick(device) for device in get_devices(display)]
            if joystick is not None]


def _detect_controller_mapping(device):
    # If no explicit mapping is available, we can
    # detect it from the Linux gamepad specification:
    # https://www.kernel.org/doc/html/v4.13/input/gamepad.html
    # Note: legacy device drivers don't always adhere to this.
    mapping = dict(guid=device.get_guid(), name=device.name)

    _aliases = {BTN_MODE: 'guide', BTN_SELECT: 'back', BTN_START: 'start',
                BTN_SOUTH: 'a', BTN_EAST: 'b', BTN_WEST: 'x', BTN_NORTH: 'y',
                BTN_TL: 'leftshoulder', BTN_TR: 'rightshoulder',
                BTN_TL2: 'lefttrigger', BTN_TR2: 'righttrigger',
                BTN_THUMBL: 'leftstick', BTN_THUMBR: 'rightstick',
                BTN_DPAD_UP: 'dpup', BTN_DPAD_DOWN: 'dpdown',
                BTN_DPAD_LEFT: 'dpleft', BTN_DPAD_RIGHT: 'dpright',

                ABS_HAT0X: 'dpleft',  # 'dpright',
                ABS_HAT0Y: 'dpup',    # 'dpdown',
                ABS_Z: 'lefttrigger', ABS_RZ: 'righttrigger',
                ABS_X: 'leftx', ABS_Y: 'lefty', ABS_RX: 'rightx', ABS_RY: 'righty'}

    button_controls = [control for control in device.controls if isinstance(control, Button)]
    axis_controls = [control for control in device.controls if isinstance(control, AbsoluteAxis)]
    hat_controls = [control for control in device.controls if control.name in ('hat_x', 'hat_y')]

    for i, control in enumerate(button_controls):
        name = _aliases.get(control._event_code)
        if name:
            mapping[name] = Relation('button', i)

    for i, control in enumerate(axis_controls):
        name = _aliases.get(control._event_code)
        if name:
            mapping[name] = Relation('axis', i)

    for i, control in enumerate(hat_controls):
        name = _aliases.get(control._event_code)
        if name:
            index = 1 + i << 1
            mapping[name] = Relation('hat0', index)

    return mapping


def _create_controller(device):
    for control in device.controls:
        if control._event_type == EV_KEY and control._event_code == BTN_GAMEPAD:
            break
    else:
        return None     # Game Controllers must have a BTN_GAMEPAD

    mapping = get_mapping(device.get_guid())
    if not mapping:
        mapping = _detect_controller_mapping(device)

    if FF_RUMBLE in device.ff_types:
        return FFController(device, mapping)
    else:
        return Controller(device, mapping)


def get_controllers(display=None):
    return [controller for controller in
            [_create_controller(device) for device in get_devices(display)]
            if controller is not None]
