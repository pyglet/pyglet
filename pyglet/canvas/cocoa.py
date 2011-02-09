
'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from pyglet import app
from base import Display, Screen, ScreenMode, Canvas

from pyglet.libs.darwin import *

# NOTE: The display mode code uses methods that are available only with PyObjC 2.3
# The alternative methods available in PyObjC 2.2 are all deprecated in Mac OS X 10.6

from objc import __version__ as pyobjc_version
pyobjc_version = float(pyobjc_version[:3])

class CocoaDisplay(Display):

    def get_screens(self):
        return [CocoaScreen(self, nsscreen) for nsscreen in NSScreen.screens()]

class CocoaScreen(Screen):

    def __init__(self, display, nsscreen):
        (x, y), (width, height) = nsscreen.frame()
        super(CocoaScreen, self).__init__(display, int(x), int(y), int(width), int(height))
        self._nsscreen = nsscreen
        self._cg_display_id = self._get_CGDirectDisplayID()
        # Save the default mode so we can restore to it.
        self._default_mode = self.get_mode()

    def _get_CGDirectDisplayID(self):
        screenInfo = self._nsscreen.deviceDescription()
        return screenInfo.objectForKey_("NSScreenNumber")

    def get_matching_configs(self, template):
        canvas = CocoaCanvas(self.display, self, None)
        return template.match(canvas)

    def get_modes(self):
        if pyobjc_version < 2.3: return []
        mode_list = CGDisplayCopyAllDisplayModes(self._cg_display_id, None)
        return [ CocoaScreenMode(self, cgmode) for cgmode in mode_list ]

    def get_mode(self):
        if pyobjc_version < 2.3: return
        cgmode = CGDisplayCopyDisplayMode(self._cg_display_id)
        return CocoaScreenMode(self, cgmode)

    def set_mode(self, mode): 
        if pyobjc_version < 2.3: return
        assert mode.screen is self
        CGDisplayCapture(self._cg_display_id)
        CGDisplaySetDisplayMode(self._cg_display_id, mode.cgmode, None)
        self.width = mode.width
        self.height = mode.height

    def restore_mode(self):
        if pyobjc_version >= 2.3: 
            CGDisplaySetDisplayMode(self._cg_display_id, self._default_mode.cgmode, None)
        CGDisplayRelease(self._cg_display_id)

    def capture_display(self):
        CGDisplayCapture(self._cg_display_id)

    def release_display(self):
        CGDisplayRelease(self._cg_display_id)


class CocoaScreenMode(ScreenMode):

    def __init__(self, screen, cgmode):
        super(CocoaScreenMode, self).__init__(screen)
        self.cgmode = cgmode
        self.width = int(CGDisplayModeGetWidth(cgmode))
        self.height = int(CGDisplayModeGetHeight(cgmode))
        self.depth = self.getBitsPerPixel(cgmode)
        self.rate = CGDisplayModeGetRefreshRate(cgmode)
        
    def getBitsPerPixel(self, cgmode):
        # from /System/Library/Frameworks/IOKit.framework/Headers/graphics/IOGraphicsTypes.h
        IO8BitIndexedPixels = "PPPPPPPP"
        IO16BitDirectPixels = "-RRRRRGGGGGBBBBB"
        IO32BitDirectPixels = "--------RRRRRRRRGGGGGGGGBBBBBBBB"

        pixelEncoding = CGDisplayModeCopyPixelEncoding(cgmode)

        if pixelEncoding == IO8BitIndexedPixels: return 8
        if pixelEncoding == IO16BitDirectPixels: return 16
        if pixelEncoding == IO32BitDirectPixels: return 32
        return 0

                   
class CocoaCanvas(Canvas):

    def __init__(self, display, screen, nsview):
        super(CocoaCanvas, self).__init__(display)
        self.screen = screen
        self.nsview = nsview
