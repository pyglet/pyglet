import os
import select

from math import inf
from time import CLOCK_MONOTONIC
from select import POLLIN

from pyglet import app
from pyglet.app.base import PlatformEventLoop


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
        self.fd = os.eventfd(1, os.EFD_SEMAPHORE)

    def fileno(self):
        return self.fd

    def select(self):
        os.eventfd_read(self.fd)
        app.platform_event_loop.dispatch_posted_events()

    def notify(self):
        os.eventfd_write(self.fd, 1)


class TimerDevice(XlibSelectDevice):
    def __init__(self):
        self.fd = os.timerfd_create(CLOCK_MONOTONIC)

    def fileno(self):
        return self.fd

    def select(self):
        os.read(self.fd, 1024)

    def set_timer(self, value):
        os.timerfd_settime(self.fd, initial=value)


class XlibEventLoop(PlatformEventLoop):
    def __init__(self):
        super().__init__()
        self.monitored_devices = {}
        self.epoll = select.epoll()

        self._notification_device = NotificationDevice()
        self._timer_device = TimerDevice()

        self.register(self._notification_device, POLLIN)
        self.register(self._timer_device, POLLIN)

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

        if timeout:
            self._timer_device.set_timer(timeout)

        # At least one event will be returned (a real event, or the timer event)
        for fd, _ in self.epoll.poll(timeout):
            self.monitored_devices[fd].select()

        # Check the remaining time left before the timer device times out.
        # If the timer has expired and woke the poll, this will equal 0.0 and return False.
        # If an event woke the poll, then the value will be greater than 0.0 and return True.
        return os.timerfd_gettime(self._timer_device.fd) > (0.0, 0.0)
