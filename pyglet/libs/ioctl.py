from pyglet import compat_platform

if compat_platform != 'linux':
    raise ImportError("pyglet.libs.ioctl is only support unix-like platforms.")

from fcntl import ioctl as _ioctl
from ctypes import sizeof as _sizeof
from ctypes import create_string_buffer as _create_string_buffer


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


def _IOC(dir, type, nr, size):
    return (dir << _IOC_DIRSHIFT) | (type << _IOC_TYPESHIFT) | (nr << _IOC_NRSHIFT) | (size << _IOC_SIZESHIFT)


def _IOR(type, nr, struct):
    request = _IOC(_IOC_READ, ord(type), nr, _sizeof(struct))

    def f(fileno):
        buffer = struct()
        _ioctl(fileno, request, buffer)
        return buffer

    return f


def _IOR_len(type, nr):
    def f(fileno, buffer):
        request = _IOC(_IOC_READ, ord(type), nr, _sizeof(buffer))
        _ioctl(fileno, request, buffer)
        return buffer

    return f


def _IOR_str(type, nr):
    g = _IOR_len(type, nr)

    def f(fileno, length=256):
        return g(fileno, _create_string_buffer(length)).value

    return f


def _IOW(type, nr, struct):
    request = _IOC(_IOC_WRITE, ord(type), nr, _sizeof(struct))

    def f(fileno, buffer):
        if not isinstance(buffer, struct):
            buffer = struct(buffer)
        _ioctl(fileno, request, buffer)

    return f


def _IOWR(type, nr, struct):
    request = _IOC(_IOC_READ | _IOC_WRITE, ord(type), nr, _sizeof(struct))

    def f(fileno, buffer):
        _ioctl(fileno, request, buffer)
        return buffer

    return f


def _IOWR_len(type, nr):
    def f(fileno, buffer):
        request = _IOC(_IOC_READ | _IOC_WRITE, ord(type), nr, _sizeof(buffer))
        _ioctl(fileno, request, buffer)
        return buffer

    return f
