from ctypes import c_void_p

import pyglet.lib

# Even though we don't use this directly, it must be loaded so that
# we can find the NSApplication, NSWindow, and NSView classes.
appkit = pyglet.lib.load_library(framework='AppKit')

NSDefaultRunLoopMode = c_void_p.in_dll(appkit, 'NSDefaultRunLoopMode')
NSEventTrackingRunLoopMode = c_void_p.in_dll(appkit, 'NSEventTrackingRunLoopMode')
NSApplicationDidHideNotification = c_void_p.in_dll(appkit, 'NSApplicationDidHideNotification')
NSApplicationDidUnhideNotification = c_void_p.in_dll(appkit, 'NSApplicationDidUnhideNotification')
NSApplicationDidUpdateNotification = c_void_p.in_dll(appkit, 'NSApplicationDidUpdateNotification')
NSPasteboardURLReadingFileURLsOnlyKey = c_void_p.in_dll(appkit, 'NSPasteboardURLReadingFileURLsOnlyKey')
NSPasteboardTypeURL = c_void_p.in_dll(appkit, 'NSPasteboardTypeURL')
NSPasteboardTypeString = c_void_p.in_dll(appkit, 'NSPasteboardTypeString')
NSDeviceSize = c_void_p.in_dll(appkit, 'NSDeviceSize')
NSDeviceResolution = c_void_p.in_dll(appkit, 'NSDeviceResolution')


######################################################################

# APPLICATION KIT

NSDragOperationGeneric = 4

NSStatusWindowLevel = 25
NSMainMenuWindowLevel = 24
NSNormalWindowLevel = 0


# /System/Library/Frameworks/AppKit.framework/Headers/NSEvent.h
NSAnyEventMask = 0xFFFFFFFF     # NSUIntegerMax

NSKeyDown            = 10
NSKeyUp              = 11
NSFlagsChanged       = 12
NSApplicationDefined = 15

# Undocumented left/right modifier masks found by experimentation:
NSLeftShiftKeyMask = 1 << 1
NSRightShiftKeyMask = 1 << 2
NSLeftControlKeyMask = 1 << 0
NSRightControlKeyMask = 1 << 13
NSLeftAlternateKeyMask = 1 << 5
NSRightAlternateKeyMask = 1 << 6
NSLeftCommandKeyMask = 1 << 3
NSRightCommandKeyMask = 1 << 4


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
NSTrackingInVisibleRect             = 0x200    # If set, tracking occurs in visibleRect of view and rect is ignored

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
NSOpenGLPFAOpenGLProfile      =  99   # specify an OpenGL Profile to use
NSOpenGLPFAVirtualScreenCount = 128   # number of virtual screens in this format

NSOpenGLProfileVersionLegacy  = 0x1000    # choose a Legacy/Pre-OpenGL 3.0 Implementation
NSOpenGLProfileVersion3_2Core = 0x3200    # choose an OpenGL 3.2 Core Implementation
NSOpenGLProfileVersion4_1Core = 0x4100    # choose an OpenGL 4.1 Core Implementation

NSOpenGLCPSwapInterval        = 222
NSOpenGLCPSurfaceOpacity      = 236

# NSApplication.h
NSApplicationPresentationDefault = 0
NSApplicationPresentationHideDock = 1 << 1
NSApplicationPresentationHideMenuBar = 1 << 3
NSApplicationPresentationDisableProcessSwitching = 1 << 5
NSApplicationPresentationDisableHideApplication = 1 << 8

# NSRunningApplication.h
NSApplicationActivationPolicyRegular = 0
NSApplicationActivationPolicyAccessory = 1
NSApplicationActivationPolicyProhibited = 2
NSApplicationActivateIgnoringOtherApps = 1 << 1
