#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from ctypes import *

class Rect(Structure):
    _fields_ = [
        ('top', c_short),
        ('left', c_short),
        ('bottom', c_short),
        ('right', c_short)
    ]

class Point(Structure):
    _fields_ = [
        ('v', c_short),
        ('h', c_short),
    ]

class CGPoint(Structure):
    _fields_ = [
        ('x', c_float),
        ('y', c_float),
    ]

class CGSize(Structure):
    _fields_ = [
        ('width', c_float),
        ('height', c_float)
    ]

class CGRect(Structure):
    _fields_ = [
        ('origin', CGPoint),
        ('size', CGSize)
    ]
    __slots__ = ['origin', 'size']

CGDirectDisplayID = c_void_p
CGDisplayCount = c_uint32
CGTableCount = c_uint32
CGDisplayCoord = c_int32
CGByteValue = c_ubyte
CGOpenGLDisplayMask = c_uint32
CGRefreshRate = c_double
CGCaptureOptions = c_uint32

GDHandle = c_void_p

HIPoint = CGPoint
HISize = CGSize
HIRect = CGRect

class EventTypeSpec(Structure):
    _fields_ = [
        ('eventClass', c_uint32),
        ('eventKind', c_uint32)
    ]

WindowRef = c_void_p
EventRef = c_void_p
EventTargetRef = c_void_p
EventHandlerRef = c_void_p

CFStringEncoding = c_uint
WindowClass = c_uint32
WindowAttributes = c_uint32
WindowPositionMethod = c_uint32
EventMouseButton = c_uint16
EventMouseWheelAxis = c_uint16

OSType = c_uint32

class MouseTrackingRegionID(Structure):
    _fields_ = [('signature', OSType),
                ('id', c_int32)]

MouseTrackingRef = c_void_p

RgnHandle = c_void_p

class ProcessSerialNumber(Structure):
    _fields_ = [('highLongOfPSN', c_uint32),
                ('lowLongOfPSN', c_uint32)]
