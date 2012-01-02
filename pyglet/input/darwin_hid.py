# Uses the HID API introduced in Mac OS X version 10.5
# http://developer.apple.com/library/mac/#technotes/tn2007/tn2187.html

from ctypes import *
from ctypes import util

# Load frameworks
iokit = cdll.LoadLibrary(util.find_library('IOKit'))
cf = cdll.LoadLibrary(util.find_library('CoreFoundation'))

# Core Foundation constants
kCFStringEncodingASCII   = 0x0600
kCFStringEncodingUnicode = 0x0100
kCFStringEncodingUTF8    = 0x08000100

kCFNumberIntType = 9

kCFRunLoopDefaultMode = c_void_p.in_dll(iokit, 'kCFRunLoopDefaultMode')

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
kHIDUsage_Csmr_Mute	       = 0xE2
kHIDUsage_Csmr_VolumeIncrement = 0xE9
kHIDUsage_Csmr_VolumeDecrement = 0xEA


# Setup return types for functions that return pointers.
# (Otherwise ctypes returns 32-bit int which breaks on 64-bit systems.)
# Note that you must also wrap the return value with c_void_p before
# you use it as an argument to another function, otherwise ctypes will
# automatically convert it back to a 32-bit int again.
cf.CFStringCreateWithCString.restype = c_void_p
cf.CFArrayGetValueAtIndex.restype = c_void_p
cf.CFRunLoopGetCurrent.restype = c_void_p
cf.CFRunLoopGetMain.restype = c_void_p
iokit.IOHIDDeviceGetProperty.restype = c_void_p
iokit.IOHIDDeviceCopyMatchingElements.restype = c_void_p
iokit.IOHIDValueGetElement.restype = c_void_p
iokit.IOHIDElementGetName.restype = c_void_p
iokit.IOHIDManagerCreate.restype = c_void_p
iokit.IOHIDManagerCopyDevices.restype = c_void_p

# Callback function types
HIDManagerCallback = CFUNCTYPE(None, c_void_p, c_int, c_void_p, c_void_p)    
HIDDeviceCallback = CFUNCTYPE(None, c_void_p, c_int, c_void_p)    
HIDDeviceValueCallback = CFUNCTYPE(None, c_void_p, c_int, c_void_p, c_void_p)    

######################################################################
# Core Foundation type to Python type conversion functions

def CFSTR(text):
    return c_void_p(cf.CFStringCreateWithCString(None, text.encode('utf8'), kCFStringEncodingUTF8))

def cfstring_to_string(cfstring):
    length = cf.CFStringGetLength(cfstring)
    size = cf.CFStringGetMaximumSizeForEncoding(length, kCFStringEncodingUTF8)
    buffer = c_buffer(size + 1)
    result = cf.CFStringGetCString(cfstring, buffer, len(buffer), kCFStringEncodingUTF8)
    if result:
        return buffer.value

def cfnumber_to_int(cfnumber):
    result = c_int()
    if cf.CFNumberGetValue(cfnumber, kCFNumberIntType, byref(result)):
        return result.value

def cfset_to_set(cfset):
    count = cf.CFSetGetCount(cfset)
    buffer = (c_void_p * count)()
    cf.CFSetGetValues(cfset, byref(buffer))
    return set([ cftype_to_value(c_void_p(buffer[i])) for i in range(count) ])
    
def cfarray_to_list(cfarray):
    count = cf.CFArrayGetCount(cfarray)
    return [ cftype_to_value(c_void_p(cf.CFArrayGetValueAtIndex(cfarray, i))) 
             for i in range(count) ]
    
def cftype_to_value(cftype):
    if not cftype:
        return None
    typeID = cf.CFGetTypeID(cftype)
    if typeID == cf.CFStringGetTypeID():
        return cfstring_to_string(cftype)
    elif typeID == cf.CFNumberGetTypeID():
        return cfnumber_to_int(cftype)
    elif typeID == iokit.IOHIDDeviceGetTypeID():
        return HIDDevice.get_device(cftype)
    elif typeID == iokit.IOHIDElementGetTypeID():
        return HIDDeviceElement.get_element(cftype)
    else:
        return cftype

######################################################################
# HID Class Wrappers

# Lookup tables cache python objects for the devices and elements so that
# we can avoid creating multiple wrapper objects for the same device.
_device_lookup = {}  # IOHIDDeviceRef to python HIDDevice object  
_element_lookup = {} # IOHIDElementRef to python HIDDeviceElement object

class HIDValue:
    def __init__(self, valueRef):
        # Check that this is a valid IOHIDValue.
        assert(valueRef)
        assert(cf.CFGetTypeID(valueRef) == iokit.IOHIDValueGetTypeID())
        self.valueRef = valueRef
        self.timestamp = iokit.IOHIDValueGetTimeStamp(valueRef)
        self.intvalue = iokit.IOHIDValueGetIntegerValue(valueRef)
        elementRef = c_void_p(iokit.IOHIDValueGetElement(valueRef))
        self.element = HIDDeviceElement.get_element(elementRef)

class HIDDevice:
    @classmethod
    def get_device(cls, deviceRef):
        # deviceRef is a c_void_p pointing to an IOHIDDeviceRef
        if deviceRef.value in _device_lookup:
            return _device_lookup[deviceRef.value]
        else:
            device = HIDDevice(deviceRef)
            return device

    def __init__(self, deviceRef):
        # Check that we've got a valid IOHIDDevice.
        assert(deviceRef)
        assert(cf.CFGetTypeID(deviceRef) == iokit.IOHIDDeviceGetTypeID())
        _device_lookup[deviceRef.value] = self
        self.deviceRef = deviceRef
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
        self.get_elements()        
        # Set up callback functions.
        self.value_observers = set()
        self.removal_observers = set()
        self.register_removal_callback()
        self.register_input_value_callback()

    def dump_info(self):
        for x in ('manufacturer', 'product', 'transport', 'vendorID', 'vendorIDSource', 'productID', 
                  'versionNumber', 'serialNumber', 'locationID', 'primaryUsage', 'primaryUsagePage'):
            value = getattr(self, x)
            print x + ":", value

    def unique_identifier(self):
        # Since we can't rely on the serial number, create our own identifier.
        # Can use this to find devices when they are plugged back in.
        return (self.manufacturer, self.product, self.vendorID, self.productID, 
                self.versionNumber, self.primaryUsage, self.primaryUsagePage)

    def get_property(self, name):
        cfvalue = c_void_p(iokit.IOHIDDeviceGetProperty(self.deviceRef, CFSTR(name)))
        return cftype_to_value(cfvalue)
        
    def open(self, exclusive_mode=False):
        if exclusive_mode: options = kIOHIDOptionsTypeSeizeDevice
        else: options = kIOHIDOptionsTypeNone
        return bool(iokit.IOHIDDeviceOpen(self.deviceRef, options))
    
    def close(self):
        return bool(iokit.IOHIDDeviceClose(self.deviceRef, kIOHIDOptionsTypeNone))

    def schedule_with_run_loop(self):
        iokit.IOHIDDeviceScheduleWithRunLoop(
            self.deviceRef, 
            c_void_p(cf.CFRunLoopGetCurrent()), 
            kCFRunLoopDefaultMode)

    def unschedule_from_run_loop(self):
        iokit.IOHIDDeviceUnscheduleFromRunLoop(
            self.deviceRef, 
            c_void_p(cf.CFRunLoopGetCurrent()), 
            kCFRunLoopDefaultMode)

    def get_elements(self):
        cfarray = c_void_p(iokit.IOHIDDeviceCopyMatchingElements(self.deviceRef, None, 0))
        self.elements = cfarray_to_list(cfarray)
        cf.CFRelease(cfarray)

    # Page and usage IDs are from the HID usage tables located at
    # http://www.usb.org/developers/devclass_docs/Hut1_12.pdf
    def conforms_to(self, page, usage):
        return bool(iokit.IOHIDDeviceConformsTo(self.deviceRef, page, usage))
    def is_pointer(self):    return self.conforms_to(0x01, 0x01)
    def is_mouse(self):      return self.conforms_to(0x01, 0x02)
    def is_joystick(self):   return self.conforms_to(0x01, 0x04)
    def is_gamepad(self):    return self.conforms_to(0x01, 0x05)
    def is_keyboard(self):   return self.conforms_to(0x01, 0x06)
    def is_keypad(self):     return self.conforms_to(0x01, 0x07)
    def is_multi_axis(self): return self.conforms_to(0x01, 0x08)

    def py_removal_callback(self, context, result, sender):
        self = _device_lookup[sender] # avoid wonky python context issues
        # Dispatch removal message to all observers.
        for x in self.removal_observers:
            if hasattr(x, 'device_removed'):
                x.device_removed(self)
        # Remove self from device lookup table.
        del _device_lookup[sender]
        # Remove device elements from lookup table.
        for key, value in _element_lookup.items():
            if value in self.elements:
                del _element_lookup[key]

    def register_removal_callback(self):
        self.removal_callback = HIDDeviceCallback(self.py_removal_callback)
        iokit.IOHIDDeviceRegisterRemovalCallback(
            self.deviceRef,
            self.removal_callback,
            None)

    def add_removal_observer(self, observer):
        self.removal_observers.add(observer)

    def py_value_callback(self, context, result, sender, value):
        v = HIDValue(c_void_p(value))
        # Dispatch value changed message to all observers.
        for x in self.value_observers:
            if hasattr(x, 'device_value_changed'):
                x.device_value_changed(self, v)

    def register_input_value_callback(self):
        self.value_callback = HIDDeviceValueCallback(self.py_value_callback)
        iokit.IOHIDDeviceRegisterInputValueCallback(
            self.deviceRef, 
            self.value_callback,
            None)

    def add_value_observer(self, observer):
        self.value_observers.add(observer)

    def get_value(self, element):
        # If the device is not open, then returns None
        valueRef = c_void_p()
        iokit.IOHIDDeviceGetValue(self.deviceRef, element.elementRef, byref(valueRef))
        if valueRef:
            return HIDValue(valueRef)
        else:
            return None


class HIDDeviceElement:
    @classmethod
    def get_element(cls, elementRef):
        # elementRef is a c_void_p pointing to an IOHIDDeviceElementRef
        if elementRef.value in _element_lookup:
            return _element_lookup[elementRef.value]
        else:
            element = HIDDeviceElement(elementRef)
            return element

    def __init__(self, elementRef):
        # Check that we've been passed a valid IOHIDElement.
        assert(elementRef)
        assert(cf.CFGetTypeID(elementRef) == iokit.IOHIDElementGetTypeID())
        _element_lookup[elementRef.value] = self
        self.elementRef = elementRef
        # Set element properties as attributes.
        self.cookie = iokit.IOHIDElementGetCookie(elementRef)
        self.type = iokit.IOHIDElementGetType(elementRef)
        if self.type == kIOHIDElementTypeCollection:
            self.collectionType = iokit.IOHIDElementGetCollectionType(elementRef)
        else:
            self.collectionType = None
        self.usagePage = iokit.IOHIDElementGetUsagePage(elementRef)
        self.usage = iokit.IOHIDElementGetUsage(elementRef)
        self.isVirtual = bool(iokit.IOHIDElementIsVirtual(elementRef))
        self.isRelative = bool(iokit.IOHIDElementIsRelative(elementRef))
        self.isWrapping = bool(iokit.IOHIDElementIsWrapping(elementRef))
        self.isArray = bool(iokit.IOHIDElementIsArray(elementRef))
        self.isNonLinear = bool(iokit.IOHIDElementIsNonLinear(elementRef))
        self.hasPreferredState = bool(iokit.IOHIDElementHasPreferredState(elementRef))
        self.hasNullState = bool(iokit.IOHIDElementHasNullState(elementRef))
        self.name = cftype_to_value(iokit.IOHIDElementGetName(elementRef))
        self.reportID = iokit.IOHIDElementGetReportID(elementRef)
        self.reportSize = iokit.IOHIDElementGetReportSize(elementRef)
        self.reportCount = iokit.IOHIDElementGetReportCount(elementRef)        
        self.unit = iokit.IOHIDElementGetUnit(elementRef)        
        self.unitExponent = iokit.IOHIDElementGetUnitExponent(elementRef)
        self.logicalMin = iokit.IOHIDElementGetLogicalMin(elementRef)
        self.logicalMax = iokit.IOHIDElementGetLogicalMax(elementRef)
        self.physicalMin = iokit.IOHIDElementGetPhysicalMin(elementRef)
        self.physicalMax = iokit.IOHIDElementGetPhysicalMax(elementRef)


class HIDManager:
    def __init__(self):
        # Create the HID Manager.
        self.managerRef = c_void_p(iokit.IOHIDManagerCreate(None, kIOHIDOptionsTypeNone))
        assert(self.managerRef)
        assert cf.CFGetTypeID(self.managerRef) == iokit.IOHIDManagerGetTypeID()
        self.schedule_with_run_loop()
        self.matching_observers = set()
        self.register_matching_callback()
        self.get_devices()
        
    def get_devices(self):
        # Tell manager that we are willing to match *any* device.    
        # (Alternatively, we could restrict by device usage, or usage page.)
        iokit.IOHIDManagerSetDeviceMatching(self.managerRef, None)
        # Copy the device set and convert it to python.
        cfset = c_void_p(iokit.IOHIDManagerCopyDevices(self.managerRef))
        self.devices = cfset_to_set(cfset)
        cf.CFRelease(cfset)

    def open(self):
        iokit.IOHIDManagerOpen(self.managerRef, kIOHIDOptionsTypeNone)

    def close(self):
        iokit.IOHIDManagerClose(self.managerRef, kIOHIDOptionsTypeNone)
        
    def schedule_with_run_loop(self):
        iokit.IOHIDManagerScheduleWithRunLoop(
            self.managerRef, 
            c_void_p(cf.CFRunLoopGetCurrent()), 
            kCFRunLoopDefaultMode)
        
    def unschedule_from_run_loop(self):
        iokit.IOHIDManagerUnscheduleFromRunLoop(
            self.managerRef, 
            c_void_p(cf.CFRunLoopGetCurrent()), 
            kCFRunLoopDefaultMode)

    def py_matching_callback(self, context, result, sender, device):
        d = HIDDevice.get_device(c_void_p(device))
        if d not in self.devices:
            self.devices.add(d)
            for x in self.matching_observers:
                if hasattr(x, 'device_discovered'):
                    x.device_discovered(d)

    def register_matching_callback(self):
        self.matching_callback = HIDManagerCallback(self.py_matching_callback)
        iokit.IOHIDManagerRegisterDeviceMatchingCallback(
            self.managerRef,
            self.matching_callback,
            None)

######################################################################
# Pyglet interface to HID

from base import Device, Control, AbsoluteAxis, RelativeAxis, Button
from base import Joystick, AppleRemote
from base import DeviceExclusiveException

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
    def __init__(self, display, device, manager):
        super(PygletDevice, self).__init__(display, device.product)
        self.device = device
        self.device_identifier = self.device.unique_identifier()
        self.device.add_value_observer(self)
        self.device.add_removal_observer(self)
        manager.matching_observers.add(self)
        self._create_controls()
        self._is_open = False
        self._is_exclusive = False
    
    def open(self, window=None, exclusive=False):
        super(PygletDevice, self).open(window, exclusive)
        self.device.open(exclusive)
        self.device.schedule_with_run_loop()
        self._is_open = True
        self._is_exclusive = exclusive
        self._set_initial_control_values()

    def close(self):
        super(PygletDevice, self).close()
        self.device.close()
        self._is_open = False

    def get_controls(self):
        return self._controls.values()

    def device_removed(self, hid_device):
        # Called by device when it is unplugged.
        # Set device to None, but Keep self._controls around
        # in case device is plugged back in.
        self.device = None

    def device_discovered(self, hid_device):
        # Called by HID manager when new device is found.
        # If our device was disconnected, reconnect when it is plugged back in.
        if not self.device and self.device_identifier == hid_device.unique_identifier():
            self.device = hid_device
            self.device.add_value_observer(self)
            self.device.add_removal_observer(self)
            # Don't need to recreate controls since this is same device.
            # They are indexed by cookie, which is constant.
            if self._is_open: 
                self.device.open(self._is_exclusive)
                self.device.schedule_with_run_loop()
        
    def device_value_changed(self, hid_device, hid_value):
        # Called by device when input value changes.
        control = self._controls[hid_value.element.cookie]
        control._set_value(hid_value.intvalue)

    def _create_controls(self):
        self._controls = {}
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
            self._controls[control._cookie] = control

    def _set_initial_control_values(self):
        # Must be called AFTER the device has been opened.
        for element in self.device.elements:
            if element.cookie in self._controls:
                control = self._controls[element.cookie]
                hid_value = self.device.get_value(element)
                if hid_value:
                    control._set_value(hid_value.intvalue)

######################################################################

_manager = HIDManager()

def get_devices(display=None):
    return [ PygletDevice(display, device, _manager) for device in _manager.devices ]

def get_joysticks(display=None):
    return [ Joystick(PygletDevice(display, device, _manager)) for device in _manager.devices
             if device.is_joystick() or device.is_gamepad() or device.is_multi_axis() ]

def get_apple_remote(display=None):
    for device in _manager.devices:
        if device.product == 'Apple IR':
            return AppleRemote(PygletDevice(display, device, _manager))

