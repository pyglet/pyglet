from ctypes import *
from ctypes import util

from runtime import send_message, ObjCInstance
from cocoatypes import *

######################################################################

# CORE FOUNDATION

cf = cdll.LoadLibrary(util.find_library('CoreFoundation'))

kCFStringEncodingUTF8 = 0x08000100
CFAllocatorRef = c_void_p
CFStringEncoding = c_uint32

cf.CFStringCreateWithCString.restype = c_void_p
cf.CFStringCreateWithCString.argtypes = [CFAllocatorRef, c_char_p, CFStringEncoding]

cf.CFRelease.restype = c_void_p
cf.CFRelease.argtypes = [c_void_p]

cf.CFStringGetLength.restype = CFIndex
cf.CFStringGetLength.argtypes = [c_void_p]

cf.CFStringGetMaximumSizeForEncoding.restype = CFIndex
cf.CFStringGetMaximumSizeForEncoding.argtypes = [CFIndex, CFStringEncoding]

cf.CFStringGetCString.restype = c_bool
cf.CFStringGetCString.argtypes = [c_void_p, c_char_p, CFIndex, CFStringEncoding]

def CFSTR(string):
    return ObjCInstance(c_void_p(cf.CFStringCreateWithCString(
            None, string.encode('utf8'), kCFStringEncodingUTF8)))

# Other possible names for this method:
# at, ampersat, arobe, apenstaartje (little monkey tail), strudel,
# klammeraffe (spider monkey), little_mouse, arroba, sobachka (doggie)
# malpa (monkey), snabel (trunk), papaki (small duck), afna (monkey),
# kukac (caterpillar).
def get_NSString(string):
    """Autoreleased version of CFSTR"""
    return CFSTR(string).autorelease()

def cfstring_to_string(cfstring):
    length = cf.CFStringGetLength(cfstring)
    size = cf.CFStringGetMaximumSizeForEncoding(length, kCFStringEncodingUTF8)
    buffer = c_buffer(size + 1)
    result = cf.CFStringGetCString(cfstring, buffer, len(buffer), kCFStringEncodingUTF8)
    if result:
        return unicode(buffer.value, 'utf-8')

cf.CFArrayGetValueAtIndex.restype = c_void_p
cf.CFArrayGetValueAtIndex.argtypes = [c_void_p, CFIndex]

def cfarray_to_list(cfarray):
    count = cf.CFArrayGetCount(cfarray)
    return [ c_void_p(cf.CFArrayGetValueAtIndex(cfarray, i))
             for i in range(count) ]

cf.CFDataCreate.restype = c_void_p
cf.CFDataCreate.argtypes = [c_void_p, c_void_p, CFIndex]

cf.CFDictionaryGetValue.restype = c_void_p
cf.CFDictionaryGetValue.argtypes = [c_void_p, c_void_p]

# Helper function to convert CFNumber to a Python float.
kCFNumberFloatType = 12
def cfnumber_to_float(cfnumber):
    result = c_float()
    if cf.CFNumberGetValue(cfnumber, kCFNumberFloatType, byref(result)):
        return result.value

######################################################################

# APPLICATION KIT

# Even though we don't use this directly, it must be loaded so that
# we can find the NSApplication, NSWindow, and NSView classes.
appkit = cdll.LoadLibrary(util.find_library('AppKit'))

NSDefaultRunLoopMode = c_void_p.in_dll(appkit, 'NSDefaultRunLoopMode')
NSEventTrackingRunLoopMode = c_void_p.in_dll(appkit, 'NSEventTrackingRunLoopMode')
NSApplicationDidHideNotification = c_void_p.in_dll(appkit, 'NSApplicationDidHideNotification')
NSApplicationDidUnhideNotification = c_void_p.in_dll(appkit, 'NSApplicationDidUnhideNotification')

# /System/Library/Frameworks/AppKit.framework/Headers/NSEvent.h
NSAnyEventMask = 0xFFFFFFFFL     # NSUIntegerMax

NSKeyDown            = 10
NSKeyUp              = 11
NSFlagsChanged       = 12
NSApplicationDefined = 15

NSAlphaShiftKeyMask         = 1 << 16
NSShiftKeyMask              = 1 << 17
NSControlKeyMask            = 1 << 18
NSAlternateKeyMask          = 1 << 19
NSCommandKeyMask            = 1 << 20
NSNumericPadKeyMask         = 1 << 21
NSHelpKeyMask               = 1 << 22
NSFunctionKeyMask           = 1 << 23

NSInsertFunctionKey   = 0xF727
NSDeleteFunctionKey   = 0xF728
NSHomeFunctionKey     = 0xF729
NSBeginFunctionKey    = 0xF72A
NSEndFunctionKey      = 0xF72B
NSPageUpFunctionKey   = 0xF72C
NSPageDownFunctionKey = 0xF72D

# /System/Library/Frameworks/AppKit.framework/Headers/NSWindow.h
NSBorderlessWindowMask		= 0
NSTitledWindowMask		= 1 << 0
NSClosableWindowMask		= 1 << 1
NSMiniaturizableWindowMask	= 1 << 2
NSResizableWindowMask		= 1 << 3

# /System/Library/Frameworks/AppKit.framework/Headers/NSPanel.h
NSUtilityWindowMask		= 1 << 4

# /System/Library/Frameworks/AppKit.framework/Headers/NSGraphics.h
NSBackingStoreRetained	        = 0
NSBackingStoreNonretained	= 1
NSBackingStoreBuffered	        = 2

# /System/Library/Frameworks/AppKit.framework/Headers/NSTrackingArea.h
NSTrackingMouseEnteredAndExited  = 0x01
NSTrackingMouseMoved             = 0x02
NSTrackingCursorUpdate 		 = 0x04
NSTrackingActiveInActiveApp 	 = 0x40

# /System/Library/Frameworks/AppKit.framework/Headers/NSOpenGL.h
NSOpenGLPFAAllRenderers       =   1   # choose from all available renderers          
NSOpenGLPFADoubleBuffer       =   5   # choose a double buffered pixel format        
NSOpenGLPFAStereo             =   6   # stereo buffering supported                   
NSOpenGLPFAAuxBuffers         =   7   # number of aux buffers                        
NSOpenGLPFAColorSize          =   8   # number of color buffer bits                  
NSOpenGLPFAAlphaSize          =  11   # number of alpha component bits               
NSOpenGLPFADepthSize          =  12   # number of depth buffer bits                  
NSOpenGLPFAStencilSize        =  13   # number of stencil buffer bits                
NSOpenGLPFAAccumSize          =  14   # number of accum buffer bits                  
NSOpenGLPFAMinimumPolicy      =  51   # never choose smaller buffers than requested  
NSOpenGLPFAMaximumPolicy      =  52   # choose largest buffers of type requested     
NSOpenGLPFAOffScreen          =  53   # choose an off-screen capable renderer        
NSOpenGLPFAFullScreen         =  54   # choose a full-screen capable renderer        
NSOpenGLPFASampleBuffers      =  55   # number of multi sample buffers               
NSOpenGLPFASamples            =  56   # number of samples per multi sample buffer    
NSOpenGLPFAAuxDepthStencil    =  57   # each aux buffer has its own depth stencil    
NSOpenGLPFAColorFloat         =  58   # color buffers store floating point pixels    
NSOpenGLPFAMultisample        =  59   # choose multisampling                         
NSOpenGLPFASupersample        =  60   # choose supersampling                         
NSOpenGLPFASampleAlpha        =  61   # request alpha filtering                      
NSOpenGLPFARendererID         =  70   # request renderer by ID                       
NSOpenGLPFASingleRenderer     =  71   # choose a single renderer for all screens     
NSOpenGLPFANoRecovery         =  72   # disable all failure recovery systems         
NSOpenGLPFAAccelerated        =  73   # choose a hardware accelerated renderer       
NSOpenGLPFAClosestPolicy      =  74   # choose the closest color buffer to request   
NSOpenGLPFARobust             =  75   # renderer does not need failure recovery      
NSOpenGLPFABackingStore       =  76   # back buffer contents are valid after swap    
NSOpenGLPFAMPSafe             =  78   # renderer is multi-processor safe             
NSOpenGLPFAWindow             =  80   # can be used to render to an onscreen window  
NSOpenGLPFAMultiScreen        =  81   # single window can span multiple screens      
NSOpenGLPFACompliant          =  83   # renderer is opengl compliant                 
NSOpenGLPFAScreenMask         =  84   # bit mask of supported physical screens       
NSOpenGLPFAPixelBuffer        =  90   # can be used to render to a pbuffer           
NSOpenGLPFARemotePixelBuffer  =  91   # can be used to render offline to a pbuffer   
NSOpenGLPFAAllowOfflineRenderers = 96 # allow use of offline renderers               
NSOpenGLPFAAcceleratedCompute =  97   # choose a hardware accelerated compute device 
NSOpenGLPFAVirtualScreenCount = 128   # number of virtual screens in this format     

NSOpenGLCPSwapInterval        = 222


# /System/Library/Frameworks/ApplicationServices.framework/Frameworks/...
#     CoreGraphics.framework/Headers/CGImage.h
kCGImageAlphaNone                   = 0
kCGImageAlphaPremultipliedLast      = 1
kCGImageAlphaPremultipliedFirst     = 2
kCGImageAlphaLast                   = 3
kCGImageAlphaFirst                  = 4
kCGImageAlphaNoneSkipLast           = 5
kCGImageAlphaNoneSkipFirst          = 6
kCGImageAlphaOnly                   = 7

kCGBitmapAlphaInfoMask              = 0x1F
kCGBitmapFloatComponents            = 1 << 8

kCGBitmapByteOrderMask              = 0x7000
kCGBitmapByteOrderDefault           = 0 << 12
kCGBitmapByteOrder16Little          = 1 << 12
kCGBitmapByteOrder32Little          = 2 << 12
kCGBitmapByteOrder16Big             = 3 << 12
kCGBitmapByteOrder32Big             = 4 << 12

# NSApplication.h
NSApplicationPresentationDefault = 0
NSApplicationPresentationHideDock = 1 << 1
NSApplicationPresentationHideMenuBar = 1 << 3
NSApplicationPresentationDisableProcessSwitching = 1 << 5
NSApplicationPresentationDisableHideApplication = 1 << 8

######################################################################

# QUARTZ / COREGRAPHICS

quartz = cdll.LoadLibrary(util.find_library('quartz'))

CGDirectDisplayID = c_uint32     # CGDirectDisplay.h
CGError = c_int32                # CGError.h

# /System/Library/Frameworks/ApplicationServices.framework/Frameworks/...
#     ImageIO.framework/Headers/CGImageProperties.h
kCGImagePropertyGIFDictionary = c_void_p.in_dll(quartz, 'kCGImagePropertyGIFDictionary')
kCGImagePropertyGIFDelayTime = c_void_p.in_dll(quartz, 'kCGImagePropertyGIFDelayTime')

# /System/Library/Frameworks/ApplicationServices.framework/Frameworks/...
#     CoreGraphics.framework/Headers/CGColorSpace.h
kCGRenderingIntentDefault = 0

quartz.CGDisplayIDToOpenGLDisplayMask.restype = c_uint32
quartz.CGDisplayIDToOpenGLDisplayMask.argtypes = [c_uint32]

quartz.CGMainDisplayID.restype = c_uint32

quartz.CGShieldingWindowLevel.restype = c_int32

quartz.CGCursorIsVisible.restype = c_bool

quartz.CGDisplayCopyAllDisplayModes.restype = c_void_p
quartz.CGDisplayCopyAllDisplayModes.argtypes = [CGDirectDisplayID, c_void_p]

quartz.CGDisplayModeGetRefreshRate.restype = c_double
quartz.CGDisplayModeGetRefreshRate.argtypes = [c_void_p]

quartz.CGDisplayModeCopyPixelEncoding.restype = c_void_p
quartz.CGDisplayModeCopyPixelEncoding.argtypes = [c_void_p]

quartz.CGGetActiveDisplayList.restype = CGError
quartz.CGGetActiveDisplayList.argtypes = [c_uint32, POINTER(CGDirectDisplayID), POINTER(c_uint32)]

quartz.CGDisplayBounds.restype = CGRect
quartz.CGDisplayBounds.argtypes = [CGDirectDisplayID]

quartz.CGImageSourceCreateWithData.restype = c_void_p
quartz.CGImageSourceCreateWithData.argtypes = [c_void_p, c_void_p]

quartz.CGImageSourceCreateImageAtIndex.restype = c_void_p
quartz.CGImageSourceCreateImageAtIndex.argtypes = [c_void_p, c_size_t, c_void_p]

quartz.CGImageSourceCopyPropertiesAtIndex.restype = c_void_p
quartz.CGImageSourceCopyPropertiesAtIndex.argtypes = [c_void_p, c_size_t, c_void_p]

quartz.CGImageGetDataProvider.restype = c_void_p
quartz.CGImageGetDataProvider.argtypes = [c_void_p]

quartz.CGDataProviderCopyData.restype = c_void_p
quartz.CGDataProviderCopyData.argtypes = [c_void_p]

quartz.CGDataProviderCreateWithCFData.restype = c_void_p
quartz.CGDataProviderCreateWithCFData.argtypes = [c_void_p]

quartz.CGImageCreate.restype = c_void_p
quartz.CGImageCreate.argtypes = [c_size_t, c_size_t, c_size_t, c_size_t, c_size_t, c_void_p, c_uint32, c_void_p, c_void_p, c_bool, c_int]

quartz.CGColorSpaceCreateDeviceRGB.restype = c_void_p

quartz.CGDataProviderRelease.restype = None
quartz.CGDataProviderRelease.argtypes = [c_void_p]

quartz.CGColorSpaceRelease.restype = None
quartz.CGColorSpaceRelease.argtypes = [c_void_p]

quartz.CGWarpMouseCursorPosition.restype = CGError
quartz.CGWarpMouseCursorPosition.argtypes = [CGPoint]

quartz.CGDisplayMoveCursorToPoint.restype = CGError
quartz.CGDisplayMoveCursorToPoint.argtypes = [CGDirectDisplayID, CGPoint]

quartz.CGAssociateMouseAndMouseCursorPosition.restype = CGError
quartz.CGAssociateMouseAndMouseCursorPosition.argtypes = [c_bool]

######################################################################

# FOUNDATION

foundation = cdll.LoadLibrary(util.find_library('Foundation'))
foundation.NSMouseInRect.restype = c_bool
foundation.NSMouseInRect.argtypes = [NSPoint, NSRect, c_bool]
