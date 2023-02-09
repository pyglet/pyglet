import sys
import warnings

from ctypes import CFUNCTYPE, byref, c_void_p, c_int, c_ubyte, c_bool, c_uint32, c_uint64

import pyglet

from pyglet.event import EventDispatcher
from pyglet.input.base import Device, AbsoluteAxis, RelativeAxis, Button
from pyglet.input.base import Joystick, Controller, AppleRemote, ControllerManager
from pyglet.input.controller import get_mapping, create_guid

from pyglet.libs.darwin.cocoapy import CFSTR, CFIndex, CFTypeID, known_cftypes
from pyglet.libs.darwin.cocoapy import kCFRunLoopDefaultMode, CFAllocatorRef, cf
from pyglet.libs.darwin.cocoapy import cfset_to_set, cftype_to_value, cfarray_to_list


__LP64__ = (sys.maxsize > 2 ** 32)

# Uses the HID API introduced in Mac OS X version 10.5
# http://developer.apple.com/library/mac/#technotes/tn2007/tn2187.html
iokit = pyglet.lib.load_library(framework='IOKit')

# IOKit constants from
# /System/Library/Frameworks/IOKit.framework/Headers/hid/IOHIDKeys.h
kIOHIDOptionsTypeNone	     = 0x00
kIOHIDOptionsTypeSeizeDevice = 0x01

kIOHIDElementTypeInput_Misc      = 1
kIOHIDElementTypeInput_Button    = 2
kIOHIDElementTypeInput_Axis      = 3
kIOHIDElementTypeInput_ScanCodes = 4
kIOHIDElementTypeOutput          = 129
kIOHIDElementTypeFeature         = 257
kIOHIDElementTypeCollection      = 513

# /System/Library/Frameworks/IOKit.framework/Headers/hid/IOHIDUsageTables.h
kHIDPage_GenericDesktop	       = 0x01
kHIDPage_Consumer              = 0x0C
kHIDUsage_GD_SystemSleep       = 0x82
kHIDUsage_GD_SystemWakeUp      = 0x83
kHIDUsage_GD_SystemAppMenu     = 0x86
kHIDUsage_GD_SystemMenu	       = 0x89
kHIDUsage_GD_SystemMenuRight   = 0x8A
kHIDUsage_GD_SystemMenuLeft    = 0x8B
kHIDUsage_GD_SystemMenuUp      = 0x8C
kHIDUsage_GD_SystemMenuDown    = 0x8D
kHIDUsage_Csmr_Menu            = 0x40
kHIDUsage_Csmr_FastForward     = 0xB3
kHIDUsage_Csmr_Rewind          = 0xB4
kHIDUsage_Csmr_Eject	       = 0xB8
kHIDUsage_Csmr_Mute	           = 0xE2
kHIDUsage_Csmr_VolumeIncrement = 0xE9
kHIDUsage_Csmr_VolumeDecrement = 0xEA

IOReturn = c_int  # IOReturn.h
IOOptionBits = c_uint32  # IOTypes.h

# IOHIDKeys.h
IOHIDElementType = c_int
IOHIDElementCollectionType = c_int
IOHIDElementCookie = c_uint32 if __LP64__ else c_void_p

iokit.IOHIDDeviceClose.restype = IOReturn
iokit.IOHIDDeviceClose.argtypes = [c_void_p, IOOptionBits]

iokit.IOHIDDeviceConformsTo.restype = c_ubyte
iokit.IOHIDDeviceConformsTo.argtypes = [c_void_p, c_uint32, c_uint32]

iokit.IOHIDDeviceCopyMatchingElements.restype = c_void_p
iokit.IOHIDDeviceCopyMatchingElements.argtypes = [c_void_p, c_void_p, IOOptionBits]

iokit.IOHIDDeviceGetProperty.restype = c_void_p
iokit.IOHIDDeviceGetProperty.argtypes = [c_void_p, c_void_p]

iokit.IOHIDDeviceGetTypeID.restype = CFTypeID
iokit.IOHIDDeviceGetTypeID.argtypes = []

iokit.IOHIDDeviceGetValue.restype = IOReturn
iokit.IOHIDDeviceGetValue.argtypes = [c_void_p, c_void_p, c_void_p]

iokit.IOHIDDeviceOpen.restype = IOReturn
iokit.IOHIDDeviceOpen.argtypes = [c_void_p, IOOptionBits]

iokit.IOHIDDeviceRegisterInputValueCallback.restype = None
iokit.IOHIDDeviceRegisterInputValueCallback.argtypes = [c_void_p, c_void_p, c_void_p]

iokit.IOHIDDeviceScheduleWithRunLoop.restype = None
iokit.IOHIDDeviceScheduleWithRunLoop.argtypes = [c_void_p, c_void_p, c_void_p]

iokit.IOHIDDeviceUnscheduleFromRunLoop.restype = None
iokit.IOHIDDeviceUnscheduleFromRunLoop.argtypes = [c_void_p, c_void_p, c_void_p]

iokit.IOHIDElementGetCollectionType.restype = IOHIDElementCollectionType
iokit.IOHIDElementGetCollectionType.argtypes = [c_void_p]

iokit.IOHIDElementGetCookie.restype = IOHIDElementCookie
iokit.IOHIDElementGetCookie.argtypes = [c_void_p]

iokit.IOHIDElementGetLogicalMax.restype = CFIndex
iokit.IOHIDElementGetLogicalMax.argtypes = [c_void_p]

iokit.IOHIDElementGetLogicalMin.restype = CFIndex
iokit.IOHIDElementGetLogicalMin.argtypes = [c_void_p]

iokit.IOHIDElementGetName.restype = c_void_p
iokit.IOHIDElementGetName.argtypes = [c_void_p]

iokit.IOHIDElementGetPhysicalMax.restype = CFIndex
iokit.IOHIDElementGetPhysicalMax.argtypes = [c_void_p]

iokit.IOHIDElementGetPhysicalMin.restype = CFIndex
iokit.IOHIDElementGetPhysicalMin.argtypes = [c_void_p]

iokit.IOHIDElementGetReportCount.restype = c_uint32
iokit.IOHIDElementGetReportCount.argtypes = [c_void_p]

iokit.IOHIDElementGetReportID.restype = c_uint32
iokit.IOHIDElementGetReportID.argtypes = [c_void_p]

iokit.IOHIDElementGetReportSize.restype = c_uint32
iokit.IOHIDElementGetReportSize.argtypes = [c_void_p]

iokit.IOHIDElementGetType.restype = IOHIDElementType
iokit.IOHIDElementGetType.argtypes = [c_void_p]

iokit.IOHIDElementGetTypeID.restype = CFTypeID
iokit.IOHIDElementGetTypeID.argtypes = []

iokit.IOHIDElementGetUnit.restype = c_uint32
iokit.IOHIDElementGetUnit.argtypes = [c_void_p]

iokit.IOHIDElementGetUnitExponent.restype = c_uint32
iokit.IOHIDElementGetUnitExponent.argtypes = [c_void_p]

iokit.IOHIDElementGetUsage.restype = c_uint32
iokit.IOHIDElementGetUsage.argtypes = [c_void_p]

iokit.IOHIDElementGetUsagePage.restype = c_uint32
iokit.IOHIDElementGetUsagePage.argtypes = [c_void_p]

iokit.IOHIDElementHasNullState.restype = c_bool
iokit.IOHIDElementHasNullState.argtypes = [c_void_p]

iokit.IOHIDElementHasPreferredState.restype = c_bool
iokit.IOHIDElementHasPreferredState.argtypes = [c_void_p]

iokit.IOHIDElementIsArray.restype = c_bool
iokit.IOHIDElementIsArray.argtypes = [c_void_p]

iokit.IOHIDElementIsNonLinear.restype = c_bool
iokit.IOHIDElementIsNonLinear.argtypes = [c_void_p]

iokit.IOHIDElementIsRelative.restype = c_bool
iokit.IOHIDElementIsRelative.argtypes = [c_void_p]

iokit.IOHIDElementIsVirtual.restype = c_bool
iokit.IOHIDElementIsVirtual.argtypes = [c_void_p]

iokit.IOHIDElementIsWrapping.restype = c_bool
iokit.IOHIDElementIsWrapping.argtypes = [c_void_p]

iokit.IOHIDManagerCreate.restype = c_void_p
iokit.IOHIDManagerCreate.argtypes = [CFAllocatorRef, IOOptionBits]

iokit.IOHIDManagerCopyDevices.restype = c_void_p
iokit.IOHIDManagerCopyDevices.argtypes = [c_void_p]

iokit.IOHIDManagerRegisterDeviceMatchingCallback.restype = None
iokit.IOHIDManagerRegisterDeviceMatchingCallback.argtypes = [c_void_p, c_void_p, c_void_p]

iokit.IOHIDManagerRegisterDeviceRemovalCallback.restype = None
iokit.IOHIDManagerRegisterDeviceRemovalCallback.argtypes = [c_void_p, c_void_p, c_void_p]

iokit.IOHIDManagerScheduleWithRunLoop.restype = c_void_p
iokit.IOHIDManagerScheduleWithRunLoop.argtypes = [c_void_p, c_void_p, c_void_p]

iokit.IOHIDManagerSetDeviceMatching.restype = None
iokit.IOHIDManagerSetDeviceMatching.argtypes = [c_void_p, c_void_p]

iokit.IOHIDValueGetElement.restype = c_void_p
iokit.IOHIDValueGetElement.argtypes = [c_void_p]

iokit.IOHIDValueGetIntegerValue.restype = CFIndex
iokit.IOHIDValueGetIntegerValue.argtypes = [c_void_p]

iokit.IOHIDValueGetLength.restype = CFIndex
iokit.IOHIDValueGetLength.argtypes = [c_void_p]

iokit.IOHIDValueGetTimeStamp.restype = c_uint64
iokit.IOHIDValueGetTimeStamp.argtypes = [c_void_p]

iokit.IOHIDValueGetTypeID.restype = CFTypeID
iokit.IOHIDValueGetTypeID.argtypes = []

# Callback function types
HIDManagerCallback = CFUNCTYPE(None, c_void_p, c_int, c_void_p, c_void_p)
HIDDeviceCallback = CFUNCTYPE(None, c_void_p, c_int, c_void_p)
HIDDeviceValueCallback = CFUNCTYPE(None, c_void_p, c_int, c_void_p, c_void_p)

######################################################################
# HID Class Wrappers

# Lookup tables cache python objects for the devices and elements so that
# we can avoid creating multiple wrapper objects for the same device.
_device_lookup = {}   # IOHIDDeviceRef to python HIDDevice object


class HIDValue:
    def __init__(self, value_ref):
        # Check that this is a valid IOHIDValue.
        assert value_ref
        assert cf.CFGetTypeID(value_ref) == iokit.IOHIDValueGetTypeID()
        self.value_ref = value_ref
        self.timestamp = iokit.IOHIDValueGetTimeStamp(value_ref)
        self.length = iokit.IOHIDValueGetLength(value_ref)
        if self.length <= 4:
            self.intvalue = iokit.IOHIDValueGetIntegerValue(value_ref)
        else:
            # Values may be byte data rather than integers.
            # e.g. the PS3 controller has a 39-byte HIDValue element.
            # We currently do not try to handle these cases.
            self.intvalue = None
        element_ref = c_void_p(iokit.IOHIDValueGetElement(value_ref))
        self.element = HIDDeviceElement.get_element(element_ref)


class HIDDevice:
    @classmethod
    def get_device(cls, device_ref):
        # device_ref is a c_void_p pointing to an IOHIDDeviceRef
        if device_ref.value in _device_lookup:
            return _device_lookup[device_ref.value]
        else:
            device = HIDDevice(device_ref)
            return device

    def __init__(self, device_ref):
        _device_lookup[device_ref.value] = self
        self.device_ref = device_ref
        # Set attributes from device properties.
        self.transport = self.get_property("Transport")
        self.vendorID = self.get_property("VendorID")
        self.vendorIDSource = self.get_property("VendorIDSource")
        self.productID = self.get_property("ProductID")
        self.versionNumber = self.get_property("VersionNumber")
        self.manufacturer = self.get_property("Manufacturer")
        self.product = self.get_property("Product")
        self.serialNumber = self.get_property("SerialNumber")  # always returns None; apple bug?
        self.locationID = self.get_property("LocationID")
        self.primaryUsage = self.get_property("PrimaryUsage")
        self.primaryUsagePage = self.get_property("PrimaryUsagePage")
        # Populate self.elements with our device elements.
        self.elements = self._get_elements()
        # Set up callback functions.
        self.value_observers = set()
        self.value_callback = self._register_input_value_callback()

    def get_guid(self):
        """Generate an SDL2 style GUID from the product guid."""
        # TODO: in what situation should 0x05 be used?
        # 0x03: USB
        # 0x05: Bluetooth
        bustype = 0x03
        vendor = self.vendorID or 0
        product = self.productID or 0
        version = self.versionNumber or 0
        name = self.product or ""
        return create_guid(bustype, vendor, product, version, name, 0, 0)

    def get_property(self, name):
        cfname = CFSTR(name)
        cfvalue = c_void_p(iokit.IOHIDDeviceGetProperty(self.device_ref, cfname))
        cf.CFRelease(cfname)
        return cftype_to_value(cfvalue)

    def open(self, exclusive_mode=False):
        if exclusive_mode:
            options = kIOHIDOptionsTypeSeizeDevice
        else:
            options = kIOHIDOptionsTypeNone
        return bool(iokit.IOHIDDeviceOpen(self.device_ref, options))

    def close(self):
        return bool(iokit.IOHIDDeviceClose(self.device_ref, kIOHIDOptionsTypeNone))

    def schedule_with_run_loop(self):
        iokit.IOHIDDeviceScheduleWithRunLoop(
            self.device_ref,
            c_void_p(cf.CFRunLoopGetCurrent()),
            kCFRunLoopDefaultMode)

    def unschedule_from_run_loop(self):
        iokit.IOHIDDeviceUnscheduleFromRunLoop(
            self.device_ref,
            c_void_p(cf.CFRunLoopGetCurrent()),
            kCFRunLoopDefaultMode)

    def _get_elements(self):
        cfarray = c_void_p(iokit.IOHIDDeviceCopyMatchingElements(self.device_ref, None, 0))
        if not cfarray:
            # requires "Security & Privacy / Input Monitoring", see #95
            return []
        elements = cfarray_to_list(cfarray)
        cf.CFRelease(cfarray)
        return elements

    # Page and usage IDs are from the HID usage tables located at
    # https://usb.org/sites/default/files/hut1_3_0.pdf
    def conforms_to(self, page, usage):
        return bool(iokit.IOHIDDeviceConformsTo(self.device_ref, page, usage))

    def is_pointer(self):
        return self.conforms_to(0x01, 0x01)

    def is_mouse(self):
        return self.conforms_to(0x01, 0x02)

    def is_joystick(self):
        return self.conforms_to(0x01, 0x04)

    def is_gamepad(self):
        return self.conforms_to(0x01, 0x05)

    def is_keyboard(self):
        return self.conforms_to(0x01, 0x06)

    def is_keypad(self):
        return self.conforms_to(0x01, 0x07)

    def is_multi_axis(self):
        return self.conforms_to(0x01, 0x08)

    def py_value_callback(self, context, result, sender, value):
        v = HIDValue(c_void_p(value))
        # Dispatch value changed message to all observers.
        for x in self.value_observers:
            if hasattr(x, 'device_value_changed'):
                x.device_value_changed(self, v)

    def _register_input_value_callback(self):
        value_callback = HIDDeviceValueCallback(self.py_value_callback)
        iokit.IOHIDDeviceRegisterInputValueCallback(self.device_ref, value_callback, None)
        return value_callback

    def add_value_observer(self, observer):
        self.value_observers.add(observer)

    def get_value(self, element):
        # If the device is not open, then returns None
        value_ref = c_void_p()
        iokit.IOHIDDeviceGetValue(self.device_ref, element.element_ref, byref(value_ref))
        if value_ref:
            return HIDValue(value_ref)
        else:
            return None

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.product})"


class HIDDeviceElement:

    @classmethod
    def get_element(cls, element_ref):
        # element_ref is a c_void_p pointing to an IOHIDDeviceElementRef
        return HIDDeviceElement(element_ref)

    def __init__(self, element_ref):
        self.element_ref = element_ref
        # Set element properties as attributes.
        self.cookie = iokit.IOHIDElementGetCookie(element_ref)
        self.type = iokit.IOHIDElementGetType(element_ref)
        if self.type == kIOHIDElementTypeCollection:
            self.collectionType = iokit.IOHIDElementGetCollectionType(element_ref)
        else:
            self.collectionType = None
        self.usagePage = iokit.IOHIDElementGetUsagePage(element_ref)
        self.usage = iokit.IOHIDElementGetUsage(element_ref)
        self.isVirtual = bool(iokit.IOHIDElementIsVirtual(element_ref))
        self.isRelative = bool(iokit.IOHIDElementIsRelative(element_ref))
        self.isWrapping = bool(iokit.IOHIDElementIsWrapping(element_ref))
        self.isArray = bool(iokit.IOHIDElementIsArray(element_ref))
        self.isNonLinear = bool(iokit.IOHIDElementIsNonLinear(element_ref))
        self.hasPreferredState = bool(iokit.IOHIDElementHasPreferredState(element_ref))
        self.hasNullState = bool(iokit.IOHIDElementHasNullState(element_ref))
        self.name = cftype_to_value(iokit.IOHIDElementGetName(element_ref))
        self.reportID = iokit.IOHIDElementGetReportID(element_ref)
        self.reportSize = iokit.IOHIDElementGetReportSize(element_ref)
        self.reportCount = iokit.IOHIDElementGetReportCount(element_ref)
        self.unit = iokit.IOHIDElementGetUnit(element_ref)
        self.unitExponent = iokit.IOHIDElementGetUnitExponent(element_ref)
        self.logicalMin = iokit.IOHIDElementGetLogicalMin(element_ref)
        self.logicalMax = iokit.IOHIDElementGetLogicalMax(element_ref)
        self.physicalMin = iokit.IOHIDElementGetPhysicalMin(element_ref)
        self.physicalMax = iokit.IOHIDElementGetPhysicalMax(element_ref)


class HIDManager(EventDispatcher):
    def __init__(self):
        """Create an instance of an HIDManager."""
        self.manager_ref = c_void_p(iokit.IOHIDManagerCreate(None, kIOHIDOptionsTypeNone))
        self.schedule_with_run_loop()

        self.devices = self._get_devices()
        self.matching_callback = self._register_matching_callback()
        self.removal_callback = self._register_removal_callback()

    def _get_devices(self):
        try:
            # Tell manager that we are willing to match *any* device.
            # (Alternatively, we could restrict by device usage, or usage page.)
            iokit.IOHIDManagerSetDeviceMatching(self.manager_ref, None)
            # Copy the device set and convert it to python.
            cfset = c_void_p(iokit.IOHIDManagerCopyDevices(self.manager_ref))
            devices = cfset_to_set(cfset)
            cf.CFRelease(cfset)
        except:
            return set()
        return devices

    def open(self):
        iokit.IOHIDManagerOpen(self.manager_ref, kIOHIDOptionsTypeNone)

    def close(self):
        iokit.IOHIDManagerClose(self.manager_ref, kIOHIDOptionsTypeNone)

    def schedule_with_run_loop(self):
        iokit.IOHIDManagerScheduleWithRunLoop(
            self.manager_ref,
            c_void_p(cf.CFRunLoopGetCurrent()),
            kCFRunLoopDefaultMode)

    def unschedule_from_run_loop(self):
        iokit.IOHIDManagerUnscheduleFromRunLoop(
            self.manager_ref,
            c_void_p(cf.CFRunLoopGetCurrent()),
            kCFRunLoopDefaultMode)

    # Device add/remove callbacks:

    def _py_matching_callback(self, context, result, sender, device):
        d = HIDDevice.get_device(c_void_p(device))
        if d not in self.devices:
            self.devices.add(d)
            self.dispatch_event("on_connect", d)

    def _register_matching_callback(self):
        matching_callback = HIDManagerCallback(self._py_matching_callback)
        iokit.IOHIDManagerRegisterDeviceMatchingCallback(self.manager_ref, matching_callback, None)
        return matching_callback

    def _py_removal_callback(self, context, result, sender, device):
        d = HIDDevice.get_device(c_void_p(device))
        d.close()
        if d in self.devices:
            self.devices.remove(d)
            self.dispatch_event("on_disconnect", d)

    def _register_removal_callback(self):
        removal_callback = HIDManagerCallback(self._py_removal_callback)
        iokit.IOHIDManagerRegisterDeviceRemovalCallback(self.manager_ref, removal_callback, None)
        return removal_callback


HIDManager.register_event_type('on_connect')
HIDManager.register_event_type('on_disconnect')


######################################################################
# Add conversion methods for IOHIDDevices and IOHIDDeviceElements
# to the list of known types used by cftype_to_value.
known_cftypes[iokit.IOHIDDeviceGetTypeID()] = HIDDevice.get_device
known_cftypes[iokit.IOHIDElementGetTypeID()] = HIDDeviceElement.get_element
######################################################################

# Pyglet interface to HID


_axis_names = {
    (0x01, 0x30): 'x',
    (0x01, 0x31): 'y',
    (0x01, 0x32): 'z',
    (0x01, 0x33): 'rx',
    (0x01, 0x34): 'ry',
    (0x01, 0x35): 'rz',
    (0x01, 0x38): 'wheel',
    (0x01, 0x39): 'hat',
}


_button_names = {
    (kHIDPage_GenericDesktop, kHIDUsage_GD_SystemSleep): 'sleep',
    (kHIDPage_GenericDesktop, kHIDUsage_GD_SystemWakeUp): 'wakeup',
    (kHIDPage_GenericDesktop, kHIDUsage_GD_SystemAppMenu): 'menu',
    (kHIDPage_GenericDesktop, kHIDUsage_GD_SystemMenu): 'select',
    (kHIDPage_GenericDesktop, kHIDUsage_GD_SystemMenuRight): 'right',
    (kHIDPage_GenericDesktop, kHIDUsage_GD_SystemMenuLeft): 'left',
    (kHIDPage_GenericDesktop, kHIDUsage_GD_SystemMenuUp): 'up',
    (kHIDPage_GenericDesktop, kHIDUsage_GD_SystemMenuDown): 'down',
    (kHIDPage_Consumer, kHIDUsage_Csmr_FastForward): 'right_hold',
    (kHIDPage_Consumer, kHIDUsage_Csmr_Rewind): 'left_hold',
    (kHIDPage_Consumer, kHIDUsage_Csmr_Menu): 'menu_hold',
    (0xff01, 0x23): 'select_hold',
    (kHIDPage_Consumer, kHIDUsage_Csmr_Eject): 'eject',
    (kHIDPage_Consumer, kHIDUsage_Csmr_Mute): 'mute',
    (kHIDPage_Consumer, kHIDUsage_Csmr_VolumeIncrement): 'volume_up',
    (kHIDPage_Consumer, kHIDUsage_Csmr_VolumeDecrement): 'volume_down'
}


class PygletDevice(Device):
    def __init__(self, display, device):
        super().__init__(display=display, name=device.product)
        self.device = device
        self.device.add_value_observer(self)
        self._create_controls()

    def open(self, window=None, exclusive=False):
        super().open(window, exclusive)
        self.device.open(exclusive)
        self._set_initial_control_values()

    def close(self):
        super().close()
        self.device.close()

    def get_controls(self):
        return list(self._controls.values())

    def get_guid(self):
        return self.device.get_guid()

    def device_value_changed(self, hid_device, hid_value):
        # Called by device when input value changes.
        control = self._controls[hid_value.element.cookie]
        control.value = hid_value.intvalue

    def _create_controls(self):
        controls = []

        for element in self.device.elements:
            raw_name = element.name or '0x%x:%x' % (element.usagePage, element.usage)
            if element.type in (kIOHIDElementTypeInput_Misc, kIOHIDElementTypeInput_Axis):
                name = _axis_names.get((element.usagePage, element.usage))
                if element.isRelative:
                    control = RelativeAxis(name, raw_name)
                else:
                    control = AbsoluteAxis(name, element.logicalMin, element.logicalMax, raw_name)
            elif element.type == kIOHIDElementTypeInput_Button:
                name = _button_names.get((element.usagePage, element.usage))
                control = Button(name, raw_name)
            else:
                continue

            control._cookie = element.cookie
            control._usage = element.usage
            controls.append(control)

        controls.sort(key=lambda c: c._usage)
        self._controls = {control._cookie: control for control in controls}

    def _set_initial_control_values(self):
        # Must be called AFTER the device has been opened.
        for element in self.device.elements:
            if element.cookie in self._controls:
                control = self._controls[element.cookie]
                hid_value = self.device.get_value(element)
                if hid_value:
                    control.value = hid_value.intvalue

    def __repr__(self):
        return f"{self.__class__.__name__}({self.device})"

######################################################################


_hid_manager = HIDManager()


class DarwinControllerManager(ControllerManager):

    def __init__(self, display=None):
        self._controllers = {}

        for device in _hid_manager.devices:
            if controller := _create_controller(device, display):
                self._controllers[device] = controller

        @_hid_manager.event
        def on_connect(hiddevice):
            if _controller := _create_controller(hiddevice, display):
                self._controllers[hiddevice] = _controller
                pyglet.app.platform_event_loop.post_event(self, 'on_connect', _controller)

        @_hid_manager.event
        def on_disconnect(hiddevice):
            if hiddevice in self._controllers:
                _controller = self._controllers[hiddevice]
                del self._controllers[hiddevice]
                pyglet.app.platform_event_loop.post_event(self, 'on_disconnect', _controller)

    def get_controllers(self):
        return list(self._controllers.values())


def get_devices(display=None):
    return [PygletDevice(display, device) for device in _hid_manager.devices]


def get_joysticks(display=None):
    return [Joystick(PygletDevice(display, device)) for device in _hid_manager.devices
            if device.is_joystick() or device.is_gamepad() or device.is_multi_axis()]


def get_apple_remote(display=None):
    for device in _hid_manager.devices:
        if device.product == 'Apple IR':
            return AppleRemote(PygletDevice(display, device))


def _create_controller(device, display):

    if not device.transport and device.transport.upper() in ('USB', 'BLUETOOTH'):
        return

    if device.is_joystick() or device.is_gamepad() or device.is_multi_axis():

        if mapping := get_mapping(device.get_guid()):
            return Controller(PygletDevice(display, device), mapping)
        else:
            warnings.warn(f"Warning: {device} (GUID: {device.get_guid()}) "
                          f"has no controller mappings. Update the mappings in the Controller DB.")


def get_controllers(display=None):
    return [controller for controller in
            [_create_controller(device, display) for device in _hid_manager.devices
             if device.is_joystick() or device.is_gamepad() or device.is_multi_axis()]
            if controller is not None]
