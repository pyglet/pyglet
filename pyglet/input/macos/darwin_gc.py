from __future__ import annotations

from ctypes import cdll, util, c_void_p
from typing import Protocol

from pycocoa import ObjCSubclass, ObjCInstance, send_super

from pyglet.window.cocoa.pyglet_delegate import NSNotification


from pyglet.input import ControllerManager, Device, Control

from pyglet.libs.darwin import ObjCClass, get_selector

lib = util.find_library('GameController')

# Hack for compatibility with macOS > 11.0
if lib is None:
    lib = '/System/Library/Frameworks/GameController.framework/GameController'

gc = cdll.LoadLibrary(lib)

GCController = ObjCClass("GCController")

class _GCController(Protocol):
    """Just a type hint to better understand the controller API's"""
    def playerIndex(self) -> int: ...
    def vendorName(self) -> str: ...
    def battery(self): ...
    def haptics(self): ...
    def light(self): ...
    def physicalInputProfile(self): ...

NSNotificationCenter = ObjCClass("NSNotificationCenter")

GCControllerDidConnectNotification = c_void_p.in_dll(gc, 'GCControllerDidConnectNotification')
GCControllerDidDisconnectNotification = c_void_p.in_dll(gc, 'GCControllerDidDisconnectNotification')

class PygletAppleDevice(Device):

    def __init__(self, controller: _GCController) -> None:
        self.device_name = controller.vendorName()
        self.product_category = controller.productCategory()


        super().__init__(None, self.device_name)
        self.index = controller.playerIndex()



        print("DEVICE NAME", self.device_name, self.index, self.product_category)

    def get_controls(self) -> list[Control]:
        return list(self.controls.values())

    def get_guid(self) -> str:
        return self.guid

class AppleControllerManager_Implementation(ControllerManager):
    PygletAppleControllerManager = ObjCSubclass('NSObject', 'PygletAppleControllerManager')

    def __init__(self, display=None):
        self._controllers = {}

    def init(self):
        self = ObjCInstance(send_super(self, 'init'))
        if self is None:
            return None

        center = NSNotificationCenter.defaultCenter()
        center.addObserver_selector_name_object_(
            self,
            get_selector("controller_connected:"),
            GCControllerDidConnectNotification,
            None,
        )
        center.addObserver_selector_name_object_(
            self,
            get_selector("controller_disconnected:"),
            GCControllerDidDisconnectNotification,
            None,
        )

        GCController.startWirelessControllerDiscoveryWithCompletionHandler_(None)
        return self

    @PygletAppleControllerManager.method('v@')
    def controller_connected_(self, notification: NSNotification):
        controller = notification.object()
        print("Controller", controller)
        #if _controller := _create_controller(hiddevice, display):
        #    self._controllers[hiddevice] = _controller
        #    pyglet.app.platform_event_loop.post_event(self, 'on_connect', _controller)

    @PygletAppleControllerManager.method('v@')
    def controller_disconnected_(self, notification: NSNotification):
        controller = notification.object()
        print("Controller", controller)

        #if hiddevice in self._controllers:
        #    _controller = self._controllers[hiddevice]
        #    del self._controllers[hiddevice]
        #    pyglet.app.platform_event_loop.post_event(self, 'on_disconnect', _controller)


    def get_controllers(self):
        return list(self._controllers.values())



_apple_gc_manager = AppleControllerManager_Implementation()

#
# def get_joysticks(display=None):
#     return [Joystick(PygletDevice(display, device)) for device in _hid_manager.devices
#             if device.is_joystick() or device.is_gamepad() or device.is_multi_axis()]
#
#
# def get_apple_remote(display=None):
#     for device in _hid_manager.devices:
#         if device.product == 'Apple IR':
#             return AppleRemote(PygletDevice(display, device))
#
#
# def _create_controller(device, display):
#
#     if not device.transport or device.transport.upper() not in ('USB', 'BLUETOOTH', 'BLUETOOTH LOW ENERGY'):
#         return None
#
#     if device.is_joystick() or device.is_gamepad() or device.is_multi_axis():
#
#         if mapping := get_mapping(device.get_guid()):
#             return Controller(PygletDevice(display, device, axis_filter=[0x1, 0x2]), mapping)
#         else:
#             warnings.warn(f"Warning: {device} (GUID: {device.get_guid()}) "
#                           f"has no controller mappings. Update the mappings in the Controller DB.")
#
#
# def get_controllers(display=None):
#     return [controller for controller in
#             [_create_controller(device, display) for device in _hid_manager.devices
#              if device.is_joystick() or device.is_gamepad() or device.is_multi_axis()]
#             if controller is not None]
