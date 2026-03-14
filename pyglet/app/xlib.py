import ctypes
import select

from os import read as os_read
from time import CLOCK_MONOTONIC
from select import POLLIN

from pyglet import app, lib
from pyglet.app.base import PlatformEventLoop

# TODO: remove eventfd fallbacks once Python 3.9 is EOL
#       remove timerfd fallbacks once Python 3.12 is EOL
try:
    from os import timerfd_create, timerfd_settime, timerfd_gettime
    from os import EFD_SEMAPHORE, eventfd, eventfd_read, eventfd_write
except ImportError:
    EFD_SEMAPHORE = 1

    class Timespec(ctypes.Structure):
        _fields_ = [('tv_sec', ctypes.c_long), ('tv_nsec', ctypes.c_long)]

    class Itimerspec(ctypes.Structure):
        _fields_ = [('it_interval', Timespec), ('it_value', Timespec)]

    libc = lib.load_library('libc.so.6')
    libc.timerfd_create.restype = ctypes.c_int
    libc.timerfd_create.argtypes = [ctypes.c_int, ctypes.c_int]
    libc.timerfd_settime.restype = ctypes.c_int
    libc.timerfd_settime.argtypes = ctypes.c_int, ctypes.c_int, ctypes.POINTER(Itimerspec), ctypes.POINTER(Itimerspec)
    libc.timerfd_gettime.restype = ctypes.c_int
    libc.timerfd_gettime.argtypes = [ctypes.c_int, ctypes.POINTER(Itimerspec)]

    def timerfd_create(clockid, /, *, flags=0):
        return libc.timerfd_create(clockid, flags)

    def timerfd_settime(fd, /, *, flags=0, initial=0.0, interval=0.0):
        old_spec = Itimerspec()
        new_spec = Itimerspec()
        new_spec.it_value.tv_sec = int(initial)
        new_spec.it_value.tv_nsec = int((initial - new_spec.it_value.tv_sec) * 1e9)
        new_spec.it_interval.tv_sec = int(interval)
        new_spec.it_interval.tv_nsec = int((interval - new_spec.it_interval.tv_sec) * 1e9)
        libc.timerfd_settime(fd, flags, ctypes.byref(new_spec), ctypes.byref(old_spec))
        old_initial = old_spec.it_value.tv_sec + old_spec.it_value.tv_nsec * 1e-9
        old_interval = old_spec.it_interval.tv_sec + old_spec.it_interval.tv_nsec * 1e-9
        return old_initial, old_interval

    def timerfd_gettime(fd, /):
        curr_value = Itimerspec()
        libc.timerfd_gettime(fd, curr_value)
        time_until_expiry = curr_value.it_value.tv_sec + curr_value.it_value.tv_nsec * 1e-9
        interval = curr_value.it_interval.tv_sec + curr_value.it_interval.tv_nsec * 1e-9
        return time_until_expiry, interval

    libc.eventfd.restype = ctypes.c_int
    libc.eventfd.argtypes = [ctypes.c_uint, ctypes.c_int]
    libc.eventfd_read.restype = ctypes.c_ssize_t
    libc.eventfd_read.argtypes = [ctypes.c_int, ctypes.POINTER(ctypes.c_uint64)]
    libc.eventfd_write.restype = ctypes.c_ssize_t
    libc.eventfd_write.argtypes = [ctypes.c_int, ctypes.c_uint64]

    def eventfd(initval, flags):
        return libc.eventfd(initval, flags)

    def eventfd_read(fd):
        return libc.eventfd_read(fd, ctypes.c_ulong(8))

    def eventfd_write(fd, value):
        return libc.eventfd_write(fd, value)


class XlibSelectDevice:
    def fileno(self):
        """Get the file handle for ``select()`` for this device.

        :rtype: int
        """
        raise NotImplementedError('abstract')

    def select(self):
        """Perform event processing on the device.

        Called when ``select()`` returns this device in its list of active
        files.
        """
        raise NotImplementedError('abstract')


class NotificationDevice(XlibSelectDevice):
    def __init__(self):
        self.fd = eventfd(1, EFD_SEMAPHORE)

    def fileno(self):
        return self.fd

    def select(self):
        eventfd_read(self.fd)
        app.platform_event_loop.dispatch_posted_events()

    def notify(self):
        eventfd_write(self.fd, 1)


class TimerDevice(XlibSelectDevice):
    def __init__(self):
        self.fd = timerfd_create(CLOCK_MONOTONIC)

    def fileno(self):
        return self.fd

    def select(self):
        os_read(self.fd, 8)

    def set_timer(self, value):
        timerfd_settime(self.fd, initial=value)


class XlibEventLoop(PlatformEventLoop):
    def __init__(self):
        super().__init__()
        self.monitored_devices = {}
        self.epoll = select.epoll()

        self._notification_device = NotificationDevice()
        self._timer_device = TimerDevice()

        self.register(self._notification_device)
        self.register(self._timer_device)

    def register(self, device, eventmask=POLLIN):
        self.epoll.register(device, eventmask)
        self.monitored_devices[device.fileno()] = device

    def unregister(self, device):
        self.epoll.unregister(device)
        del self.monitored_devices[device.fileno()]

    def notify(self):
        self._notification_device.notify()

    def step(self, timeout=None):
        # Timeout is from EventLoop.idle(). Return after that timeout or directly
        # after receiving a new event. None means: block for user input.

        # More precise than epoll.poll(timeout):
        if timeout:
            self._timer_device.set_timer(timeout * 0.9)

        # At least one event will be returned (a real event, or the timer event)
        for fd, _ in self.epoll.poll(timeout):
            self.monitored_devices[fd].select()

        # Check the remaining time left on the timer_device.
        # If the timer_device has expired and woke the poll, this will be 0.0 (returning False).
        # If another event woke the poll, the remainder will be greater than 0.0 (returning True).
        return timerfd_gettime(self._timer_device.fd) > (0.0, 0.0)
