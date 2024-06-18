"""Work in progress HIDRAW device abstraction for Linux"""

import os
import fcntl
import ctypes
import warnings

from ctypes import c_int as _int
from ctypes import c_uint as _uint
from ctypes import c_uint8 as _u8
from ctypes import c_uint16 as _u16
from ctypes import c_int16 as _s16
from ctypes import c_uint32 as _u32
from ctypes import c_int32 as _s32
from ctypes import c_int64 as _s64
from ctypes import create_string_buffer

from concurrent.futures import ThreadPoolExecutor

import pyglet

from pyglet.app.xlib import XlibSelectDevice
from pyglet.libs.ioctl import _IOR, _IOR_str, _IOWR_len
from pyglet.input.base import Device, RelativeAxis, AbsoluteAxis, Button, Joystick, Controller
from pyglet.input.base import DeviceOpenException, ControllerManager
from pyglet.input.linux.evdev_constants import *
from pyglet.input.controller import get_mapping, Relation, create_guid


# From /linux/blob/master/include/uapi/linux/hidraw.h


class HIDRawDevInfo(ctypes.Structure):
    _fields_ = (('bustype', _u32),
                ('vendor', _s16),
                ('product', _s16))

    def __repr__(self):
        return f"Info(bustype={self.bustype}, vendor={hex(self.vendor)}, product={hex(self.product)})"


class HIDRawReportDescriptor(ctypes.Structure):
    _fields_ = (('size', _u32),
                ('values', _u8 * 4096))

    def __bytes__(self):
        return bytes(self.values)[:self.size]


HIDIOCGRDESCSIZE = _IOR('H', 0x01, _uint)
HIDIOCGRAWINFO = _IOR('H', 0x03, HIDRawDevInfo)
HIDIOCGRAWNAME = _IOR_str('H', 0x04)
HIDIOCGRAWPHYS = _IOR_str('H', 0x05)
HIDIOCGRAWUNIQ = _IOR_str('H', 0x08)


def HIDIOCGRDESC(fileno, size):
    return _IOR('H', 0x02, HIDRawReportDescriptor)(fileno, size)


def HIDIOCSFEATURE(fileno, buffer):
    return _IOWR_len('H', 0x06)(fileno, buffer)


def HIDIOCGFEATURE(fileno, buffer):
    return _IOWR_len('H', 0x07)(fileno, buffer)


# HIDRAW_FIRST_MINOR = 0
# HIDRAW_MAX_DEVICES = 64
# HIDRAW_BUFFER_SIZE = 64


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


class HIDRawDevice(XlibSelectDevice, Device):
    _fileno = None

    def __init__(self, display, filename):
        self._filename = filename

        fileno = os.open(filename, os.O_RDWR | os.O_NONBLOCK)

        self.info = HIDIOCGRAWINFO(fileno)
        self.bus_type = {BUS_USB: 'usb', BUS_BLUETOOTH: 'bluetooth'}.get(self.info.bustype)
        self.phys = HIDIOCGRAWPHYS(fileno).decode('utf-8')
        self.uniq = HIDIOCGRAWUNIQ(fileno).decode('utf-8')
        name = HIDIOCGRAWNAME(fileno).decode('utf-8')

        # Query the descriptor size, and pass it as an argument.
        desc_size = HIDIOCGRDESCSIZE(fileno)
        self.report_descriptor = HIDIOCGRDESC(fileno, desc_size)

        self.controls = []
        self.control_map = {}

        os.close(fileno)
        super().__init__(display, name)

    def get_feature_report(self, number=0x00, length=256) -> bytes:
        # Make a buffer, and set the first byte to the report number:
        buffer = create_string_buffer(length + 1)
        buffer[0] = number

        HIDIOCGFEATURE(self._fileno, buffer=buffer)

        return buffer.raw

    # TODO: HIDRaw version
    # def get_guid(self):
    #     """Get the device's SDL2 style GUID string"""
    #     _id = self._id
    #     return create_guid(_id.bustype, _id.vendor, _id.product, _id.version, self.name, 0, 0)

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

    # def ff_upload_effect(self, structure):
    #     os.write(self._fileno, structure)

    # XlibSelectDevice interface

    def fileno(self):
        return self._fileno

    def poll(self):
        return False

    def select(self):
        if not self._fileno:
            return

        try:
            # TODO:  Read HID reports here
            pass
        except OSError:
            self.close()
            return


def get_devices(display=None):
    _devices = {}
    base = '/dev'
    for filename in os.listdir(base):
        if filename.startswith('hidraw'):
            path = os.path.join(base, filename)
            try:
                _devices[path] = HIDRawDevice(display, path)
            except OSError:
                continue

    return list(_devices.values())
