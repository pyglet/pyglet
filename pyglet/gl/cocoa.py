#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

from pyglet.gl.base import Config, CanvasConfig, Context

from pyglet.libs.darwin import *
from pyglet.gl import ContextException
from pyglet.gl import gl
from pyglet.gl import agl

from pyglet.canvas.cocoa import CocoaCanvas


_gl_attributes = {
    'double_buffer': NSOpenGLPFADoubleBuffer,
    'stereo': NSOpenGLPFAStereo,
    #'buffer_size': agl.AGL_BUFFER_SIZE, 
    'sample_buffers': NSOpenGLPFASampleBuffers,
    'samples': NSOpenGLPFASamples,
    'aux_buffers': NSOpenGLPFAAuxBuffers,
    #'red_size': agl.AGL_RED_SIZE,
    #'green_size': agl.AGL_GREEN_SIZE,
    #'blue_size': agl.AGL_BLUE_SIZE,
    'alpha_size': NSOpenGLPFAAlphaSize,
    'depth_size': NSOpenGLPFADepthSize,
    'stencil_size': NSOpenGLPFAStencilSize,
    #'accum_red_size': agl.AGL_ACCUM_RED_SIZE,
    #'accum_green_size': agl.AGL_ACCUM_GREEN_SIZE,
    #'accum_blue_size': agl.AGL_ACCUM_BLUE_SIZE,
    #'accum_alpha_size': agl.AGL_ACCUM_ALPHA_SIZE,

    # Not exposed by pyglet API (set internally)
    'all_renderers': NSOpenGLPFAAllRenderers,
    'fullscreen': NSOpenGLPFAFullScreen,
    'minimum_policy': NSOpenGLPFAMinimumPolicy,
    'maximum_policy': NSOpenGLPFAMaximumPolicy,
    'screen_mask' : NSOpenGLPFAScreenMask,

    # Not supported in current pyglet API
    'color_float': NSOpenGLPFAColorFloat,
    'offscreen': NSOpenGLPFAOffScreen,
    'sample_alpha': NSOpenGLPFASampleAlpha,
    'multisample': NSOpenGLPFAMultisample,
    'supersample': NSOpenGLPFASupersample,
}


_boolean_gl_attributes = frozenset([
    NSOpenGLPFAAllRenderers, 
    NSOpenGLPFADoubleBuffer,
    NSOpenGLPFAStereo,
    NSOpenGLPFAMinimumPolicy,
    NSOpenGLPFAMaximumPolicy,
    NSOpenGLPFAOffScreen,
    NSOpenGLPFAFullScreen,
    NSOpenGLPFAColorFloat,
    NSOpenGLPFAMultisample,
    NSOpenGLPFASupersample,
    NSOpenGLPFASampleAlpha,
])


class CocoaConfig(Config):

    def match(self, canvas):

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
        attrs.append(NSOpenGLPFAAllRenderers)

        # Force selection policy.
        attrs.append(NSOpenGLPFAMaximumPolicy)

        # NSOpenGLPFAFullScreen is always supplied so we can switch to and
        # from fullscreen without losing the context.
        attrs.append(NSOpenGLPFAFullScreen)
        attrs.append(NSOpenGLPFAScreenMask)
        
        # Horrible breakage if double buffer not enabled.
        attrs.append(NSOpenGLPFADoubleBuffer)
        
        # Create the pixel format.
        pixel_format = NSOpenGLPixelFormat.alloc().initWithAttributes_(attrs)
        
        # Return the match list.
        if pixel_format is None:
            return []
        else:
            return [CocoaCanvasConfig(canvas, self, pixel_format)]


class CocoaCanvasConfig(CanvasConfig):

    def __init__(self, canvas, config, pixel_format):
        super(CocoaCanvasConfig, self).__init__(canvas, config)
        self._pixel_format = pixel_format

        for name, attr in _gl_attributes.items():
            # Acquire and set values.
            pass
 
    def create_context(self, share):

        # Determine the shared NSOpenGLContext.
        if share is None:
            share_context = None
        else:
            share_context = share._ns_context

        # Create a new NSOpenGLContext.
        ns_context = NSOpenGLContext.alloc()
        ns_context.initWithFormat_shareContext_(
                self._pixel_format,
                share_context,)

        return CocoaContext(self, share, ns_context)

    def compatible(self, canvas):
        return isinstance(canvas, CocoaCanvas)


class CocoaContext(Context):

    def __init__(self, config, share, ns_context):
        super(CocoaContext, self).__init__(config, share)
        self._ns_context = ns_context

    def set_current(self):
        self._ns_context.makeCurrentContext()
        super(CocoaContext, self).set_current()
