import os
import select
import threading

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

    def poll(self):
        """Check if the device has events ready to process.

        :rtype: bool
        :return: True if there are events to process, False otherwise.
        """
        return False


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

    def poll(self):
        return self._event.is_set()


class XlibEventLoop(PlatformEventLoop):
    def __init__(self):
        super().__init__()
        self._notification_device = NotificationDevice()
        self.select_devices = set()
        self.select_devices.add(self._notification_device)

    def notify(self):
        self._notification_device.set()

    def step(self, timeout=None):
        # Timeout is from EventLoop.idle(). Return after that timeout or directly
        # after receiving a new event. None means: block for user input.

        # Poll devices to check for already pending events (select.select is not enough)
        pending_devices = []
        for device in self.select_devices:
            if device.poll():
                pending_devices.append(device)

        # If no devices were ready, wait until one gets ready
        if not pending_devices:
            pending_devices, _, _ = select.select(self.select_devices, (), (), timeout)

        if not pending_devices:
            # Notify caller that timeout expired without incoming events
            return False

        # Dispatch activity on matching devices
        for device in pending_devices:
            device.select()

        # Notify caller that events were handled before timeout expired
        return True
