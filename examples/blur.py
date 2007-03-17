import sys
import time
from ctypes import *
from exceptions import *
import random

# disable error checking (python -O) to make this code work :)
from pyglet import options

import pyglet.window
from pyglet import clock
from pyglet.shader import *
from pyglet.ext.model.geometric import *

from pyglet.gl import *
from pyglet.gl import gl_info

c_float4 = c_float * 4


class Failed(Exception): pass

class TextureParam(object):
    max_anisotropy = 0.0

    FILTER   = 1
    LOD      = 2
    MIPMAP   = 4
    WRAP     = 8
    BORDER   = 16
    PRIORITY = 32
    ALL      = 63

    def __init__(self, wrap = GL_REPEAT, filter = GL_LINEAR, min_filter = None):
        if self.max_anisotropy == 0.0 and \
           gl_info.have_extension('GL_EXT_texture_filter_anisotropic'):
            v = c_float()
            glGetFloatv(GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT, byref(v))
            self.max_anisotropy = v.value

        if min_filter is None: min_filter = filter
        self.min_filter = min_filter
        self.mag_filter = filter
        self.min_lod = -1000
        self.max_lod = 1000
        self.min_mipmap = 0
        self.max_mipmap = 1000
        self.wrap_s = wrap
        self.wrap_t = wrap
        self.wrap_r = wrap
        self.priority = 0
        self.anisotropy = 1.0
        self.border_colour = c_float4(0.0, 0.0, 0.0, 0.0)

    def applyToCurrentTexture(self, target, flags = ALL):
      if flags & self.FILTER:
          glTexParameteri(target, GL_TEXTURE_MIN_FILTER, self.min_filter)
          glTexParameteri(target, GL_TEXTURE_MAG_FILTER, self.mag_filter)
          if self.max_anisotropy > 0.0:
              glTexParameterf(target, GL_TEXTURE_MAX_ANISOTROPY_EXT, self.anisotropy)

      if flags & self.LOD:
          glTexParameterf(target, GL_TEXTURE_MIN_LOD, self.min_lod)
          glTexParameterf(target, GL_TEXTURE_MAX_LOD, self.max_lod)

      if flags & self.MIPMAP:
          glTexParameteri(target, GL_TEXTURE_BASE_LEVEL, self.min_mipmap)
          glTexParameteri(target, GL_TEXTURE_MAX_LEVEL, self.max_mipmap)

      if flags & self.WRAP:
          glTexParameteri(target, GL_TEXTURE_WRAP_S, self.wrap_s)
          glTexParameteri(target, GL_TEXTURE_WRAP_T, self.wrap_t)
          glTexParameteri(target, GL_TEXTURE_WRAP_R, self.wrap_r)

      if flags & self.BORDER:
          glTexParameterfv(target, GL_TEXTURE_BORDER_COLOR, self.border_colour)

      if flags & self.PRIORITY:
        glTexParameterf(target, GL_TEXTURE_PRIORITY, self.priority)


class Surface(object):
    SURF_NONE          = 0
    SURF_COLOUR        = 2
    SURF_DEPTH         = 3
    SURF_STENCIL       = 4
    SURF_DEPTH_STENCIL = 5

    DEFAULTS = {
        SURF_COLOUR:
            (GL_RGBA,                 GL_TEXTURE_2D,       True,  False),
        SURF_DEPTH:
            (GL_DEPTH_COMPONENT24,    GL_RENDERBUFFER_EXT, False, False),
        SURF_STENCIL:
            (GL_STENCIL_INDEX8_EXT,   GL_RENDERBUFFER_EXT, False, False),
        SURF_DEPTH_STENCIL:
            (GL_DEPTH24_STENCIL8_EXT, GL_RENDERBUFFER_EXT, False, False)
    }

    def __init__(self, surface_type = SURF_NONE, gl_fmt = None,
            gl_tgt = None, is_texture = None, is_mipmapped = None,
            params = None):
        self.gl_id = 0

        d = self.DEFAULTS[surface_type]
        if gl_fmt is None: gl_fmt = d[0]
        if gl_tgt is None: gl_tgt = d[1]
        if is_texture is None: is_texture = d[2]
        if is_mipmapped is None: is_mipmapped = d[3]
        if params is None: params = TextureParam()

        self.surface_type = surface_type
        self.gl_fmt = gl_fmt
        self.gl_tgt = gl_tgt
        self.is_texture = is_texture
        self.is_mipmapped = is_mipmapped

        self.params = params

    def bind(self):
        glBindTexture(self.gl_tgt, self.gl_id)

    def enableAndBind(self):
        glEnable(self.gl_tgt)
        glBindTexture(self.gl_tgt, self.gl_id)

    def unbind(self):
        glBindTexture(self.gl_tgt, 0)

    def unbindAndDisable(self):
        glBindTexture(self.gl_tgt, 0)
        glDisable(self.gl_tgt)

    def __del__(self):
        self.destroy()

    # retain a reference to these objects so we can use them during GC
    # cleanup
    def destroy(self, c_uint=c_uint, glDeleteTextures=glDeleteTextures,
            byref=byref, glDeleteRenderbuffersEXT=glDeleteRenderbuffersEXT):
        if self.gl_id == 0: return
        gl_id = c_uint(self.gl_id)
        if self.is_texture:
            glDeleteTextures(1, byref(gl_id))
        else:
            glDeleteRenderbuffersEXT(1, byref(gl_id))
        self.gl_id = 0

    def init(self, w = 0, h = 0, d = 0):
        if self.gl_id > 0: raise self.Failed('already initialised')

        if self.surface_type == self.SURF_NONE: return 0
        if self.surface_type == self.SURF_COLOUR and not self.is_texture:
            raise Failed('bad surface')
        if self.surface_type == self.SURF_STENCIL and self.is_texture:
            raise Failed('bad surface')

        gl_id = c_uint(0)

        if self.is_texture:
            if self.gl_tgt not in (GL_TEXTURE_RECTANGLE_ARB,):
                def _ceil_p2(x):
                    if x == 0: return 0
                    y = 1
                    while y < x: y = y * 2
                    return y

                w, h, d = _ceil_p2(w), _ceil_p2(h), _ceil_p2(d)

            glGenTextures(1, byref(gl_id))
            glBindTexture(self.gl_tgt, gl_id.value)

            glGetError()
            fmt = GL_RGBA
            if self.gl_fmt in (
                GL_DEPTH_COMPONENT16_ARB,
                GL_DEPTH_COMPONENT24_ARB,
                GL_DEPTH_COMPONENT32_ARB,
                GL_TEXTURE_DEPTH_SIZE_ARB,
                GL_DEPTH_TEXTURE_MODE_ARB):
                fmt = GL_DEPTH_COMPONENT

            if self.gl_tgt == GL_TEXTURE_1D:
                print >> sys.stderr, gl_id.value, '=> T(%d)' % (w,)
                glTexImage1D(self.gl_tgt,
                             0,
                             self.gl_fmt,
                             w,
                             0,
                             fmt, GL_BYTE, None)
            elif self.gl_tgt in (GL_TEXTURE_2D, GL_TEXTURE_RECTANGLE_ARB):
                print >> sys.stderr, gl_id.value, '=> T(%d,%d)' % (w,h)
                glTexImage2D(self.gl_tgt,
                             0,
                             self.gl_fmt,
                             w, h,
                             0,
                             fmt, GL_BYTE, None)
            elif self.gl_tgt == GL_TEXTURE_CUBE_MAP_EXT:
                print >> sys.stderr, gl_id.value, '=> C(%d,%d)' % (w,h)
                for i in range(6):
                    glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X_EXT + i,
                                 0,
                                 self.gl_fmt,
                                 w, h,
                                 0,
                                 fmt, GL_BYTE, None)
            elif self.gl_tgt == GL_TEXTURE_3D:
                print >> sys.stderr, gl_id.value, '=> T(%d,%d,%d)' % (w,h,d)
                glTexImage3D(self.gl_tgt,
                             0,
                             self.gl_fmt,
                             w, h, d,
                             0,
                             fmt, GL_BYTE, None)
            else:
                raise Failed('unhandled texture target: ' + hex(self.gl_tgt))
            err = glGetError()
            if err:
                raise Failed('failed to create texture: ' + hex(err))

            if self.gl_tgt == GL_TEXTURE_CUBE_MAP_EXT:
                for i in range(6):
                    if self.is_mipmapped:
                        glGenerateMipmapEXT(GL_TEXTURE_CUBE_MAP_POSITIVE_X_EXT + i)
                    self.params.applyToCurrentTexture(GL_TEXTURE_CUBE_MAP_POSITIVE_X_EXT + i)
                else:
                    if self.is_mipmapped:
                        glGenerateMipmapEXT(self.gl_tgt)
                    self.params.applyToCurrentTexture(self.gl_tgt)

            self.params.applyToCurrentTexture(self.gl_tgt)

            glBindTexture(self.gl_tgt, 0)
        else:
            print >> sys.stderr, gl_id.value, '=> R(%d,%d)' % (w,h)
            glGenRenderbuffersEXT(1, byref(gl_id))
            glBindRenderbufferEXT(GL_RENDERBUFFER_EXT, gl_id)
            glRenderbufferStorageEXT(GL_RENDERBUFFER_EXT, self.gl_fmt, w, h)
            glBindRenderbufferEXT(GL_RENDERBUFFER_EXT, 0)

        if gl_id.value == 0:
            raise Failed('failed to init. glGetError(): ' + str(glGetError()))

        self.gl_id = gl_id.value
        self.width, self.height, self.depth = w, h, d



class FrameBuffer(object):
    bound_fbo = [ 0 ]

    def __init__(self, w, h, *surf):
        self.frame_buffer = 0
        self.width = w
        self.height = h

        self.colour = []
        self.depth = None
        self.stencil = None

        for s in surf: self.add(s)

    def add(self, surf):
        if type(surf) in (tuple, list):
            surf, gl_tgt = surf
        else:
            surf, gl_tgt = surf, surf.gl_tgt

        if not (gl_tgt in (GL_TEXTURE_2D, GL_TEXTURE_RECTANGLE_ARB, GL_RENDERBUFFER_EXT) or
                GL_TEXTURE_CUBE_MAP_POSITIVE_X_EXT <= gl_tgt < GL_TEXTURE_CUBE_MAP_POSITIVE_X_EXT + 6):
            raise Failed('invalid target: ' + hex(gl_tgt))

        if   surf.surface_type == Surface.SURF_COLOUR:
            self.colour.append((surf, gl_tgt))
        elif surf.surface_type == Surface.SURF_DEPTH:
            self.depth = (surf, gl_tgt)
        elif surf.surface_type == Surface.SURF_STENCIL:
            self.stencil = (surf, gl_tgt)
        elif surf.surface_type == Surface.SURF_DEPTH:
            self.depth = (surf, gl_tgt)
        elif surf.surface_type == Surface.SURF_DEPTH_STENCIL:
            self.depth = self.stencil = (surf, gl_tgt)

    def init(self):
        for i in self.colour:
            i[0].init(self.width, self.height)
        if self.depth is not None:
            self.depth[0].init(self.width, self.height)
        if self.stencil is not None:
            self.stencil[0].init(self.width, self.height)

        fbo = c_uint(0)
        glGenFramebuffersEXT(1, byref(fbo))
        self.frame_buffer = fbo.value
        if self.frame_buffer == 0:
            raise Failed('failed to init. glGetError(): ' + str(glGetError()))

    def attach(self, mipmap_level = 0):
        if self.frame_buffer == 0:
            raise Failed('not initialised')

        self.bind()

        R = zip(self.colour, range(GL_COLOR_ATTACHMENT0_EXT,
            GL_COLOR_ATTACHMENT0_EXT + len(self.colour)))
        R.extend(((self.depth, GL_DEPTH_ATTACHMENT_EXT),
            (self.stencil, GL_STENCIL_ATTACHMENT_EXT)))

        for surf_info, attachment in R:
            if surf_info is None: continue
            surf, tgt = surf_info

            if surf.gl_id == 0: continue

            if surf.is_texture:
                print >> sys.stderr, 'ATTACH: T:%d' % (surf.gl_id,)
                glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT,
                    attachment, tgt, surf.gl_id, mipmap_level)
            else:
                print >> sys.stderr, 'ATTACH: R:%d' % (surf.gl_id,)
                glFramebufferRenderbufferEXT(GL_FRAMEBUFFER_EXT,
                    attachment, tgt, surf.gl_id)

        status = glCheckFramebufferStatusEXT(GL_FRAMEBUFFER_EXT)

        if status != GL_FRAMEBUFFER_COMPLETE_EXT:
            raise Failed('attach failed: ' + hex(status))

    def pushBind(self):
        _bind  = FrameBuffer.bound_fbo[-1] != self.frame_buffer
        FrameBuffer.bound_fbo.append(self.frame_buffer)
        if _bind:
            glFlush()
            glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, self.frame_buffer)

    @classmethod
    def popBind(cls):
        if len(FrameBuffer.bound_fbo) > 1:
            fbo = FrameBuffer.bound_fbo.pop()
            if fbo != FrameBuffer.bound_fbo[-1]:
                glFlush()
                glBindFramebufferEXT(GL_FRAMEBUFFER_EXT,
                    FrameBuffer.bound_fbo[-1])

    def bind(self):
        if len(FrameBuffer.bound_fbo) == 1:
            return self.pushBind()

        if FrameBuffer.bound_fbo[-1] != self.frame_buffer:
            glFlush()
            glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, self.frame_buffer)
            FrameBuffer.bound_fbo[-1] = self.frame_buffer

    unbind = popBind

    def colourBuffer(self, i):
        try:
            return self.colour[i][0]
        except:
            return None

    def depthBuffer(self):
        try:
            return self.depth[0]
        except:
            return None

    def stencilBuffer(self):
        try:
            return self.stencil[0]
        except:
            return None

    def __del__(self):
        self.destroy()

    # retain a reference to these objects so we can use them during GC
    # cleanup
    def destroy(self, c_uint=c_uint, byref=byref,
            glDeleteFramebuffersEXT=glDeleteFramebuffersEXT):
        if self.frame_buffer == 0: return
        self.colour = []
        self.depth = None
        self.stencil = None
        if self.frame_buffer != 0:
            fbo = c_uint(self.frame_buffer)
            glDeleteFramebuffersEXT(1, byref(fbo))
        self.frame_buffer = 0


class GaussianFuncs(FragmentShader):
    def __init__(self):
        FragmentShader.__init__(self, "gaussian_rect_funcs_f", """\
vec4 _blur3(in sampler2D tex, in vec2 base, in vec2 offset) {
  return
      0.52201146875401894 * texture2D(tex, base)
    + 0.23899426562299048 * (texture2D(tex, base - offset) + texture2D(tex, base + offset));
}

vec4 _blur5(in sampler2D tex, in vec2 base, in vec2 offset) {
  return
      0.28083404410305668 * texture2D(tex, base)
    + 0.23100778343685141 * (texture2D(tex, base - offset) + texture2D(tex, base + offset))
    + 0.12857519451162022 * (texture2D(tex, base - 2.0*offset) + texture2D(tex, base + 2.0*offset));
}

vec4 _blur7(in sampler2D tex, in vec2 base, in vec2 offset) {
  return
      0.17524014277641392 * texture2D(tex, base)
    + 0.16577007239192226 * (texture2D(tex, base - offset) + texture2D(tex, base + offset))
    + 0.14032133681355632 * (texture2D(tex, base - 2.0*offset) + texture2D(tex, base + 2.0*offset))
    + 0.10628851940631442 * (texture2D(tex, base - 3.0*offset) + texture2D(tex, base + 3.0*offset));
}

vec4 _blur9(in sampler2D tex, in vec2 base, in vec2 offset) {
  return
      0.13465835724954514  * texture2D(tex, base)
    + 0.13051535514624768  * (texture2D(tex, base - offset) + texture2D(tex, base + offset))
    + 0.11883558317985349  * (texture2D(tex, base - 2.0*offset) + texture2D(tex, base + 2.0*offset))
    + 0.1016454607907402   * (texture2D(tex, base - 3.0*offset) + texture2D(tex, base + 3.0*offset))
    + 0.081674422258386087 * (texture2D(tex, base - 4.0*offset) + texture2D(tex, base + 4.0*offset));
}

vec4 _blur11(in sampler2D tex, in vec2 base, in vec2 offset) {
  return
      0.1093789154396443   * texture2D(tex, base)
    + 0.1072130678016711   * (texture2D(tex, base - offset) + texture2D(tex, base + offset))
    + 0.10096946479237721  * (texture2D(tex, base - 2.0*offset) + texture2D(tex, base + 2.0*offset))
    + 0.091360949823207332 * (texture2D(tex, base - 3.0*offset) + texture2D(tex, base + 3.0*offset))
    + 0.079425394122662363 * (texture2D(tex, base - 4.0*offset) + texture2D(tex, base + 4.0*offset))
    + 0.066341665740259792 * (texture2D(tex, base - 5.0*offset) + texture2D(tex, base + 5.0*offset));
}

vec4 _blur3_r(in sampler2DRect tex, in vec2 base, in vec2 offset) {
  return
      0.52201146875401894 * texture2DRect(tex, base)
    + 0.23899426562299048 * (texture2DRect(tex, base - offset) + texture2DRect(tex, base + offset));
}

vec4 _blur5_r(in sampler2DRect tex, in vec2 base, in vec2 offset) {
  return
      0.28083404410305668 * texture2DRect(tex, base)
    + 0.23100778343685141 * (texture2DRect(tex, base - offset) + texture2DRect(tex, base + offset))
    + 0.12857519451162022 * (texture2DRect(tex, base - 2.0*offset) + texture2DRect(tex, base + 2.0*offset));
}

vec4 _blur7_r(in sampler2DRect tex, in vec2 base, in vec2 offset) {
  return
      0.17524014277641392 * texture2DRect(tex, base)
    + 0.16577007239192226 * (texture2DRect(tex, base - offset) + texture2DRect(tex, base + offset))
    + 0.14032133681355632 * (texture2DRect(tex, base - 2.0*offset) + texture2DRect(tex, base + 2.0*offset))
    + 0.10628851940631442 * (texture2DRect(tex, base - 3.0*offset) + texture2DRect(tex, base + 3.0*offset));
}

vec4 _blur9_r(in sampler2DRect tex, in vec2 base, in vec2 offset) {
  return
      0.13465835724954514  * texture2DRect(tex, base)
    + 0.13051535514624768  * (texture2DRect(tex, base - offset) + texture2DRect(tex, base + offset))
    + 0.11883558317985349  * (texture2DRect(tex, base - 2.0*offset) + texture2DRect(tex, base + 2.0*offset))
    + 0.1016454607907402   * (texture2DRect(tex, base - 3.0*offset) + texture2DRect(tex, base + 3.0*offset))
    + 0.081674422258386087 * (texture2DRect(tex, base - 4.0*offset) + texture2DRect(tex, base + 4.0*offset));
}

vec4 _blur11_r(in sampler2DRect tex, in vec2 base, in vec2 offset) {
  return
      0.1093789154396443   * texture2DRect(tex, base)
    + 0.1072130678016711   * (texture2DRect(tex, base - offset) + texture2DRect(tex, base + offset))
    + 0.10096946479237721  * (texture2DRect(tex, base - 2.0*offset) + texture2DRect(tex, base + 2.0*offset))
    + 0.091360949823207332 * (texture2DRect(tex, base - 3.0*offset) + texture2DRect(tex, base + 3.0*offset))
    + 0.079425394122662363 * (texture2DRect(tex, base - 4.0*offset) + texture2DRect(tex, base + 4.0*offset))
    + 0.066341665740259792 * (texture2DRect(tex, base - 5.0*offset) + texture2DRect(tex, base + 5.0*offset));
}
""")

class RenderDOFPass1(ShaderProgram):
    def __init__(self):
        ShaderProgram.__init__(self)
        self.setShader(FragmentShader("dof_f", """\
uniform vec4 dof; // .x = near, .y = focus, .z = far, .w = max_far_blur
uniform float near;
uniform float far;
uniform sampler2DRect depth;

float convertZ(in float z) {
  return far * near / (far + z * (near - far));
}

void main() {
  float z = convertZ(texture2DRect(depth, gl_TexCoord[0].st).r);

  if (z < dof.y) {
    z = (z - dof.y) / (dof.y - dof.x);
  } else {
    z = min(dof.w, (z - dof.y) / (dof.z - dof.y));
  }
  gl_FragColor.r = z * 0.5 + 0.5;
}
"""))

class RenderDOFPass2(ShaderProgram):
    def __init__(self):
        ShaderProgram.__init__(self)
        self.setShader(FragmentShader("dof_f", """\
uniform sampler2DRect focus;
uniform sampler2DRect blur;
uniform sampler2DRect alpha;
uniform vec4 scale;
uniform vec2 taps[16];

float coc_r = 10.0;
float coc_d = 20.0;
float max_blur = 1.0;

void main() {
  vec4 t = gl_TexCoord[0].xyxy * scale;
  float d = texture2DRect(alpha, t.xy).r;
  vec4 R = vec4(d * coc_d - coc_r) * scale;

  vec4 fhi = texture2DRect(focus, t.xy);
  vec4 flo = texture2DRect(blur, t.zw);

  vec4 accum = mix(fhi, flo, abs(d * 2.0 - 1.0));
  accum.a = 1.0;

  for (int i = 1; i < 4; i++) {
    vec4 c = t + taps[i].xyxy * R;

    fhi = texture2DRect(focus, c.xy);
    flo = texture2DRect(blur, c.zw);
    float d2 = texture2DRect(alpha, c.xy).r;

    float blend = abs(d2 * 2.0 - 1.0);
    float weight = d2 < d ? 1.0 : blend;

    vec4 tap = mix(fhi, flo, blend);

    accum.rgb += tap.rgb * weight;
    accum.a += weight;
  }
  gl_FragColor = accum / accum.a;
}
"""))

class DownsamplerRect(ShaderProgram):
    def __init__(self):
        ShaderProgram.__init__(self)
        self.setShader(FragmentShader("downsample_f", """\
uniform sampler2DRect src;
uniform vec2 taps[16];

void main() {
  vec4 dest = vec4(0.0, 0.0, 0.0, 1.0);
  for (int i = 0; i < 16; i++) {
    dest += texture2DRect(src, gl_TexCoord[0].st + taps[i]);
  }
  gl_FragColor = dest / 16.0;
}
"""))

class Downsampler(ShaderProgram):
    def __init__(self):
        ShaderProgram.__init__(self)
        self.setShader(FragmentShader("downsample_rect_f", """\
uniform sampler2D src;
uniform vec2 taps[16];

void main() {
  vec4 dest = vec4(0.0, 0.0, 0.0, 1.0);
  for (int i = 0; i < 16; i++) {
    dest += texture2D(src, gl_TexCoord[0].st + taps[i]);
  }
  gl_FragColor = dest / 16.0;
}
"""))

class Gaussian3(ShaderProgram):
    def __init__(self):
        ShaderProgram.__init__(self)
        self.setShader(FragmentShader("gaussian_f", """\
uniform sampler2D src;
uniform vec2 texel;

void main() {
  gl_FragColor = _blur3(src, gl_TexCoord[0].st, texel);
}
""").addDependency(GaussianFuncs()))

class GaussianRect3(ShaderProgram):
    def __init__(self):
        ShaderProgram.__init__(self)
        self.setShader(FragmentShader("gaussian_rect_f", """\
uniform sampler2DRect src;
uniform vec2 texel;

void main() {
  gl_FragColor = _blur3_r(src, gl_TexCoord[0].st, texel);
}
""").addDependency(GaussianFuncs()))


def gaussNoise(l):
    noise = []
    while len(noise) < l:
        x = random.gauss(.5, .25)
        if 0.0 <= x <= 1.0: noise.append(x)
    return noise


def renderScene(r, object):
    glClearColor(0.0, 0.0, 0.0, 1.0)
    glClearDepth(1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, 8.0/6.0, 1.0, 60.0)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(10.0, 20.0, 30.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

    glEnable(GL_DEPTH_TEST)

    glPushMatrix()
    glRotatef(r, 1, 3, 1)

    glColor4f(0.4, 0.5, 1.0, 1.0)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)

    object.draw()

    glPopMatrix()


def gaussianBlur(src, temp_fbo, tgt_fbo, px, py, pw, ph, blur):
    glDisable(GL_DEPTH_TEST)

    # blur horizonally.
    #tx = 1.0 / src.width
    #ty = 1.0 / src.height
    tx = ty = 1.0

    temp_fbo.pushBind()
    setup2D(temp_fbo.width, temp_fbo.height)

    blur.install()
    blur.usetTex("src", 0, src)
    blur.uset2F("texel", tx, 0.0)

    glBegin(GL_QUADS)
    glTexCoord2f(tx * (     px), ty * (      py)); glVertex2f(     px,      py)
    glTexCoord2f(tx * (px + pw), ty * (      py)); glVertex2f(px + pw,      py)
    glTexCoord2f(tx * (px + pw), ty * ( py + ph)); glVertex2f(px + pw, py + ph)
    glTexCoord2f(tx * (     px), ty * ( py + ph)); glVertex2f(     px, py + ph)
    glEnd()

    # blur vertically.
    #tx = 1.0 / temp_fbo.width
    #ty = 1.0 / temp_fbo.height
    tx = ty = 1.0

    tgt_fbo.bind()
    setup2D(tgt_fbo.width, tgt_fbo.height)

    blur.usetTex("src", 0, temp_fbo.colourBuffer(0))
    blur.uset2F("texel", 0.0, ty)

    glBegin(GL_QUADS)
    glTexCoord2f(tx * (     px), ty * (      py)); glVertex2f(     px,      py)
    glTexCoord2f(tx * (px + pw), ty * (      py)); glVertex2f(px + pw,      py)
    glTexCoord2f(tx * (px + pw), ty * ( py + ph)); glVertex2f(px + pw, py + ph)
    glTexCoord2f(tx * (     px), ty * ( py + ph)); glVertex2f(     px, py + ph)
    glEnd()

    blur.uninstall()

    FrameBuffer.popBind()


def downsample(src, tgt_fbo, downsampler, noise):
    glDisable(GL_DEPTH_TEST)

    tgt_fbo.bind()
    setup2D(tgt_fbo.width, tgt_fbo.height)

    #src_texel_x = 1.0 / src.width
    #tgt_texel_x = 1.0 / tgt_fbo.width
    src_texel_x = tgt_texel_x = 1.0
    downsamp_x = src.width / tgt_fbo.width

    #src_texel_y = 1.0 / src.height
    #tgt_texel_y = 1.0 / tgt_fbo.height
    src_texel_y = tgt_texel_y = 1.0
    downsamp_y = src.height / tgt_fbo.height

    downsampler.install()

    for x in range(4):
        for y in range(4):
            i = x + y * 4
            downsampler.uset2F("taps[" + str(i) + "]",
                src_texel_x * downsamp_x * noise[i * 2] * 2.0 - 1.0,
                src_texel_y * downsamp_y * noise[i * 2 + 1] * 2.0 - 1.0)

    downsampler.usetTex("src", 1, src)

    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex2f(0.0, 0.0)

    glTexCoord2f(src.width * src_texel_x, 0.0)
    glVertex2f(tgt_fbo.width, 0.0)

    glTexCoord2f(src.width * src_texel_x, src.height * src_texel_y)
    glVertex2f(tgt_fbo.width, tgt_fbo.height)

    glTexCoord2f(0.0, src.height * src_texel_y)
    glVertex2f(0.0, tgt_fbo.height)
    glEnd()

    downsampler.uninstall()

    tgt_fbo.unbind()


def renderDOF(scene, alpha, blurred, pass1, pass2, noise):
    sx = scene.width
    sy = scene.height

    pass1.install()
    pass1.uset4F("dof", 15.0, 37.0, 60.0, 0.5);
    pass1.uset1F("near", 1.0);
    pass1.uset1F("far", 60.0);
    pass1.usetTex("depth", 0, scene.depthBuffer());

    glDisable(GL_DEPTH_TEST)

    alpha.pushBind()
    setup2D(scene.width, scene.height)

    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0); glVertex2f(0.0, 0.0)
    glTexCoord2f( sx, 0.0); glVertex2f( sx, 0.0)
    glTexCoord2f( sx,  sy); glVertex2f( sx,  sy)
    glTexCoord2f(0.0,  sy); glVertex2f(0.0,  sy)
    glEnd()

    pass1.uninstall()

    FrameBuffer.popBind()

    # pass 2 goes to the display
    pass2.install()
    for i in range(1,16):
        pass2.uset2F("taps[0]", 0.0, 0.0)
        pass2.uset2F("taps[" + str(i) + "]", noise[i * 2] * 2.0 - 1.0,
            noise[i * 2 + 1] * 2.0 - 1.0)
    pass2.usetTex("focus", 0, scene.colourBuffer(0))
    pass2.usetTex("blur", 1, blurred.colourBuffer(0))
    pass2.usetTex("alpha", 2, alpha.colourBuffer(0))
    pass2.uset4F("scale", 1.0, 1.0, 0.25, 0.25);

    setup2D(scene.width, scene.height)

    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0); glVertex2f(0.0, 0.0)
    glTexCoord2f( sx, 0.0); glVertex2f( sx, 0.0)
    glTexCoord2f( sx,  sy); glVertex2f( sx,  sy)
    glTexCoord2f(0.0,  sy); glVertex2f(0.0,  sy)
    glEnd()

    pass2.uninstall()

def setup2D(w, h):
    glViewport(0, 0, w, h)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    glOrtho(0, w, 0, h, -1, 1)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

def blit(surf, x, y, w, h, mode):
    glActiveTexture(GL_TEXTURE0);
    surf.enableAndBind()

    if surf.gl_tgt == GL_TEXTURE_RECTANGLE_ARB:
        sx, sy = w, h
    else:
        tx, ty = surf.width, surf.height
        sx, sy = w / tx, h / ty

    glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, mode)

    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0); glVertex2f(    x,     y)
    glTexCoord2f( sx, 0.0); glVertex2f(w + x,     y)
    glTexCoord2f( sx,  sy); glVertex2f(w + x, h + y)
    glTexCoord2f(0.0,  sy); glVertex2f(    x, h + y)
    glEnd()

    surf.unbindAndDisable()


def main():
    screen_width = 800
    screen_height = 600
    window = pyglet.window.Window(screen_width, screen_height)

    cparams = TextureParam(wrap = GL_CLAMP)

    buf = FrameBuffer(screen_width, screen_height,
        Surface(Surface.SURF_COLOUR, gl_tgt=GL_TEXTURE_RECTANGLE_ARB,
            params=cparams),
        Surface(Surface.SURF_DEPTH, gl_tgt=GL_TEXTURE_RECTANGLE_ARB,
            gl_fmt=GL_DEPTH_COMPONENT32_ARB, is_texture=True,
            is_mipmapped=False, params=cparams))
    buf.init()
    buf.attach()
    buf.unbind()

    alpha_buf = FrameBuffer(screen_width, screen_height,
        Surface(Surface.SURF_COLOUR, gl_tgt=GL_TEXTURE_RECTANGLE_ARB,
            params = cparams))
    alpha_buf.init()
    alpha_buf.attach()
    alpha_buf.unbind()

    buf_subsampled = FrameBuffer(200, 150,
        Surface(Surface.SURF_COLOUR, gl_tgt=GL_TEXTURE_RECTANGLE_ARB,
            params=cparams),
        Surface(Surface.SURF_DEPTH, params=cparams))
    buf_subsampled.init()
    buf_subsampled.attach()
    buf_subsampled.unbind()

    buf_subsampled2 = FrameBuffer(200, 150,
        Surface(Surface.SURF_COLOUR, gl_tgt=GL_TEXTURE_RECTANGLE_ARB,
            params=cparams),
        Surface(Surface.SURF_DEPTH, params=cparams))
    buf_subsampled2.init()
    buf_subsampled2.attach()
    buf_subsampled2.unbind()

    object = cube_array_list()

    downsampler=DownsamplerRect()
    noise=gaussNoise(32)
    blur=GaussianRect3()
    pass1=RenderDOFPass1()
    pass2=RenderDOFPass2()

    r = 0
    clk = clock.Clock(60)
    while not window.has_exit:
        clk.tick()

        window.dispatch_events()

        buf.bind()
        glViewport(0, 0, screen_width, screen_height)
        r += 1
        if r > 360: r = 0
        renderScene(r, object)
        buf.unbind()

        downsample(buf.colourBuffer(0), buf_subsampled, downsampler, noise)
        
        gaussianBlur(buf_subsampled.colourBuffer(0),
                     buf_subsampled2,
                     buf_subsampled,
                     0.0,
                     0.0,
                     200.0,
                     150.0,
                     blur)

        renderDOF(buf, alpha_buf, buf_subsampled, pass1, pass2, noise)

        #fps.draw(window, clk)

        window.flip()

    buf = None
    buf_subsampled = None
main()

