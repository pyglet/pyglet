"""Factory functions to provide equivalent functionality as the Linux ioctl macros.

Ioctl macros are commonly used on Linux for interacting with character (char)
files. This module provides factory functions that create custom helper functions
to perform these same types of operations.

In pyglet, the input/evdev backend uses these functions for interacting with input
devices. For example, the helper functions are first defined::

    # Create a function for reading a HID descriptor size:
    HIDIOCGRDESCSIZE = _IOR(code='H', nr=0x01, struct=ctypes.c_uint)

    # Create a function for writing Force Feedback data:
    EVIOCSFF = _IOW(code='E', nr=0x80, struct=FFEventStruct)

    # Create a function to read a device name as a str:
    EVIOCGNAME = _IOR_str('E', 0x06)

These functions are then called to perform the operations::

    # Query the HID descriptor size (as uint):
    desc_size = HIDIOCGRDESCSIZE(fileno).value

    # Write a force feedback event (defined in a Structure):
    EVIOCSFF(fileno, ff_event_struct_instance)

    # Query the device name:
    name = EVIOCGNAME(fileno)


https://github.com/torvalds/linux/blob/master/include/uapi/asm-generic/ioctl.h

"""
from __future__ import annotations

from fcntl import ioctl as _ioctl
from ctypes import sizeof as _sizeof
from ctypes import create_string_buffer as _create_string_buffer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ctypes import Structure, c_int, c_uint
    from typing import Callable, Union
    c_data = Union[type[Structure], c_int, c_uint]


_IOC_NRBITS = 8
_IOC_TYPEBITS = 8
_IOC_SIZEBITS = 14
_IOC_DIRBITS = 2

_IOC_NRSHIFT = 0
_IOC_TYPESHIFT = _IOC_NRSHIFT + _IOC_NRBITS
_IOC_SIZESHIFT = _IOC_TYPESHIFT + _IOC_TYPEBITS
_IOC_DIRSHIFT = _IOC_SIZESHIFT + _IOC_SIZEBITS

_IOC_NONE = 0
_IOC_WRITE = 1
_IOC_READ = 2


# To avoid name conflicts with Python, the following names are substituted:
# 'io_dir' instead of 'dir' to indicate the transfer direction (READ, WRITE, NONE).
# 'code' instead of 'type' to indicate the ioctl "magic number" ('H', 'E', etc.).


def _IOC(io_dir: _IOC_NONE | _IOC_READ | _IOC_WRITE, code: int, nr: int, size: int) -> int:
    return (io_dir << _IOC_DIRSHIFT) | (code << _IOC_TYPESHIFT) | (nr << _IOC_NRSHIFT) | (size << _IOC_SIZESHIFT)


def _IOR(code: str, nr: int, struct: c_data) -> Callable:
    request = _IOC(_IOC_READ, ord(code), nr, _sizeof(struct))

    def f(fileno, *args):
        buffer = struct(*args)
        _ioctl(fileno, request, buffer)
        return buffer

    return f


def _IOR_len(code: str, nr: int) -> Callable:

    def f(fileno, buffer):
        request = _IOC(_IOC_READ, ord(code), nr, _sizeof(buffer))
        _ioctl(fileno, request, buffer)
        return buffer

    return f


def _IOR_str(code: str, nr: int) -> Callable:
    g = _IOR_len(code, nr)

    def f(fileno, length=256):
        return g(fileno, _create_string_buffer(length)).value

    return f


def _IOW(code: str, nr: int, struct: c_data) -> Callable:
    request = _IOC(_IOC_WRITE, ord(code), nr, _sizeof(struct))

    def f(fileno, buffer):
        if not isinstance(buffer, struct):
            buffer = struct(buffer)
        _ioctl(fileno, request, buffer)

    return f


def _IOWR(code: str, nr: int, struct: c_data) -> Callable:
    request = _IOC(_IOC_READ | _IOC_WRITE, ord(code), nr, _sizeof(struct))

    def f(fileno, buffer):
        _ioctl(fileno, request, buffer)
        return buffer

    return f


def _IOWR_len(code: str, nr: int) -> Callable:

    def f(fileno, buffer):
        request = _IOC(_IOC_READ | _IOC_WRITE, ord(code), nr, _sizeof(buffer))
        _ioctl(fileno, request, buffer)
        return buffer

    return f
