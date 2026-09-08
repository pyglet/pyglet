"""macOS Quartz Display Services."""
from ctypes import POINTER, c_bool, c_double, c_int32, c_size_t, c_uint32, c_void_p

import pyglet.lib

from .cocoatypes import CGPoint, CGRect, CGSize
from .lib_coregraphics import CGDirectDisplayID, CGError

quartz = pyglet.lib.load_library(framework='Quartz')

quartz.CGDisplayIDToOpenGLDisplayMask.restype = c_uint32
quartz.CGDisplayIDToOpenGLDisplayMask.argtypes = [c_uint32]

quartz.CGMainDisplayID.restype = CGDirectDisplayID
quartz.CGMainDisplayID.argtypes = []

quartz.CGShieldingWindowLevel.restype = c_int32
quartz.CGShieldingWindowLevel.argtypes = []

quartz.CGCursorIsVisible.restype = c_bool

quartz.CGDisplayCopyAllDisplayModes.restype = c_void_p
quartz.CGDisplayCopyAllDisplayModes.argtypes = [CGDirectDisplayID, c_void_p]

quartz.CGDisplaySetDisplayMode.restype = CGError
quartz.CGDisplaySetDisplayMode.argtypes = [CGDirectDisplayID, c_void_p, c_void_p]

quartz.CGDisplayCapture.restype = CGError
quartz.CGDisplayCapture.argtypes = [CGDirectDisplayID]

quartz.CGDisplayRelease.restype = CGError
quartz.CGDisplayRelease.argtypes = [CGDirectDisplayID]

quartz.CGDisplayCopyDisplayMode.restype = c_void_p
quartz.CGDisplayCopyDisplayMode.argtypes = [CGDirectDisplayID]

quartz.CGDisplayModeGetRefreshRate.restype = c_double
quartz.CGDisplayModeGetRefreshRate.argtypes = [c_void_p]

quartz.CGDisplayScreenSize.restype = CGSize
quartz.CGDisplayScreenSize.argtypes = [CGDirectDisplayID]

quartz.CGDisplayModeRetain.restype = c_void_p
quartz.CGDisplayModeRetain.argtypes = [c_void_p]

quartz.CGDisplayModeRelease.restype = None
quartz.CGDisplayModeRelease.argtypes = [c_void_p]

quartz.CGDisplayModeGetWidth.restype = c_size_t
quartz.CGDisplayModeGetWidth.argtypes = [c_void_p]

quartz.CGDisplayModeGetHeight.restype = c_size_t
quartz.CGDisplayModeGetHeight.argtypes = [c_void_p]

quartz.CGDisplayModeCopyPixelEncoding.restype = c_void_p
quartz.CGDisplayModeCopyPixelEncoding.argtypes = [c_void_p]

quartz.CGGetActiveDisplayList.restype = CGError
quartz.CGGetActiveDisplayList.argtypes = [c_uint32, POINTER(CGDirectDisplayID), POINTER(c_uint32)]

quartz.CGDisplayBounds.restype = CGRect
quartz.CGDisplayBounds.argtypes = [CGDirectDisplayID]

quartz.CGDisplayUnitNumber.restype = c_uint32
quartz.CGDisplayUnitNumber.argtypes = [CGDirectDisplayID]

quartz.CGWarpMouseCursorPosition.restype = CGError
quartz.CGWarpMouseCursorPosition.argtypes = [CGPoint]

quartz.CGDisplayMoveCursorToPoint.restype = CGError
quartz.CGDisplayMoveCursorToPoint.argtypes = [CGDirectDisplayID, CGPoint]

quartz.CGAssociateMouseAndMouseCursorPosition.restype = CGError
quartz.CGAssociateMouseAndMouseCursorPosition.argtypes = [c_bool]
