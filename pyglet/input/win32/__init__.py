from typing import Dict, Optional

import pyglet
from pyglet.input import base

_xinput_enabled = False
if not pyglet.options["win32_disable_xinput"]:
    try:
        from pyglet.input.win32.xinput import XInputControllerManager, XInputController, XInputDevice
        from pyglet.input.win32.xinput import _device_manager as _xinput_device_manager

        _xinput_enabled = True
    except OSError:
        # Fail to import XInput.
        pass

from pyglet.input.win32.directinput import DirectInputDevice, _create_controller
from pyglet.input.win32.directinput import _di_manager as _di_device_manager


class Win32ControllerManager(base.ControllerManager):
    """This class manages XInput and DirectInput as a combined manager.
       XInput will override any XInput compatible DirectInput devices.
       Any devices not supported by XInput will fallback to DirectInput.
    """

    def __init__(self):
        self._di_controllers: Dict[DirectInputDevice, base.Controller] = {}

        if _xinput_enabled:
            self._xinput_controllers: Dict[XInputDevice, XInputController] = {}

            for xdevice in _xinput_device_manager.all_devices:  # All 4 devices are initialized.
                meta = {'name': xdevice.name, 'guid': "XINPUTCONTROLLER"}
                self._xinput_controllers[xdevice] = XInputController(xdevice, meta)

            @_xinput_device_manager.event
            def on_connect(xdevice):
                self.dispatch_event('on_connect', self._xinput_controllers[xdevice])

            @_xinput_device_manager.event
            def on_disconnect(xdevice):
                self.dispatch_event('on_disconnect', self._xinput_controllers[xdevice])

        for device in _di_device_manager.devices:
            self._add_di_controller(device)

        @_di_device_manager.event
        def on_connect(di_device):
            if di_device not in self._di_controllers:
                if self._add_di_controller(di_device):
                    pyglet.app.platform_event_loop.post_event(self, 'on_connect', self._di_controllers[di_device])

        @_di_device_manager.event
        def on_disconnect(di_device):
            if di_device in self._di_controllers:
                _controller = self._di_controllers[di_device]
                del self._di_controllers[di_device]
                pyglet.app.platform_event_loop.post_event(self, 'on_disconnect', _controller)

    def _add_di_controller(self, device: DirectInputDevice) -> Optional[base.Controller]:
        controller = _create_controller(device)
        if controller:
            self._di_controllers[device] = controller
            return controller

        return None

    def _get_xinput_controllers(self) -> list:
        if not _xinput_enabled:
            return []
        return [ctlr for ctlr in self._xinput_controllers.values() if ctlr.device.connected]

    def _get_di_controllers(self) -> list:
        return list(self._di_controllers.values())

    def get_controllers(self):
        return self._get_xinput_controllers() + self._get_di_controllers()
