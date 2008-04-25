#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes

from pyglet.window.carbon import carbon, _oscheck, _create_cfstring
from pyglet.window.carbon.constants import *

import input
import usage

# non-broken c_void_p
void_p = ctypes.POINTER(ctypes.c_int)

class CFUUIDBytes(ctypes.Structure):
    _fields_ = [('byte%d' % i, ctypes.c_uint8) for i in range(16)]

mach_port_t = void_p
io_iterator_t = void_p
kern_return_t = ctypes.c_int
IOReturn = ctypes.c_uint
CFDictionaryRef = void_p
CFMutableDictionaryRef = void_p
CFArrayRef = void_p
CFUUIDRef = ctypes.POINTER(CFUUIDBytes)
AbsoluteTime = ctypes.c_double
HRESULT = ctypes.c_int
REFIID = CFUUIDBytes

IOHIDElementType = ctypes.c_int
kIOHIDElementTypeInput_Misc        = 1
kIOHIDElementTypeInput_Button      = 2
kIOHIDElementTypeInput_Axis        = 3
kIOHIDElementTypeInput_ScanCodes   = 4
kIOHIDElementTypeOutput            = 129
kIOHIDElementTypeFeature           = 257
kIOHIDElementTypeCollection        = 513

IOHIDElementCookie = ctypes.c_void_p

MACH_PORT_NULL = 0
kIOHIDDeviceKey = "IOHIDDevice"
kIOServicePlane = "IOService"
kIOHIDProductIDKey = "ProductID"
kCFNumberIntType = 9

kIOHIDOptionsTypeSeizeDevice = 1

kIOReturnExclusiveAccess = 0xe00002c5

carbon.CFUUIDGetConstantUUIDWithBytes.restype = CFUUIDRef
kIOHIDDeviceUserClientTypeID = carbon.CFUUIDGetConstantUUIDWithBytes(None, 
    0xFA, 0x12, 0xFA, 0x38, 0x6F, 0x1A, 0x11, 0xD4,
    0xBA, 0x0C, 0x00, 0x05, 0x02, 0x8F, 0x18, 0xD5)
kIOCFPlugInInterfaceID = carbon.CFUUIDGetConstantUUIDWithBytes(None,
    0xC2, 0x44, 0xE8, 0x58, 0x10, 0x9C, 0x11, 0xD4,
    0x91, 0xD4, 0x00, 0x50, 0xE4, 0xC6, 0x42, 0x6F)
kIOHIDDeviceInterfaceID = carbon.CFUUIDGetConstantUUIDWithBytes(None,
    0x78, 0xBD, 0x42, 0x0C, 0x6F, 0x14, 0x11, 0xD4,
    0x94, 0x74, 0x00, 0x05, 0x02, 0x8F, 0x18, 0xD5)

class IOHIDEventStruct(ctypes.Structure):
    _fields_ = (
        ('type', IOHIDElementType),
        ('elementCookie', IOHIDElementCookie),
        ('value', ctypes.c_int32),
        ('timestamp', AbsoluteTime),
        ('longValueSize', ctypes.c_uint32),
        ('longValue', ctypes.c_void_p)
    )

Self = ctypes.c_void_p

class IUnknown(ctypes.Structure):
    _fields_ = (
        ('_reserved', ctypes.c_void_p),
        ('QueryInterface', 
         ctypes.CFUNCTYPE(HRESULT, Self, REFIID, ctypes.c_void_p)),
        ('AddRef',
         ctypes.CFUNCTYPE(ctypes.c_ulong, Self)),
        ('Release',
         ctypes.CFUNCTYPE(ctypes.c_ulong, Self)),
    )

# Most of these function prototypes are not filled in yet because I haven't
# bothered.
class IOHIDDeviceInterface(ctypes.Structure):
    _fields_ = IUnknown._fields_ + (
        ('createAsyncEventSource', ctypes.c_void_p),
        ('getAsyncEventSource', ctypes.c_void_p),
        ('createAsyncPort', ctypes.c_void_p),
        ('getAsyncPort', ctypes.c_void_p),
        ('open', ctypes.CFUNCTYPE(IOReturn,
            Self, ctypes.c_uint32)),
        ('close', ctypes.CFUNCTYPE(IOReturn,
            Self)),
        ('setRemovalCallback', ctypes.c_void_p),
        ('getElementValue', ctypes.CFUNCTYPE(IOReturn,
            Self, IOHIDElementCookie, ctypes.POINTER(IOHIDEventStruct))),
        ('setElementValue', ctypes.c_void_p),
        ('queryElementValue', ctypes.c_void_p),
        ('startAllQueues', ctypes.c_void_p),
        ('stopAllQueues', ctypes.c_void_p),
        ('allocQueue', ctypes.c_void_p),
        ('allocOutputTransaction', ctypes.c_void_p),
        # 1.2.1 (10.2.3)
        ('setReport', ctypes.c_void_p),
        ('getReport', ctypes.c_void_p),
        # 1.2.2 (10.3) 
        ('copyMatchingElements', ctypes.CFUNCTYPE(IOReturn,
            Self, CFDictionaryRef, ctypes.POINTER(CFArrayRef))),
        ('setInterruptReportHandlerCallback', ctypes.c_void_p),
    )

def get_master_port():
    master_port = mach_port_t()
    _oscheck(
        carbon.IOMasterPort(MACH_PORT_NULL, ctypes.byref(master_port))
    )
    return master_port

def get_matching_dictionary():
    carbon.IOServiceMatching.restype = CFMutableDictionaryRef
    matching_dictionary = carbon.IOServiceMatching(kIOHIDDeviceKey)
    return matching_dictionary

def get_existing_devices(master_port, matching_dictionary):
    # Consumes reference to matching_dictionary
    iterator = io_iterator_t()
    _oscheck(
        carbon.IOServiceGetMatchingServices(master_port, 
                                            matching_dictionary,
                                            ctypes.byref(iterator))
    )
    devices = []
    while carbon.IOIteratorIsValid(iterator):
        device = carbon.IOIteratorNext(iterator)
        if not device:
            break
        devices.append(Device(device))
    carbon.IOObjectRelease(iterator)
    return devices

def cfstring_to_string(value_string):
    value_length = carbon.CFStringGetLength(value_string)
    buffer_length = carbon.CFStringGetMaximumSizeForEncoding(
        value_length, kCFStringEncodingUTF8)
    buffer = ctypes.c_buffer(buffer_length + 1)
    result = carbon.CFStringGetCString(value_string, 
                                       buffer, 
                                       len(buffer),
                                       kCFStringEncodingUTF8)
    if not result:
        return
    return buffer.value

def cfnumber_to_int(value):
    result = ctypes.c_int()
    carbon.CFNumberGetValue(value, kCFNumberIntType, ctypes.byref(result))
    return result.value

def cfvalue_to_value(value):
    if not value:
        return None
    value_type = carbon.CFGetTypeID(value)
    if value_type == carbon.CFStringGetTypeID():
        return cfstring_to_string(value)
    elif value_type == carbon.CFNumberGetTypeID():
        return cfnumber_to_int(value)
    else:
        return None

def get_property_value(properties, key):
    key_string = _create_cfstring(key)
    value = ctypes.c_void_p()
    present = carbon.CFDictionaryGetValueIfPresent(properties,
                                                   key_string,
                                                   ctypes.byref(value))
    carbon.CFRelease(key_string)
    if not present:
        return None

    return value
 
def get_property(properties, key):
    return cfvalue_to_value(get_property_value(properties, key))

def dump_properties(properties):
    def func(key, value, context):
        print '%s = %s' % (cfstring_to_string(key), cfvalue_to_value(value))
    CFDictionaryApplierFunction = ctypes.CFUNCTYPE(None, 
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p)
    carbon.CFDictionaryApplyFunction(properties,
        CFDictionaryApplierFunction(func), None)

class Device(object):
    '''
    :IVariables:
        `name` : str
        `manufacturer` : str

    '''
    def __init__(self, generic_device):
        self._init_properties(generic_device)
        self._device = self._get_device_interface(generic_device)
        self.elements = self._get_elements()

        self._open = False

    def _init_properties(self, generic_device):
        properties = CFMutableDictionaryRef()
        _oscheck(
            carbon.IORegistryEntryCreateCFProperties(generic_device,
                                                     ctypes.byref(properties),
                                                     None, 0)
        )

        self.name = get_property(properties, "Product")
        self.manufacturer = get_property(properties, "Manufacturer")

        carbon.CFRelease(properties)

    def _get_device_interface(self, generic_device):
        plug_in_interface = \
            ctypes.POINTER(ctypes.POINTER(IUnknown))()
        score = ctypes.c_int32()
        _oscheck(
            carbon.IOCreatePlugInInterfaceForService(
                generic_device,
                kIOHIDDeviceUserClientTypeID,
                kIOCFPlugInInterfaceID,
                ctypes.byref(plug_in_interface),
                ctypes.byref(score))
        )

        carbon.CFUUIDGetUUIDBytes.restype = CFUUIDBytes
        hid_device_interface = \
            ctypes.POINTER(ctypes.POINTER(IOHIDDeviceInterface))()
        _oscheck(
            plug_in_interface.contents.contents.QueryInterface(
                plug_in_interface,
                carbon.CFUUIDGetUUIDBytes(kIOHIDDeviceInterfaceID),
                ctypes.byref(hid_device_interface))
        )

        plug_in_interface.contents.contents.Release(plug_in_interface)
        
        return hid_device_interface

    def _get_elements(self):
        elements_array = CFArrayRef()
        _oscheck(
            self._device.contents.contents.copyMatchingElements(self._device,
                None, ctypes.byref(elements_array))
        )

        elements = []
        n_elements = carbon.CFArrayGetCount(elements_array)
        for i in range(n_elements):
            properties = carbon.CFArrayGetValueAtIndex(elements_array, i)
            elements.append(DeviceElement(self, properties))

        carbon.CFRelease(elements_array)

        return elements

    def __repr__(self):
        return '%s(name=%r, manufacturer=%r)' % (
            self.__class__.__name__, self.product, self.manufacturer)

    def open(self, exclusive=False):
        flags = 0
        if exclusive:
            flags |= kIOHIDOptionsTypeSeizeDevice
        result = self._device.contents.contents.open(self._device, flags)
        if result == 0:
            self._open = True
            return
        elif result == kIOReturnExclusiveAccess:
            raise input.InputDeviceExclusiveException()

    def close(self):
        if not self._open:
            return

        _oscheck(
            self._device.contents.contents.close(self._device)
        )
        self._open = False

class DeviceElement(object):
    def __init__(self, device, properties):
        self.device = device

        self._cookie = get_property(properties, 'ElementCookie')
        _usage = get_property(properties, 'Usage')
        usage_page = get_property(properties, 'UsagePage')

        self.name = usage.get_element_usage_name(usage_page, _usage)
        self.known = usage.get_element_usage_known(usage_page, _usage)

    def get_value(self):
        event = IOHIDEventStruct()
        self.device._device.contents.contents.getElementValue(
            self.device._device, self._cookie, ctypes.byref(event))
        return event.value

def get_devices():
    return get_existing_devices(get_master_port(), get_matching_dictionary())

