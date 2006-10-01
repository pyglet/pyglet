import pyglet.window
import pyglet.clock
from pyglet.window.event import *
import time
from ctypes import *
from exceptions import *
import random
import array

from pyglet.GL.VERSION_2_0 import *
from pyglet.GL.EXT_framebuffer_object import *
from pyglet.GL.EXT_texture_cube_map import *
from pyglet.GL.EXT_texture_filter_anisotropic import *
from pyglet.GL.EXT_packed_depth_stencil import *
from pyglet.GL.ARB_texture_rectangle import *
from pyglet.GL.ARB_shader_objects import *
from pyglet.GL.ARB_vertex_shader import *
from pyglet.GL.ARB_fragment_shader import *
from pyglet.GLU.VERSION_1_3 import *

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

    def __init__(self):
        if self.max_anisotropy == 0.0:
            v = c_float()
            glGetFloatv(GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT, byref(v))
            self.max_anisotropy = v.value

        self.min_filter = GL_LINEAR
        self.mag_filter = GL_LINEAR
        self.min_lod = -1000
        self.max_lod = 1000
        self.min_mipmap = 0
        self.max_mipmap = 1000
        self.wrap_s = GL_REPEAT
        self.wrap_t = GL_REPEAT
        self.wrap_r = GL_REPEAT
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
        SURF_COLOUR:        ( GL_RGBA,                 GL_TEXTURE_2D,       True,  False ),
        SURF_DEPTH:         ( GL_DEPTH_COMPONENT24,    GL_RENDERBUFFER_EXT, False, False ),
        SURF_STENCIL:       ( GL_STENCIL_INDEX8_EXT,   GL_RENDERBUFFER_EXT, False, False ),
        SURF_DEPTH_STENCIL: ( GL_DEPTH24_STENCIL8_EXT, GL_RENDERBUFFER_EXT, False, False )
    }

    def __del__(self):
        self.destroy()

    def __init__(self,
                 surface_type = SURF_NONE,
                 gl_fmt = None,
                 gl_tgt = None,
                 is_texture = None,
                 is_mipmapped = None,
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

    def destroy(self):
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
        if self.surface_type == self.SURF_COLOUR and not self.is_texture: raise Failed('bad surface')
        if self.surface_type == self.SURF_STENCIL and self.is_texture: raise Failed('bad surface')

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
            if self.gl_tgt == GL_TEXTURE_1D:
                glTexImage1D(self.gl_tgt,
                             0,
                             self.gl_fmt,
                             w,
                             0,
                             GL_RGBA, GL_BYTE, None)
            elif self.gl_tgt in (GL_TEXTURE_2D, GL_TEXTURE_RECTANGLE_ARB):
                glTexImage2D(self.gl_tgt,
                             0,
                             self.gl_fmt,
                             w, h,
                             0,
                             GL_RGBA, GL_BYTE, None)
            elif self.gl_tgt == GL_TEXTURE_CUBE_MAP_EXT:
                for i in range(6):
                    glTexImage2D(GL_TEXTURE_CUBE_MAP_POSITIVE_X_EXT + i,
                                 0,
                                 self.gl_fmt,
                                 w, h,
                                 0,
                                 GL_RGBA, GL_BYTE, None)
            elif self.gl_tgt == GL_TEXTURE_3D:
                glTexImage3D(self.gl_tgt,
                             0,
                             self.gl_fmt,
                             w, h, d,
                             0,
                             GL_RGBA, GL_BYTE, None)
            else:
                raise Failed('unhandled texture target: ' + hex(self.gl_tgt))

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
            glGenRenderbuffersEXT(1, byref(gl_id))
            glBindRenderbufferEXT(GL_RENDERBUFFER_EXT, gl_id)
            glRenderbufferStorageEXT(GL_RENDERBUFFER_EXT, self.gl_fmt, w, h)
            glBindRenderbufferEXT(GL_RENDERBUFFER_EXT, 0)

        if gl_id.value == 0: raise Failed('failed to init. glGetError(): ' + str(glGetError()))

        self.gl_id = gl_id.value
        self.width, self.height, self.depth = w, h, d



class FrameBuffer(object):
    bound_fbo = 0

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
        for i in self.colour: i[0].init(self.width, self.height)
        if self.depth is not None: self.depth[0].init(self.width, self.height)
        if self.stencil is not None: self.stencil[0].init(self.width, self.height)

        fbo = c_uint(0)
        glGenFramebuffersEXT(1, byref(fbo))
        self.frame_buffer = fbo.value
        if self.frame_buffer == 0: raise Failed('failed to init. glGetError(): ' + str(glGetError()))

    def attach(self, mipmap_level = 0):
        if self.frame_buffer == 0: raise Failed('not initialised')

        self.bind()

        R = zip(self.colour, range(GL_COLOR_ATTACHMENT0_EXT, GL_COLOR_ATTACHMENT0_EXT + len(self.colour)))
        R.extend(((self.depth, GL_DEPTH_ATTACHMENT_EXT), (self.stencil, GL_STENCIL_ATTACHMENT_EXT)))

        for surf_info, attachment in R:
            if surf_info is None: continue
            surf, tgt = surf_info

            if surf.gl_id == 0: continue

            if surf.is_texture:
                glFramebufferTexture2DEXT(GL_FRAMEBUFFER_EXT, attachment, tgt, surf.gl_id, mipmap_level)
            else:
                glFramebufferRenderbufferEXT(GL_FRAMEBUFFER_EXT, attachment, tgt, surf.gl_id)

        status = glCheckFramebufferStatusEXT(GL_FRAMEBUFFER_EXT)

        if status != GL_FRAMEBUFFER_COMPLETE_EXT:
            raise Failed('attach failed: ' + hex(status))

    def bind(self):
        if FrameBuffer.bound_fbo != self.frame_buffer:
            glFlush()
            glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, self.frame_buffer)
            FrameBuffer.bound_fbo = self.frame_buffer

    def unbind(self):
        if FrameBuffer.bound_fbo != 0:
            glBindFramebufferEXT(GL_FRAMEBUFFER_EXT, 0)
            FrameBuffer.bound_fbo = 0

    def destroy(self):
        if self.frame_buffer == 0: return
        self.colour = []
        self.depth = None
        self.stencil = None
        if self.frame_buffer != 0:
            fbo = c_uint(self.frame_buffer)
            glDeleteFramebuffersEXT(1, byref(fbo))
        self.frame_buffer = 0

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

    def __init__(self, w, h, *surf):
        self.frame_buffer = 0
        self.width = w
        self.height = h

        self.colour = []
        self.depth = None
        self.stencil = None

        for s in surf: self.add(s)



def glsl_log(handle):
    if handle == 0:
        return ''
    log_len = c_int(0)

    glGetObjectParameterivARB(handle, GL_OBJECT_INFO_LOG_LENGTH_ARB, byref(log_len))
    if log_len.value == 0:
        return ''

    log = create_string_buffer(log_len.value) # does log_len include the NUL?

    chars_written = c_int(0)
    glGetInfoLogARB(handle, log_len.value, byref(chars_written), log)

    return log.value



class Shader(object):
    s_attach = 0

    def __init__(self, name, prog):
        self.name = name
        self.prog = prog
        self.shader = 0
        self.compiling = False
        self.attaching = -1
        self.dependencies = []

    def __del__(self):
        self.destroy()

    def _compile(self):
        if self.shader: return
        if self.compiling : return
        self.compiling = True

        self.shader = glCreateShaderObjectARB(self.shaderType())
        if self.shader == 0:
            raise Failed('faled to create shader object')

        prog = c_char_p(self.prog)
        length = c_int(-1)
        glShaderSourceARB(self.shader,
                          1,
                          cast(byref(prog), POINTER(POINTER(c_char))),
                          byref(length))
        glCompileShaderARB(self.shader)

        self.compiling = False

        compile_status = c_int(0)
        glGetObjectParameterivARB(self.shader, GL_OBJECT_COMPILE_STATUS_ARB, byref(compile_status))

        if not compile_status.value:
            err = glsl_log(self.shader)
            glDeleteObjectARB(self.shader)
            self.shader = 0
            raise Failed('failed to compile shader', err)


    def _attachTo(self, program):
        if self.attaching == Shader.s_attach: return

        self.attaching = Shader.s_attach

        for d in self.dependencies:
            d._attachTo(program)

        if self.isCompiled():
            glAttachObjectARB(program, self.shader)

    def addDependency(self, shader):
        self.dependencies.append(shader)
        return self

    def destroy(self):
        if self.shader != 0: glDeleteObjectARB(self.shader)


    def shaderType(self):
        raise NotImplementedError()

    def isCompiled(self):
        return self.shader != 0

    def attachTo(self, program):
        Shader.s_attach = Shader.s_attach + 1
        self._attachTo(program)

    def compile(self):
        if self.isCompiled(): return

        for d in self.dependencies:
            d.compile()

        self._compile()



class VertexShader(Shader):
    def shaderType(self): return GL_VERTEX_SHADER_ARB



class FragmentShader(Shader):
    def shaderType(self): return GL_FRAGMENT_SHADER_ARB



class ShaderMaterial(object):
    def __init__(self):
        self.vertex_shader = None
        self.fragment_shader = None
        self.program = 0

    def __del__(self):
        self.destroy()

    def destroy(self):
        if self.program != 0: glDeleteObjectARB(self.program)

    def setShader(self, shader):
        if isinstance(shader, FragmentShader):
            self.fragment_shader = shader
        if isinstance(shader, VertexShader):
            self.vertex_shader = shader
        if self.program != 0: glDeleteObjectARB(self.program)

    def link(self):
        if self.vertex_shader is not None: self.vertex_shader.compile()
        if self.fragment_shader is not None: self.fragment_shader.compile()

        self.program = glCreateProgramObjectARB()
        if self.program == 0:
            raise Failed('failed to create program object')

        if self.vertex_shader is not None: self.vertex_shader.attachTo(self.program)
        if self.fragment_shader is not None: self.fragment_shader.attachTo(self.program)

        glLinkProgramARB(self.program)

        link_status = c_int(0)
        glGetObjectParameterivARB(self.program, GL_OBJECT_LINK_STATUS_ARB, byref(link_status))
        if link_status.value == 0:
            err = glsl_log(self.program)
            glDeleteObjectARB(self.program)
            self.program = 0
            raise Failed('failed to link shader', err)

        self.__class__._uloc_ = {}
        self.__class__._vloc_ = {}

        return self.program

    def prog(self):
        if self.program: return self.program
        return self.link()

    def install(self):
        p = self.prog()
        if p != 0:
            glUseProgramObjectARB(p)

    def uninstall(self):
        glUseProgramObjectARB(0)

    def uniformLoc(self, var):
        try:
            return self.__class__._uloc_[var]
        except:
            if self.program == 0:
                self.link()
            self.__class__._uloc_[var] = v = glGetUniformLocationARB(self.program, var)
            return v

    def uset1F(self, var, x):
        glUniform1fARB(self.uniformLoc(var), x)

    def uset2F(self, var, x, y):
        glUniform2fARB(self.uniformLoc(var), x, y)

    def uset3F(self, var, x, y, z):
        glUniform3fARB(self.uniformLoc(var), x, y, z)

    def uset4F(self, var, x, y, z, w):
        glUniform4fARB(self.uniformLoc(var), x, y, z, w)

    def uset1I(self, var, x):
        glUniform1iARB(self.uniformLoc(var), x)

    def uset3I(self, var, x, y, z):
        glUniform1iARB(self.uniformLoc(var), x, y, z)

    def usetM4F(self, var, m):
        pass
        # glUniform1iARB(self.uniformLoc(var), x, y, z)

    def usetTex(self, var, u, v):
        glUniform1iARB(self.uniformLoc(var), u)
        glActiveTexture(GL_TEXTURE0 + u)
        glBindTexture(v.gl_tgt, v.gl_id)



class Downsampler(ShaderMaterial):
    def __init__(self):
        ShaderMaterial.__init__(self)
        self.setShader(VertexShader("downsample_v", """\
void main() {
  gl_TexCoord[0] = gl_MultiTexCoord0;
  gl_Position = ftransform();
}
"""))
        self.setShader(FragmentShader("downsample_f", """\
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



def gaussNoise(l):
    noise = []
    while len(noise) < l:
        x = random.gauss(.5, .25)
        if 0.0 <= x <= 1.0: noise.append(x)
    return noise



def gaussNoiseSurf2D2C(w):
    surf = Surface(Surface.SURF_COLOUR, gl_fmt = GL_LUMINANCE16_ALPHA16)
    surf.params.min_filter = GL_NEAREST
    surf.params.max_filter = GL_NEAREST
    surf.init(w, w)
    noise =  []
    n = array.array('f',gaussNoise(surf.width * surf.height * 2))
    surf.bind()
    glTexImage2D(surf.gl_tgt, 0, surf.gl_fmt, surf.width, surf.height, 0,
                 GL_LUMINANCE_ALPHA, GL_FLOAT,
                 n.buffer_info()[0])
    return surf



class ExitHandler(object):
    def __init__(self):
        self.running = True

    def on_close(self):
        self.running = False

    def on_keypress(self, symbol, modifiers):
        if symbol == pyglet.window.key.K_ESCAPE:
            self.running = False
        return EVENT_UNHANDLED



factory = pyglet.window.WindowFactory()
factory.config._attributes['doublebuffer'] = 1

exit_handler = ExitHandler()

window = factory.create(width=800, height=600)
window.push_handlers(exit_handler)

noise = gaussNoiseSurf2D2C(256)

clk = pyglet.clock.Clock()

r = 0

buf = FrameBuffer(1024, 1024, Surface(Surface.SURF_COLOUR), Surface(Surface.SURF_DEPTH))
buf.init()
buf.attach()
buf.unbind()

buf_subsampled = FrameBuffer(256, 256, Surface(Surface.SURF_COLOUR), Surface(Surface.SURF_DEPTH))
buf_subsampled.init()
buf_subsampled.attach()
buf_subsampled.unbind()

def renderScene():
    global r
    glClearColor(0.1, 0.2, 0.3, 1.0)
    glClearDepth(1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60.0, 8.0/6.0, 1.0, 100.0)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(10.0, 20.0, 30.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0)

    glEnable(GL_DEPTH)

    r += 1
    if r > 360: r = 0

    glPushMatrix()
    glRotatef(r, 0, 1, 0)

    glColor4f(1.0, 0.0, 0.0, 1.0)

    glBegin(GL_QUADS)
    glVertex3f(-25.0, 0.0, -5.0)
    glVertex3f(-25.0, 0.0, +5.0)
    glVertex3f(+25.0, 0.0, +5.0)
    glVertex3f(+25.0, 0.0, -25.0)
    glEnd()

    glPopMatrix()


def downsample(src, tgt_fbo, downsampler = Downsampler(), noise = gaussNoise(32)):
    tgt_fbo.bind()
    setup2D(tgt_fbo.width, tgt_fbo.height)
    glDisable(GL_DEPTH)

    src_texel_x = 1.0 / src.width
    tgt_texel_x = 1.0 / tgt_fbo.width
    downsamp_x = src.width / tgt_fbo.width

    src_texel_y = 1.0 / src.height
    tgt_texel_y = 1.0 / tgt_fbo.height
    downsamp_y = src.height / tgt_fbo.height

    downsampler.install()

    for x in range(4):
        for y in range(4):
            i = x + y * 4
            downsampler.uset2F("taps[" + str(i) + "]",
                               src_texel_x * downsamp_x * noise[i * 2],
                               src_texel_y * downsamp_y * noise[i * 2 + 1])

    downsampler.usetTex("src", 1, src)

    glBegin(GL_QUADS)
    glTexCoord2f(0.0, 0.0)
    glVertex2f(0.0, 0.0)

    glTexCoord2f(1.0, 0.0)
    glVertex2f(buf_subsampled.width, 0.0)

    glTexCoord2f(1.0, 1.0)
    glVertex2f(buf_subsampled.width, buf_subsampled.height)

    glTexCoord2f(0.0, 1.0)
    glVertex2f(0.0, buf_subsampled.height)
    glEnd()

    downsampler.uninstall()

    tgt_fbo.unbind()


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

while exit_handler.running:
    clk.set_fps(60)

    window.dispatch_events()

    buf.bind()
    glViewport(0, 0, 800, 600)
    renderScene()
    buf.unbind()

    glFlush()
    downsample(buf.colourBuffer(0), buf_subsampled)
    glFlush()

    glClearColor(0.0, 0.0, 0.0, 0.0)
    glClearDepth(1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    setup2D(800, 600)
    glDisable(GL_DEPTH)

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glDisable(GL_LIGHTING)

    glColor4f(1.0, 1.0, 1.0, 1.0)

    blit(buf.colourBuffer(0), 0.0, 0.0, 800.0, 600.0, GL_MODULATE)
    blit(buf_subsampled.colourBuffer(0), 0.0, 0.0, 200.0, 150.0, GL_MODULATE)

    glDisable(GL_BLEND)

    window.flip()

buf = None
buf_subsampled = None
noise = None
