from ctypes import *

import sys, platform
__LP64__ = (sys.maxint > 2**32)
__i386__ = (platform.machine() == 'i386')

PyObjectEncoding = '{PyObject=@}'

def encoding_for_ctype(vartype):
    typecodes = {c_char:'c', c_int:'i', c_short:'s', c_long:'l', c_longlong:'q',
                 c_ubyte:'C', c_uint:'I', c_ushort:'S', c_ulong:'L', c_ulonglong:'Q',
                 c_float:'f', c_double:'d', c_bool:'B', c_char_p:'*', c_void_p:'@',
                 py_object:PyObjectEncoding}
    return typecodes.get(vartype, '?')

# Note CGBase.h located at
# /System/Library/Frameworks/ApplicationServices.framework/Frameworks/CoreGraphics.framework/Headers/CGBase.h
# defines CGFloat as double if __LP64__, otherwise it's a float.
if __LP64__:
    NSInteger = c_long
    NSUInteger = c_ulong
    CGFloat = c_double
    NSPointEncoding = '{CGPoint=dd}'
    NSSizeEncoding = '{CGSize=dd}'
    NSRectEncoding = '{CGRect={CGPoint=dd}{CGSize=dd}}'
else:
    NSInteger = c_int
    NSUInteger = c_uint
    CGFloat = c_float
    NSPointEncoding = '{_NSPoint=ff}'
    NSSizeEncoding = '{_NSSize=ff}'
    NSRectEncoding = '{_NSRect={_NSPoint=ff}{_NSSize=ff}}'

NSIntegerEncoding = encoding_for_ctype(NSInteger)
NSUIntegerEncoding = encoding_for_ctype(NSUInteger)
CGFloatEncoding = encoding_for_ctype(CGFloat)    

# from /System/Library/Frameworks/Foundation.framework/Headers/NSGeometry.h
class NSPoint(Structure):
    _fields_ = [ ("x", CGFloat), ("y", CGFloat) ]
CGPoint = NSPoint

class NSSize(Structure):
    _fields_ = [ ("width", CGFloat), ("height", CGFloat) ]

class NSRect(Structure):
    _fields_ = [ ("origin", NSPoint), ("size", NSSize) ]
CGRect = NSRect

def NSMakeSize(w, h):
    return NSSize(w, h)

def NSMakeRect(x, y, w, h):
    return NSRect(NSPoint(x, y), NSSize(w, h))

# NSDate.h
NSTimeInterval = c_double

CFIndex = c_long
UniChar = c_ushort
unichar = c_wchar  # (actually defined as c_ushort in NSString.h, but need ctypes to convert properly)
CGGlyph = c_ushort

# CFRange struct defined in CFBase.h
# This replaces the CFRangeMake(LOC, LEN) macro.
class CFRange(Structure):
    _fields_ = [ ("location", CFIndex), ("length", CFIndex) ]

# NSRange.h  (Note, not defined the same as CFRange)
class NSRange(Structure):
    _fields_ = [ ("location", NSUInteger), ("length", NSUInteger) ]

NSZeroPoint = NSPoint(0,0)

