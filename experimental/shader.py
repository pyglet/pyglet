from ctypes import *

from pyglet.gl import *

class GLSLException(Exception): pass



def glsl_log(handle):
    if handle == 0:
        return ''
    log_len = c_int(0)

    glGetObjectParameterivARB(handle, GL_OBJECT_INFO_LOG_LENGTH_ARB,
        byref(log_len))
    if log_len.value == 0:
        return ''

    log = create_string_buffer(log_len.value) # does log_len include the NUL?

    chars_written = c_int(0)
    glGetInfoLogARB(handle, log_len.value, byref(chars_written), log)

    return log.value



class Shader(object):
    s_tag = 0

    def __init__(self, name, prog):
        self.name = name
        self.prog = prog
        self.shader = 0
        self.compiling = False
        self.tag = -1
        self.dependencies = []

    def __del__(self):
        self.destroy()

    def _source(self):
        if self.tag == Shader.s_tag: return []
        self.tag = Shader.s_tag
        
        r = []
        for d in self.dependencies:
            r.extend(d._source())
        r.append(self.prog)

        return r

    def _compile(self):
        if self.shader: return
        if self.compiling : return
        self.compiling = True

        self.shader = glCreateShaderObjectARB(self.shaderType())
        if self.shader == 0:
            raise GLSLException('faled to create shader object')

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
            raise GLSLException('failed to compile shader', err)

    def _attachTo(self, program):
        if self.tag == Shader.s_tag: return

        self.tag = Shader.s_tag

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
        Shader.s_tag = Shader.s_tag + 1
        self._attachTo(program)

    # ATI/apple's glsl compiler is broken.
    def attachFlat(self, program):
        if self.isCompiled():
            glAttachObjectARB(program, self.shader)

    def compileFlat(self):
        if self.isCompiled(): return

        self.shader = glCreateShaderObjectARB(self.shaderType())
        if self.shader == 0:
            raise GLSLException('faled to create shader object')

        all_source = ['\n'.join(self._source())]
        prog = (c_char_p * len(all_source))(*all_source)
        length = (c_int * len(all_source))(-1)
        glShaderSourceARB(self.shader,
                          len(all_source),
                          cast(prog, POINTER(POINTER(c_char))),
                          length)
        glCompileShaderARB(self.shader)

        compile_status = c_int(0)
        glGetObjectParameterivARB(self.shader, GL_OBJECT_COMPILE_STATUS_ARB, byref(compile_status))

        if not compile_status.value:
            err = glsl_log(self.shader)
            glDeleteObjectARB(self.shader)
            self.shader = 0
            raise GLSLException('failed to compile shader', err)


    def compile(self):
        if self.isCompiled(): return

        for d in self.dependencies:
            d.compile()

        self._compile()



class VertexShader(Shader):
    def shaderType(self): return GL_VERTEX_SHADER_ARB



class FragmentShader(Shader):
    def shaderType(self): return GL_FRAGMENT_SHADER_ARB



class ShaderProgram(object):
    def __init__(self, vertex_shader=None, fragment_shader=None):
        self.vertex_shader = vertex_shader
        self.fragment_shader = fragment_shader
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
        if self.vertex_shader is not None: self.vertex_shader.compileFlat()
        if self.fragment_shader is not None: self.fragment_shader.compileFlat()

        self.program = glCreateProgramObjectARB()
        if self.program == 0:
            raise GLSLException('failed to create program object')

        if self.vertex_shader is not None: self.vertex_shader.attachFlat(self.program)
        if self.fragment_shader is not None: self.fragment_shader.attachFlat(self.program)

        glLinkProgramARB(self.program)

        link_status = c_int(0)
        glGetObjectParameterivARB(self.program, GL_OBJECT_LINK_STATUS_ARB, byref(link_status))
        if link_status.value == 0:
            err = glsl_log(self.program)
            glDeleteObjectARB(self.program)
            self.program = 0
            raise GLSLException('failed to link shader', err)

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

__all__ = ['VertexShader', 'FragmentShader', 'ShaderProgram', 'GLSLException']
