"""Work in progress HIDRAW device abstraction for Linux"""

import os
import fcntl
import ctypes
import warnings

from ctypes import c_int as _int
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
from pyglet.input.base import Device, RelativeAxis, AbsoluteAxis, Button, Joystick, Controller
from pyglet.input.base import DeviceOpenException, ControllerManager
from pyglet.input.linux.evdev_constants import *
from pyglet.input.controller import get_mapping, Relation, create_guid

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

    def f(fileno, buffer=None):
        buffer = buffer or struct()
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


def _IORW(type, nr):
    def f(fileno, buffer):
        request = _IOC(_IOC_READ | _IOC_WRITE, ord(type), nr, ctypes.sizeof(buffer))
        fcntl.ioctl(fileno, request, buffer)
        return buffer

    return f


# From /linux/blob/master/include/uapi/linux/hidraw.h


class HIDRawDevInfo(ctypes.Structure):
    _fields_ = (
        ('bustype', _u32),
        ('vendor', _s16),
        ('product', _s16),
    )

    def __repr__(self):
        return f"Info(bustype={self.bustype}, vendor={hex(self.vendor)}, product={hex(self.product)})"


class HIDRawReportDescriptor(ctypes.Structure):
    _fields_ = (
        ('size', _u32),
        ('values', _u8 * 4096)
    )


HIDIOCGRDESCSIZE = _IOR('H', 0x01, _int)
HIDIOCGRDESC = _IOR('H', 0x02, HIDRawReportDescriptor)
HIDIOCGRAWINFO = _IOR('H', 0x03, HIDRawDevInfo)
HIDIOCGRAWNAME = _IOR_str('H', 0x04)
HIDIOCGRAWPHYS = _IOR_str('H', 0x05)
HIDIOCSFEATURE = _IORW('H', 0x06)
HIDIOCGFEATURE = _IORW('H', 0x07)
HIDIOCGRAWUNIQ = _IOR_str('H', 0x08)
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

        # Query the descriptor size:
        desc_size = HIDIOCGRDESCSIZE(fileno).value
        # Query the descriptor, and save the raw bytes:
        _report_descriptor = HIDIOCGRDESC(fileno, HIDRawReportDescriptor(size=desc_size))
        self.report_descriptor = bytes(_report_descriptor.values[:desc_size])

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
