from collections import namedtuple

from pyglet.gl import *
from ctypes import *


_debug_gl_shaders = pyglet.options['debug_gl_shaders']


# TODO: test other shader types, and update pyglet GL bindings if necessary.
_shader_types = {
    'vertex': GL_VERTEX_SHADER,
    'fragment': GL_FRAGMENT_SHADER,
    # 'geometry': GL_GEOMETRY_SHADER,
}

_uniform_getters = {
    GLint: glGetUniformiv,
    GLfloat: glGetUniformfv,
}

_uniform_setters = {
    # gl_type, setter, length, count
    GL_INT: (GLint, glUniform1iv, 1, 1),
    GL_INT_VEC2: (GLint, glUniform2iv, 2, 1),
    GL_INT_VEC3: (GLint, glUniform3iv, 3, 1),
    GL_INT_VEC4: (GLint, glUniform4iv, 4, 1),

    GL_FLOAT: (GLfloat, glUniform1fv, 1, 1),
    GL_FLOAT_VEC2: (GLfloat, glUniform2fv, 2, 1),
    GL_FLOAT_VEC3: (GLfloat, glUniform3fv, 3, 1),
    GL_FLOAT_VEC4: (GLfloat, glUniform4fv, 4, 1),

    GL_SAMPLER_2D: (GLint, glUniform1i, 1, 1),

    # TODO: test/implement these:
    # GL_FLOAT_MAT2: glUniformMatrix2fv,
    # GL_FLOAT_MAT3: glUniformMatrix3fv,
    # GL_FLOAT_MAT4: glUniformMatrix4fv,
    #
    # GL_FLOAT_MAT2x3: glUniformMatrix2x3fv,
    # GL_FLOAT_MAT2x4: glUniformMatrix2x4fv,
    #
    # GL_FLOAT_MAT3x2: glUniformMatrix3x2fv,
    # GL_FLOAT_MAT3x4: glUniformMatrix3x4fv,
    #
    # GL_FLOAT_MAT4x2: glUniformMatrix4x2fv,
    # GL_FLOAT_MAT4x3: glUniformMatrix4x3fv,
}


def create_getter_function(program_id, location, gl_type, length):

    gl_getter_func = _uniform_getters[gl_type]

    def getter_func():
        buffer = (gl_type * length)()
        gl_getter_func(program_id, location, buffer)
        return buffer[0] if length == 1 else buffer[:]

    return getter_func


class Shader:
    def __init__(self, source_string, shader_type):
        if shader_type not in _shader_types.keys():
            raise TypeError("The `shader_type` must be 'vertex' or 'fragment'.")
        self._source = source_string
        self.type = shader_type
        self._id = self._compile_shader()

    @property
    def id(self):
        return self._id

    def _compile_shader(self):
        shader_source = self._source.encode("utf8")
        shader_id = glCreateShader(_shader_types[self.type])
        source_buffer = c_char_p(shader_source)
        source_buffer_pointer = cast(pointer(source_buffer), POINTER(POINTER(c_char)))
        source_length = c_int(len(shader_source) + 1)

        # shader id, count, string, length:
        glShaderSource(shader_id, 1, source_buffer_pointer, source_length)
        glCompileShader(shader_id)

        status = c_int(0)
        glGetShaderiv(shader_id, GL_COMPILE_STATUS, byref(status))

        if _debug_gl_shaders:
            print(self._get_shader_log(shader_id))

        if status.value != GL_TRUE:
            raise GLException("The {0} shader failed to compile. "
                              "\n{1}".format(self.type, self._get_shader_log(shader_id)))

        return shader_id

    def _get_shader_log(self, shader_id):
        log_length = c_int(0)
        glGetShaderiv(shader_id, GL_INFO_LOG_LENGTH, byref(log_length))
        result_str = create_string_buffer(log_length.value)
        glGetShaderInfoLog(shader_id, log_length, None, result_str)
        if result_str.value:
            return ("OpenGL returned the following message when compiling the {0} shader: "
                    "\n{1}".format(self.type, result_str.value.decode('utf8')))
        else:
            return "Compiled {0} shader successfully.".format(self.type)

    def __del__(self):
        try:
            glDeleteShader(self._id)
            # There are potentially several different exceptions that could
            # be raised here, none of them are vital to catch when deleting.
        except:
            pass

        if _debug_gl_shaders:
            print("Destroyed {0} shader object.".format(self.type))


class ShaderProgram:
    """OpenGL Shader Program"""

    Uniform = namedtuple('Uniform', 'location, getter, setter, attrs')
    Attribute = namedtuple('Attribute', 'location attribute_type')

    def __init__(self, *shaders):
        self._id = self._link_program(shaders)
        self._active = False

        self._uniforms = {}
        self._attributes = {}
        self._parse_all_uniforms()
        # self._parse_all_attributes()

        if _debug_gl_shaders:
            print(self._get_program_log())

    @property
    def id(self):
        return self._id

    @property
    def active(self):
        return self._active

    def _get_program_log(self):
        result = c_int(0)
        # glGetProgramiv(program_id, GL_LINK_STATUS, byref(result))
        # glGetProgramiv(program_id, GL_ATTACHED_SHADERS, byref(result))
        glGetProgramiv(self._id, GL_INFO_LOG_LENGTH, byref(result))
        result_str = create_string_buffer(result.value)
        glGetProgramInfoLog(self._id, result, None, result_str)
        if result_str.value:
            return ("OpenGL returned the following message when linking the program: "
                    "\n{0}".format(result_str.value))
        else:
            return "Program linked successfully."

    def _link_program(self, shaders):
        # TODO: catch exceptions when linking Program:
        program_id = glCreateProgram()
        for shader in shaders:
            glAttachShader(program_id, shader.id)
        glLinkProgram(program_id)
        return program_id

    def use_program(self):
        glUseProgram(self._id)
        self._active = True

    def stop_program(self):
        glUseProgram(0)
        self._active = False

    def __enter__(self):
        self.use_program()

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop_program()

    def __del__(self):
        try:
            glDeleteProgram(self._id)
        # There are potentially several different exceptions that could
        # be raised here, none of them are vital to catch when deleting.
        except:
            pass

        if _debug_gl_shaders:
            print("Destroyed Shader Program.")

    def __setitem__(self, key, values):
        if not self._active:
            raise Exception("Shader Program is not active.")

        try:
            uniform = self._uniforms[key]
        except KeyError("Uniform name was not found."):
            raise

        try:
            gl_type, length, count = uniform.attrs
            if length == 1:
                uniform.setter(uniform.location, length, (gl_type * length)(values))
            else:
                # array = (gl_type * length)(*values)
                ptr = cast((gl_type * length)(*values), POINTER(gl_type))
                uniform.setter(uniform.location, count, ptr)
        except GLException:
            raise

    def __getitem__(self, item):
        try:
            uniform = self._uniforms[item]
        except KeyError("Uniform name was not found."):
            raise

        try:
            return uniform.getter()
        except GLException:
            raise

    def _parse_all_uniforms(self):
        for index in range(self.get_num_active(GL_ACTIVE_UNIFORMS)):
            uniform_name, uniform_type, uniform_size = self.query_uniform(index)
            location = self.get_uniform_location(uniform_name)

            try:
                gl_type, gl_set_func, length, count = _uniform_setters[uniform_type]

                getter = create_getter_function(self._id, location, gl_type, length)
                # setter = create_setter_function(uniform_type, location)

                attrs = gl_type, length, count

            except KeyError:
                raise GLException("Unsupported Uniform type {0}".format(uniform_type))

            self._uniforms[uniform_name] = self.Uniform(location, getter, gl_set_func, attrs)

    def _parse_all_attributes(self):
        for i in range(self.get_num_active(GL_ACTIVE_ATTRIBUTES)):
            attrib_name = self.get_attrib_name(i)
            attrib_type = self.get_attrib_type(attrib_name)
            location = self.get_attrib_location(attrib_name)
            self._attributes[attrib_name] = self.Attribute(location, attrib_type)

    def get_num_active(self, variable_type):
        """Get the number of active variables of the passed GL type.

        :param variable_type: Either GL_ACTIVE_ATTRIBUTES, or GL_ACTIVE_UNIFORMS
        :return: int: number of active types of this kind
        """
        num_active = GLint(0)
        glGetProgramiv(self._id, variable_type, byref(num_active))
        return num_active.value

    def get_attrib_type(self, name):
        location = self.get_attrib_location(name)
        if location == -1:
            raise GLException("Could not find Attribute named: {0}".format(name))
        else:
            buf_size = 128
            size = GLint()
            attr_type = GLenum()
            name_buf = create_string_buffer(buf_size)
            glGetActiveAttrib(self._id, location, buf_size, None, size, attr_type, name_buf)
            return attr_type.value

    def get_attrib_name(self, index):
        buf_size = 128
        size = c_int(0)
        attr_type = c_uint(0)
        name_buf = create_string_buffer(buf_size)
        try:
            glGetActiveAttrib(self._id, index, buf_size, None, size, attr_type, name_buf)
            return name_buf.value.decode()
        except GLException:
            return None

    def get_attrib_location(self, name):
        return glGetAttribLocation(self._id, create_string_buffer(name.encode('ascii')))

    def get_uniform_name(self, index):
        buf_size = 128
        size = c_int(0)
        attr_type = c_uint(0)
        name_buf = create_string_buffer(buf_size)
        try:
            glGetActiveUniform(self._id, index, buf_size, None, size, attr_type, name_buf)
            return name_buf.value.decode()
        except GLException:
            return None

    def get_uniform_location(self, name):
        return glGetUniformLocation(self._id, create_string_buffer(name.encode('ascii')))

    def get_uniform_type(self, name):
        location = self.get_uniform_location(name)
        if location == -1:
            raise GLException("Could not find Uniform named: {0}".format(name))
        else:
            buf_size = 128
            size = GLint()
            uni_type = GLenum()
            name_buf = create_string_buffer(buf_size)
            glGetActiveUniform(self._id, location, buf_size, None, size, uni_type, name_buf)
            return uni_type.value

    def get_uniform_size(self, name):
        location = self.get_uniform_location(name)
        if location == -1:
            raise GLException("Could not find Uniform named: {0}".format(name))
        else:
            buf_size = 128
            size = GLint()
            uni_type = GLenum()
            name_buf = create_string_buffer(buf_size)
            glGetActiveUniform(self._id, location, buf_size, None, size, uni_type, name_buf)
            return size.value

    def query_uniform(self, index):
        buf_size = 128
        usize = GLint()
        utype = GLenum()
        uname = create_string_buffer(buf_size)
        try:
            glGetActiveUniform(self._id, index, buf_size, None, usize, utype, uname)
            return uname.value.decode(), utype.value, usize.value
        except GLException:
            raise


vertex_source = """#version 330 core
    in vec4 vertices;
    in vec4 colors;
    in vec2 tex_coords;
    out vec4 vertex_colors;
    out vec2 texture_coords;

    uniform vec2 window_size;
    uniform float zoom = 1.0;

    void main()
    {
        gl_Position = vec4(vertices.x * 2.0 / window_size.x - 1.0,
                           vertices.y * 2.0 / window_size.y - 1.0,
                           vertices.z,
                           vertices.w * zoom);

        vertex_colors = vec4(1.0, 0.5, 0.2, 1.0);
        vertex_colors = colors;
        texture_coords = tex_coords;
    }
"""

fragment_source = """#version 330 core
    in vec4 vertex_colors;
    in vec2 texture_coords;
    out vec4 final_colors;

    uniform sampler2D our_texture;


    void main()
    {
        // final_colors = vertex_colors;
        final_colors = texture(our_texture, texture_coords) + vertex_colors;
    }
"""
