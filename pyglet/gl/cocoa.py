from __future__ import annotations

import platform
from ctypes import byref, c_int, c_uint32

from pyglet.canvas.cocoa import CocoaCanvas
from pyglet.gl import ContextException
from pyglet.gl.base import CanvasConfig, Config, Context
from pyglet.libs.darwin import cocoapy, quartz

NSOpenGLPixelFormat = cocoapy.ObjCClass('NSOpenGLPixelFormat')
NSOpenGLContext = cocoapy.ObjCClass('NSOpenGLContext')

# Version info, needed as OpenGL different Lion and onward
"""Version is based on Darwin kernel, not OS-X version.
OS-X / Darwin version history
http://en.wikipedia.org/wiki/Darwin_(operating_system)#Release_history
pre-release:    0.1, 0.2, 1.0, 1.1,
kodiak:         1.2.1,
cheetah:        1.3.1,
puma:           1.4.1, 5.1 -> 5.5
jaguar:         6.0.1 -> 6.8
panther:        7.0 -> 7.9
tiger:          8.0 -> 8.11
leopard:        9.0 -> 9.8
snow_leopard:   10.0 -> 10.8
lion:           11.0 -> 11.4
mountain_lion:  12.0 -> 12.5
mavericks:      13.0 -> 13.4
yosemite:       14.0 -> 14.5
el_capitan:     15.0 -> 15.6
sierra:         16.0 -> 16.6
high_sierra:    17.0 -> 17.7
mojave:         18.0 -> 18.2
catalina:       19.0 -> 19.6
big_sur:        20.0 ->
"""
os_x_release: dict[str, tuple[float] | tuple[float, float] | tuple[float, float, float]] = {
    'pre-release': (0, 1),
    'kodiak': (1, 2, 1),
    'cheetah': (1, 3, 1),
    'puma': (1, 4.1),
    'jaguar': (6, 0, 1),
    'panther': (7,),
    'tiger': (8,),
    'leopard': (9,),
    'snow_leopard': (10,),
    'lion': (11,),
    'mountain_lion': (12,),
    'mavericks': (13,),
    'yosemite': (14,),
    'el_capitan': (15,),
    'sierra': (16,),
    'high_sierra': (17,),
    'mojave': (18,),
    'catalina': (19,),
    'big_sur': (20,),
}


def os_x_version() -> tuple[int, ...]:  # noqa: D103
    version = tuple([int(v) for v in platform.release().split('.')])

    # ensure we return a tuple
    if len(version) > 0:
        return version
    return (version,)


_os_x_version = os_x_version()

# Valid names for GL attributes and their corresponding NSOpenGL constant.
_gl_attributes = {
    'double_buffer': cocoapy.NSOpenGLPFADoubleBuffer,
    'stereo': cocoapy.NSOpenGLPFAStereo,
    'buffer_size': cocoapy.NSOpenGLPFAColorSize,
    'sample_buffers': cocoapy.NSOpenGLPFASampleBuffers,
    'samples': cocoapy.NSOpenGLPFASamples,
    'aux_buffers': cocoapy.NSOpenGLPFAAuxBuffers,
    'alpha_size': cocoapy.NSOpenGLPFAAlphaSize,
    'depth_size': cocoapy.NSOpenGLPFADepthSize,
    'stencil_size': cocoapy.NSOpenGLPFAStencilSize,

    # Not exposed by pyglet API (set internally)
    'all_renderers': cocoapy.NSOpenGLPFAAllRenderers,
    'fullscreen': cocoapy.NSOpenGLPFAFullScreen,
    'minimum_policy': cocoapy.NSOpenGLPFAMinimumPolicy,
    'maximum_policy': cocoapy.NSOpenGLPFAMaximumPolicy,
    'screen_mask': cocoapy.NSOpenGLPFAScreenMask,

    # Not supported in current pyglet API
    'color_float': cocoapy.NSOpenGLPFAColorFloat,
    'offscreen': cocoapy.NSOpenGLPFAOffScreen,
    'sample_alpha': cocoapy.NSOpenGLPFASampleAlpha,
    'multisample': cocoapy.NSOpenGLPFAMultisample,
    'supersample': cocoapy.NSOpenGLPFASupersample,
}

# NSOpenGL constants which do not require a value.
_boolean_gl_attributes = frozenset([
    cocoapy.NSOpenGLPFAAllRenderers,
    cocoapy.NSOpenGLPFADoubleBuffer,
    cocoapy.NSOpenGLPFAStereo,
    cocoapy.NSOpenGLPFAMinimumPolicy,
    cocoapy.NSOpenGLPFAMaximumPolicy,
    cocoapy.NSOpenGLPFAOffScreen,
    cocoapy.NSOpenGLPFAFullScreen,
    cocoapy.NSOpenGLPFAColorFloat,
    cocoapy.NSOpenGLPFAMultisample,
    cocoapy.NSOpenGLPFASupersample,
    cocoapy.NSOpenGLPFASampleAlpha,
])

# Attributes for which no NSOpenGLPixelFormatAttribute name exists.
# We could probably compute actual values for these using
# NSOpenGLPFAColorSize / 4 and NSOpenGLFAAccumSize / 4, but I'm not that
# confident I know what I'm doing.
_fake_gl_attributes = {
    'red_size': 0,
    'green_size': 0,
    'blue_size': 0,
    'accum_red_size': 0,
    'accum_green_size': 0,
    'accum_blue_size': 0,
    'accum_alpha_size': 0,
}


class CocoaConfig(Config):  # noqa: D101

    def match(self, canvas: CocoaCanvas) -> list[CocoaCanvasConfig]:
        # Construct array of attributes for NSOpenGLPixelFormat
        attrs = []
        for name, value in self.get_gl_attributes():
            attr = _gl_attributes.get(name)
            if not attr or not value:
                continue
            attrs.append(attr)
            if attr not in _boolean_gl_attributes:
                attrs.append(int(value))

        # Support for RAGE-II, which is not compliant.
        attrs.append(cocoapy.NSOpenGLPFAAllRenderers)

        # Force selection policy.
        attrs.append(cocoapy.NSOpenGLPFAMaximumPolicy)

        # NSOpenGLPFAFullScreen is always supplied so we can switch to and
        # from fullscreen without losing the context.  Also must supply the
        # NSOpenGLPFAScreenMask attribute with appropriate display ID.
        # Note that these attributes aren't necessary to render in fullscreen
        # on Mac OS X 10.6, because there we are simply rendering into a
        # screen sized window.  See:
        # http://developer.apple.com/library/mac/#documentation/GraphicsImaging/Conceptual/OpenGL-MacProgGuide/opengl_fullscreen/opengl_cgl.html%23//apple_ref/doc/uid/TP40001987-CH210-SW6
        # Otherwise, make sure we refer to the correct Profile for OpenGL (Core or
        # Legacy) on Lion and afterwards
        if _os_x_version < os_x_release['snow_leopard']:
            attrs.append(cocoapy.NSOpenGLPFAFullScreen)
            attrs.append(cocoapy.NSOpenGLPFAScreenMask)
            attrs.append(quartz.CGDisplayIDToOpenGLDisplayMask(quartz.CGMainDisplayID()))
        elif _os_x_version >= os_x_release['lion']:
            # check for opengl profile
            # This requires OS-X Lion (Darwin 11) or higher
            version = (getattr(self, 'major_version', None) or 3,
                       getattr(self, 'minor_version', None) or 3)

            # tell os-x we want to request a profile
            attrs.append(cocoapy.NSOpenGLPFAOpenGLProfile)

            # check if we're wanting core or legacy
            # Mavericks (Darwin 13) and up are capable of the Core 4.1 profile,
            # while Lion and up are only capable of Core 3.2
            if version[0] >= 4 and _os_x_version >= os_x_release['mavericks']:
                attrs.append(int(cocoapy.NSOpenGLProfileVersion4_1Core))
            elif version[0] >= 3:
                attrs.append(int(cocoapy.NSOpenGLProfileVersion3_2Core))
            else:
                attrs.append(int(cocoapy.NSOpenGLProfileVersionLegacy))
        # Terminate the list.
        attrs.append(0)

        # Create the pixel format.
        attrsArrayType = c_uint32 * len(attrs)
        attrsArray = attrsArrayType(*attrs)
        pixel_format = NSOpenGLPixelFormat.alloc().initWithAttributes_(attrsArray)

        # Return the match list.
        if pixel_format is None:
            return []

        return [CocoaCanvasConfig(canvas, self, pixel_format)]


class CocoaCanvasConfig(CanvasConfig):  # noqa: D101

    def __init__(self, canvas: CocoaCanvas, config: CocoaConfig, pixel_format: NSOpenGLPixelFormat) -> None:  # noqa: D107
        super().__init__(canvas, config)
        self._pixel_format = pixel_format

        # Query values for the attributes of the pixel format, and then set the
        # corresponding attributes of the canvas config.
        for name, attr in _gl_attributes.items():
            vals = c_int()
            self._pixel_format.getValues_forAttribute_forVirtualScreen_(byref(vals), attr, 0)
            setattr(self, name, vals.value)

        # Set these attributes so that we can run pyglet.info.
        for name, value in _fake_gl_attributes.items():
            setattr(self, name, value)

        # Update the minor/major version from profile if (Mountain)Lion
        if _os_x_version >= os_x_release['lion']:
            vals = c_int()
            profile = self._pixel_format.getValues_forAttribute_forVirtualScreen_(
                byref(vals),
                cocoapy.NSOpenGLPFAOpenGLProfile,
                0,
            )

            if vals.value == cocoapy.NSOpenGLProfileVersion4_1Core:
                self.major_version = 4
                self.minor_version = 1
            elif vals.value == cocoapy.NSOpenGLProfileVersion3_2Core:
                self.major_version = 3
                self.minor_version = 2
            else:
                self.major_version = 2
                self.minor_version = 1

    def create_context(self, share: CocoaContext | None) -> CocoaContext:
        # Determine the shared NSOpenGLContext.
        if share:
            share_context = share._nscontext  # noqa: SLF001
        else:
            share_context = None

        # Create a new NSOpenGLContext.
        nscontext = NSOpenGLContext.alloc().initWithFormat_shareContext_(
            self._pixel_format,
            share_context)

        # No longer needed after context creation.
        if self._pixel_format:
            self._pixel_format.release()
            self._pixel_format = None

        return CocoaContext(self, nscontext, share)

    def compatible(self, canvas: CocoaCanvas) -> bool:
        return isinstance(canvas, CocoaCanvas)


class CocoaContext(Context):  # noqa: D101

    def __init__(self, config: CocoaCanvasConfig, nscontext: NSOpenGLContext, share: CocoaContext | None) -> None:  # noqa: D107
        super().__init__(config, share)
        self.config = config
        self._nscontext = nscontext

    def attach(self, canvas: CocoaCanvas) -> None:
        # See if we want OpenGL 3 in a non-Lion OS
        if _os_x_version < os_x_release['lion']:
            msg = 'OpenGL 3 not supported'
            raise ContextException(msg)

        super().attach(canvas)
        # The NSView instance should be attached to a nondeferred window before calling
        # setView, otherwise you get an "invalid drawable" message.
        self._nscontext.setView_(canvas.nsview)
        self._nscontext.view().setWantsBestResolutionOpenGLSurface_(1)
        self.set_current()

    def detach(self) -> None:
        super().detach()
        self._nscontext.clearDrawable()

    def set_current(self) -> None:
        self._nscontext.makeCurrentContext()
        super().set_current()

    def update_geometry(self) -> None:
        # Need to call this method whenever the context drawable (an NSView)
        # changes size or location.
        self._nscontext.update()

    def set_full_screen(self) -> None:
        self._nscontext.makeCurrentContext()
        self._nscontext.setFullScreen()

    def destroy(self) -> None:
        super().destroy()
        self._nscontext.release()
        self._nscontext = None

    def set_vsync(self, vsync: bool=True) -> None:
        vals = c_int(vsync)
        self._nscontext.setValues_forParameter_(byref(vals), cocoapy.NSOpenGLCPSwapInterval)

    def get_vsync(self) -> bool:
        vals = c_int()
        self._nscontext.getValues_forParameter_(byref(vals), cocoapy.NSOpenGLCPSwapInterval)
        return bool(vals.value)

    def flip(self) -> None:
        self._nscontext.flushBuffer()
