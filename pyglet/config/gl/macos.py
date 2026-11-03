from __future__ import annotations

import platform
from dataclasses import asdict

from ctypes import byref, c_uint32, c_int

from pyglet.config.gl import GLSurfaceConfig
from pyglet.libs.darwin.cocoapy import lib_appkit as appkit
from pyglet.libs.darwin.cocoapy.lib_quartz import quartz

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyglet.config import OpenGLUserConfig
    from pyglet.graphics.api.gl.cocoa.context import CocoaContext
    from pyglet.libs.darwin.cocoapy.runtime import ObjCInstance
    from pyglet.window.apple.cocoa import CocoaWindow
    from pyglet.graphics.api import OpenGLBackend

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
big_sur:        20.0 -> 20.6
monterey:       21.0 -> 21.6
ventura:        22.0 -> 22.6
sonoma:         23.0 -> 23.6
sequoia:        24.0 -> 24.6
tahoe:          25.0 -> 25.6
golden_gate:    27.0 -> 27.2
"""

os_x_release: dict[str, tuple[float, ...]] = {
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
    'monterey': (21,),
    'ventura': (22,),
    'sonoma': (23,),
    'sequoia': (24,),
    'tahoe': (25,),
    'golden_gate': (27,),
}


def os_x_version() -> tuple[int, ...]:
    version = tuple([int(v) for v in platform.release().split('.')])

    # ensure we return a tuple
    if len(version) > 0:
        return version
    return (0,)


_os_x_version = os_x_version()

# Valid names for GL attributes and their corresponding NSOpenGL constant.
_gl_attributes = {
    'double_buffer': appkit.NSOpenGLPFADoubleBuffer,
    'stereo': appkit.NSOpenGLPFAStereo,
    'buffer_size': appkit.NSOpenGLPFAColorSize,
    'sample_buffers': appkit.NSOpenGLPFASampleBuffers,
    'samples': appkit.NSOpenGLPFASamples,
    'aux_buffers': appkit.NSOpenGLPFAAuxBuffers,
    'alpha_size': appkit.NSOpenGLPFAAlphaSize,
    'depth_size': appkit.NSOpenGLPFADepthSize,
    'stencil_size': appkit.NSOpenGLPFAStencilSize,

    # Not exposed by pyglet API (set internally)
    'all_renderers': appkit.NSOpenGLPFAAllRenderers,
    'fullscreen': appkit.NSOpenGLPFAFullScreen,
    'minimum_policy': appkit.NSOpenGLPFAMinimumPolicy,
    'maximum_policy': appkit.NSOpenGLPFAMaximumPolicy,
    'screen_mask': appkit.NSOpenGLPFAScreenMask,

    # Not supported in current pyglet API
    'color_float': appkit.NSOpenGLPFAColorFloat,
    'offscreen': appkit.NSOpenGLPFAOffScreen,
    'sample_alpha': appkit.NSOpenGLPFASampleAlpha,
    'multisample': appkit.NSOpenGLPFAMultisample,
    'supersample': appkit.NSOpenGLPFASupersample,
}

# NSOpenGL constants which do not require a value.
_boolean_gl_attributes = frozenset([
    appkit.NSOpenGLPFAAllRenderers,
    appkit.NSOpenGLPFADoubleBuffer,
    appkit.NSOpenGLPFAStereo,
    appkit.NSOpenGLPFAMinimumPolicy,
    appkit.NSOpenGLPFAMaximumPolicy,
    appkit.NSOpenGLPFAOffScreen,
    appkit.NSOpenGLPFAFullScreen,
    appkit.NSOpenGLPFAColorFloat,
    appkit.NSOpenGLPFAMultisample,
    appkit.NSOpenGLPFASupersample,
    appkit.NSOpenGLPFASampleAlpha,
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


def match(config: OpenGLUserConfig, window: CocoaWindow) -> CocoaGLSurfaceConfig | None:
    # Construct array of attributes for NSOpenGLPixelFormat
    attrs = []
    for name, value in asdict(config).items():
        attr = _gl_attributes.get(name)
        if not attr or not value:
            continue
        attrs.append(attr)
        if attr not in _boolean_gl_attributes:
            attrs.append(int(value))

    # Support for RAGE-II, which is not compliant.
    attrs.append(appkit.NSOpenGLPFAAllRenderers)

    # Force selection policy.
    attrs.append(appkit.NSOpenGLPFAMaximumPolicy)

    # NSOpenGLPFAFullScreen is always supplied so we can switch to and
    # from fullscreen without losing the context.  Also must supply the
    # NSOpenGLPFAScreenMask attribute with appropriate display ID.
    # Note that these attributes aren't necessary to render in fullscreen
    # on Mac OS X 10.6, because there we are simply rendering into a
    # screen sized window.  See:
    # http://developer.apple.com/library/mac/#documentation/GraphicsImaging/Conceptual/OpenGL-MacProgGuide
    # /opengl_fullscreen/opengl_cgl.html%23//apple_ref/doc/uid/TP40001987-CH210-SW6
    # Otherwise, make sure we refer to the correct Profile for OpenGL (Core or
    # Legacy) on Lion and afterwards
    if _os_x_version < os_x_release['snow_leopard']:
        attrs.append(appkit.NSOpenGLPFAFullScreen)
        attrs.append(appkit.NSOpenGLPFAScreenMask)
        attrs.append(quartz.CGDisplayIDToOpenGLDisplayMask(quartz.CGMainDisplayID()))
    elif _os_x_version >= os_x_release['lion']:
        # check for opengl profile
        # This requires OS-X Lion (Darwin 11) or higher
        version = (getattr(config, 'major_version', None) or 3,
                   getattr(config, 'minor_version', None) or 3)

        # tell os-x we want to request a profile
        attrs.append(appkit.NSOpenGLPFAOpenGLProfile)

        # check if we're wanting core or legacy
        # Mavericks (Darwin 13) and up are capable of the Core 4.1 profile,
        # while Lion and up are only capable of Core 3.2
        if version[0] >= 4 and _os_x_version >= os_x_release['mavericks']:
            attrs.append(int(appkit.NSOpenGLProfileVersion4_1Core))
        elif version[0] >= 3:
            attrs.append(int(appkit.NSOpenGLProfileVersion3_2Core))
        else:
            attrs.append(int(appkit.NSOpenGLProfileVersionLegacy))
    # Terminate the list.
    attrs.append(0)

    # Create the pixel format.
    attrs_array_type = c_uint32 * len(attrs)
    attrs_array = attrs_array_type(*attrs)
    from pyglet.graphics.api.gl.cocoa.context import NSOpenGLPixelFormat  # noqa: PLC0415
    pixel_format = NSOpenGLPixelFormat.alloc().initWithAttributes_(attrs_array)

    # Return the match list.
    if pixel_format is None:
        return None

    return CocoaGLSurfaceConfig(window, config, pixel_format)


class CocoaGLSurfaceConfig(GLSurfaceConfig['CocoaWindow']):
    _pixel_format: ObjCInstance | None

    def __init__(self, window: CocoaWindow, config: OpenGLUserConfig, pixel_format: ObjCInstance) -> None:
        super().__init__(window, config, pixel_format)
        self._pixel_format = pixel_format

        # Query values for the attributes of the pixel format, and then set the
        # corresponding attributes of the window config.
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
            self._pixel_format.getValues_forAttribute_forVirtualScreen_(
                byref(vals),
                appkit.NSOpenGLPFAOpenGLProfile,
                0,
            )

            if vals.value == appkit.NSOpenGLProfileVersion4_1Core:
                self.major_version = 4
                self.minor_version = 1
            elif vals.value == appkit.NSOpenGLProfileVersion3_2Core:
                self.major_version = 3
                self.minor_version = 2
            else:
                self.major_version = 2
                self.minor_version = 1

    def create_context(self, opengl_backend: OpenGLBackend, share: CocoaContext | None) -> CocoaContext:
        # Determine the shared NSOpenGLContext.
        from pyglet.graphics.api.gl.cocoa.context import CocoaContext, NSOpenGLContext  # noqa: PLC0415

        if share:
            share_context = share._nscontext  # noqa: SLF001
        else:
            share_context = None

        # Create a new NSOpenGLContext.
        nscontext = NSOpenGLContext.alloc().initWithFormat_shareContext_(
            self._pixel_format,
            share_context)

        if self.config.transparent_framebuffer:
            opaque = c_int(0)
            nscontext.setValues_forParameter_(byref(opaque), appkit.NSOpenGLCPSurfaceOpacity)

        # No longer needed after context creation.
        if self._pixel_format:
            self._pixel_format.release()
            self._pixel_format = None

        return CocoaContext(opengl_backend, self._window, self, nscontext, share)

    def apply_format(self) -> None:
        pass
