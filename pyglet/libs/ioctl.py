"""Factory functions to provide similar functionality to the Linux ioctl macros.

These are factory functions, and are not used directly. Instead, they are used
to create custom helper functions that perform specific tasks. For example::

    HIDIOCGRDESCSIZE = _IOR(code='H', nr=0x01, struct=ctypes.int)
    # or
    EVIOCSFF = _IOW(code='E', nr=0x80, struct=FFEventStruct)

These generated functions are then called to perform the operations::

    desc_size = HIDIOCGRDESCSIZE(fileno).value
    # or
    EVIOCSFF(fileno, ff_effect_struct_instance)


https://github.com/torvalds/linux/blob/master/include/uapi/asm-generic/ioctl.h

"""
from __future__ import annotations

from pyglet import compat_platform

if compat_platform != 'linux':
    raise ImportError("pyglet.libs.ioctl is only support unix-like platforms.")

from fcntl import ioctl as _ioctl
from ctypes import sizeof as _sizeof
from ctypes import create_string_buffer as _create_string_buffer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Callable
    from ctypes import Structure


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


def _IOR(code: str, nr: int, struct: type[Structure]) -> Callable:
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


def _IOW(code: str, nr: int, struct: type[Structure]) -> Callable:
    request = _IOC(_IOC_WRITE, ord(code), nr, _sizeof(struct))

    def f(fileno, buffer):
        if not isinstance(buffer, struct):
            buffer = struct(buffer)
        _ioctl(fileno, request, buffer)

    return f


def _IOWR(code: str, nr: int, struct: type[Structure]) -> Callable:
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
