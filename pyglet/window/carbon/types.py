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
    _fields = [
        ('width', c_float),
        ('height', c_float)
    ]

class CGRect(Structure):
    _fields_ = [
        ('origin', CGPoint),
        ('size', CGSize)
    ]

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

CFStringEncoding = c_uint
WindowClass = c_uint32
WindowAttributes = c_uint32
WindowPositionMethod = c_uint32
EventMouseButton = c_uint16
