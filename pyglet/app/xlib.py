import os
import select
import threading

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
        self._sync_file_read, self._sync_file_write = os.pipe()
        self._event = threading.Event()

    def fileno(self):
        return self._sync_file_read

    def set(self):
        self._event.set()
        os.write(self._sync_file_write, b'1')

    def select(self):
        self._event.clear()
        os.read(self._sync_file_read, 1)
        app.platform_event_loop.dispatch_posted_events()


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
        self._notification_device = NotificationDevice()
        self._timer_device = TimerDevice()

        self.monitored_devices = {}
        self.epoll = select.epoll()

        self.register(self._notification_device, POLLIN)
        self.register(self._timer_device, POLLIN)

    def register(self, device, eventmask=POLLIN):
        self.epoll.register(device, eventmask)
        self.monitored_devices[device.fileno()] = device

    def unregister(self, device):
        self.epoll.unregister(device)
        del self.monitored_devices[device.fileno()]

    def notify(self):
        self._notification_device.set()

    def step(self, timeout=None):
        # Timeout is from EventLoop.idle(). Return after that timeout or directly
        # after receiving a new event. None means: block for user input.

        # The TimerDevice file descriptor will wake the poll:
        self._timer_device.set_timer(timeout)

        # At least one event will be returned (a real event, or the timer event)
        events = self.epoll.poll(None)

        if len(events) == 1 and (self._timer_device.fd, 1) in events:
            return False

        for fd, _ in events:
            self.monitored_devices[fd].select()

        return True
