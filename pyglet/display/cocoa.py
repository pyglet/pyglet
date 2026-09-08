from __future__ import annotations

from ctypes import byref, c_uint32, c_void_p

from pyglet.libs.darwin.cocoapy import (
    CGDirectDisplayID,
    ObjCClass,
    cf,
    cfarray_to_list,
    cfstring_to_string,
    get_NSString,
    quartz,
)

from .base import Display, Screen, ScreenMode

NSScreen = ObjCClass('NSScreen')


class CocoaDisplay(Display):

    def get_screens(self):
        maxDisplays = 256
        activeDisplays = (CGDirectDisplayID * maxDisplays)()
        count = c_uint32()
        quartz.CGGetActiveDisplayList(maxDisplays, activeDisplays, byref(count))
        return [CocoaScreen(self, displayID) for displayID in list(activeDisplays)[: count.value]]

    def get_default_screen(self) -> Screen:
        main_id = quartz.CGMainDisplayID()

        screens = self.get_screens()
        for screen in screens:
            if screen.get_display_id() == main_id:
                return screen

        return screens[0]

class CocoaScreen(Screen):

    def __init__(self, display, displayID):
        bounds = quartz.CGDisplayBounds(displayID)
        x, y = bounds.origin.x, bounds.origin.y
        width, height = bounds.size.width, bounds.size.height
        super().__init__(display, int(x), int(y), int(width), int(height))
        self._cg_display_id = displayID
        self._unit_number = quartz.CGDisplayUnitNumber(displayID)
        # Save the default mode so we can restore to it.
        self._default_mode = self.get_mode()
        self._friendly_name = "Unknown"
        ns_screen = self.get_nsscreen()
        if ns_screen is not None:
            screen_name = ns_screen.localizedName()
            if screen_name:
                self._friendly_name = cfstring_to_string(screen_name)

    def get_nsscreen(self):
        """Return the current NSScreen associated with this display framebuffer."""
        # Get a list of all currently active NSScreens and then search through
        # them until we find one that matches our CGDisplayID.
        screen_array = NSScreen.screens()
        count = screen_array.count()
        for i in range(count):
            nsscreen = screen_array.objectAtIndex_(i)
            screen_info = nsscreen.deviceDescription()
            screen_number = screen_info.objectForKey_(get_NSString('NSScreenNumber'))
            display_id = screen_number.unsignedIntValue()
            if display_id == self._cg_display_id:
                return nsscreen

            # A GPU switch can replace a CGDirectDisplayID while the underlying
            # framebuffer remains the same. Match its logical unit as a fallback.
            if quartz.CGDisplayUnitNumber(display_id) == self._unit_number:
                return nsscreen
        return None

    def get_dpi(self) -> int:
        # Keep pyglet's existing 96-DPI font basis until font sizing is
        # updated to use AppKit's nominal 72 points per inch.
        return round(96 * self.get_scale())

    def get_scale(self) -> float:
        ns_screen = self.get_nsscreen()
        return ns_screen.backingScaleFactor() if ns_screen is not None else 1.0

    def get_modes(self):
        cgmodes = c_void_p(quartz.CGDisplayCopyAllDisplayModes(self._cg_display_id, None))
        modes = [CocoaScreenMode(self, cgmode) for cgmode in cfarray_to_list(cgmodes)]
        cf.CFRelease(cgmodes)
        return modes

    def get_mode(self):
        cgmode = c_void_p(quartz.CGDisplayCopyDisplayMode(self._cg_display_id))
        mode = CocoaScreenMode(self, cgmode)
        quartz.CGDisplayModeRelease(cgmode)
        return mode

    def set_mode(self, mode):
        assert mode.screen is self
        quartz.CGDisplaySetDisplayMode(self._cg_display_id, mode.cgmode, None)
        self.width = mode.width
        self.height = mode.height

    def restore_mode(self):
        match_attrs = ['width', 'height', 'depth', 'rate']
        current_mode = self.get_mode()
        if all(getattr(current_mode, attr) == getattr(self._default_mode, attr) for
               attr in match_attrs):
            # Already in default mode
            return
        quartz.CGDisplaySetDisplayMode(self._cg_display_id, self._default_mode.cgmode, None)
        self.width = self._default_mode.width
        self.height = self._default_mode.height

    def get_display_id(self) -> str:
        """Get a unique identifier for the screen."""
        return self._cg_display_id

    def get_monitor_name(self) -> str:
        """Get a friendly name, if available.

        For example, the make and model of the screen: Dell S2716DG
        """
        return self._friendly_name

class CocoaScreenMode(ScreenMode):

    def __init__(self, screen, cgmode):
        super().__init__(screen)
        quartz.CGDisplayModeRetain(cgmode)
        self.cgmode = cgmode
        self.width = int(quartz.CGDisplayModeGetWidth(cgmode))
        self.height = int(quartz.CGDisplayModeGetHeight(cgmode))
        self.depth = self.getBitsPerPixel(cgmode)
        self.rate = quartz.CGDisplayModeGetRefreshRate(cgmode)

    def __del__(self):
        quartz.CGDisplayModeRelease(self.cgmode)
        self.cgmode = None

    def getBitsPerPixel(self, cgmode):
        # from /System/Library/Frameworks/IOKit.framework/Headers/graphics/IOGraphicsTypes.h
        IO8BitIndexedPixels = "PPPPPPPP"
        IO16BitDirectPixels = "-RRRRRGGGGGBBBBB"
        IO32BitDirectPixels = "--------RRRRRRRRGGGGGGGGBBBBBBBB"

        cfstring = c_void_p(quartz.CGDisplayModeCopyPixelEncoding(cgmode))
        pixelEncoding = cfstring_to_string(cfstring)
        cf.CFRelease(cfstring)

        if pixelEncoding == IO8BitIndexedPixels: return 8
        if pixelEncoding == IO16BitDirectPixels: return 16
        if pixelEncoding == IO32BitDirectPixels: return 32
        return 0
