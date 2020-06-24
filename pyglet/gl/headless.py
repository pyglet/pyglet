# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2008 Alex Holkner
# Copyright (c) 2008-2020 pyglet contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

import warnings
from ctypes import *

from .base import Config, CanvasConfig, Context
from pyglet.gl import egl
from pyglet.gl.egl import *


class EGLConfig(Config):

    _attribute_names = [
        'double_buffer',
        'stereo',
        'buffer_size',
        'aux_buffers',
        'sample_buffers',
        'samples',
        'red_size',
        'green_size',
        'blue_size',
        'alpha_size',
        'depth_size',
        'stencil_size',
        'accum_red_size',
        'accum_green_size',
        'accum_blue_size',
        'accum_alpha_size',
        'major_version',
        'minor_version',
        'forward_compatible',
        'debug'
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Choose a config:
        config_attribs = (EGL_SURFACE_TYPE, EGL_PBUFFER_BIT,
                          EGL_BLUE_SIZE, self.blue_size or 0,
                          EGL_GREEN_SIZE, self.green_size or 0,
                          EGL_RED_SIZE, self.red_size or 0,
                          EGL_DEPTH_SIZE, self.depth_size or 0,
                          EGL_RENDERABLE_TYPE, EGL_OPENGL_BIT,
                          EGL_CONTEXT_MAJOR_VERSION, self.major_version or 2,
                          EGL_CONTEXT_MINOR_VERSION, self.minor_version or 0,
                          EGL_NONE)

        self._config_attrib_array = (egl.EGLint * len(config_attribs))(*config_attribs)
        self._egl_config = egl.EGLConfig()

        # egl.eglChooseConfig(display_connection, config_attrib_array, egl_config, 1, num_configs)

    def match(self, canvas):
        pass


class HeadlessCanvasConfig(CanvasConfig):
    def match(self, canvas):
        pass

    def compatible(self, canvas):
        pass

    def create_context(self, share):
        pass


class HeadlessContext(Context):
    pass
