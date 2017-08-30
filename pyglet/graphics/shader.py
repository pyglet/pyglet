import pyglet

from collections import namedtuple
from pyglet.gl import *
from ctypes import *


_debug_gl_shaders = pyglet.options['debug_gl_shaders']


# TODO: test other shader types, and update pyglet GL bindings if necessary.
_shader_types = {
    'vertex': GL_VERTEX_SHADER,
    'fragment': GL_FRAGMENT_SHADER,
    'geometry': GL_GEOMETRY_SHADER,
}

_uniform_getters = {
    GLint: glGetUniformiv,
    GLfloat: glGetUniformfv,
}

_uniform_setters = {
    # uniform type: (gl_type, setter, length, count)
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


def create_getter_function(program_id, location, gl_getter, buffer, length):

    if length == 1:
        def getter_func():
            gl_getter(program_id, location, buffer)
            return buffer[0]
    else:
        def getter_func():
            gl_getter(program_id, location, buffer)
            return buffer[:]

    return getter_func


def create_setter_function(location, gl_setter, buffer, length, count, ptr):

    if length == 1:
        def setter_func(value):
            buffer[0] = value
            gl_setter(location, count, ptr)
    else:
        def setter_func(values):
            buffer[:] = values
            gl_setter(location, count, ptr)

    return setter_func


class Shader:
    """OpenGL Shader object"""

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
        shader_source_utf8 = self._source.encode("utf8")
        source_buffer_pointer = cast(c_char_p(shader_source_utf8), POINTER(c_char))
        source_length = c_int(len(shader_source_utf8))

        shader_id = glCreateShader(_shader_types[self.type])
        glShaderSource(shader_id, 1, byref(source_buffer_pointer), source_length)
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

    def __repr__(self):
        return "{0}(id={1}, type={2})".format(self.__class__.__name__, self.id, self.type)


class ShaderProgram:
    """OpenGL Shader Program"""

    Uniform = namedtuple('Uniform', 'getter, setter')

    def __init__(self, *shaders):
        self._id = self._link_program(shaders)
        self._active = False

        self._uniforms = {}
        self._attributes = {}
        self._parse_all_uniforms()

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

    def __setitem__(self, key, value):
        if not self._active:
            raise Exception("Shader Program is not active.")

        try:
            uniform = self._uniforms[key]
        except KeyError("Uniform with the name `{0}` was not found.".format(key)):
            raise

        try:
            uniform.setter(value)
        except GLException:
            raise

    def __getitem__(self, item):
        try:
            uniform = self._uniforms[item]
        except KeyError("Uniform with the name `{0}` was not found.".format(item)):
            raise

        try:
            return uniform.getter()
        except GLException:
            raise

    def get_num_active(self, variable_type):
        """Get the number of active variables of the passed GL type.

        :param variable_type: GL_ACTIVE_ATTRIBUTES, GL_ACTIVE_UNIFORMS, etc.
        :return: int: number of active types of the queried type
        """
        num_active = GLint(0)
        glGetProgramiv(self._id, variable_type, byref(num_active))
        return num_active.value

    def _parse_all_uniforms(self):
        for index in range(self.get_num_active(GL_ACTIVE_UNIFORMS)):
            uniform_name, uniform_type, uniform_size = self.query_uniform(index)
            location = self.get_uniform_location(uniform_name)

            if location == -1:      # Skip uniforms that may be in Uniform Blocks
                continue

            try:
                gl_type, gl_setter, length, count = _uniform_setters[uniform_type]
                gl_getter = _uniform_getters[gl_type]

                # Create mini-buffer for getters and setters:
                buffer = (gl_type * length)()
                ptr = cast(buffer, POINTER(gl_type))

                # Create custom dedicated getters and setters for each uniform:
                getter = create_getter_function(self._id, location, gl_getter, buffer, length)
                setter = create_setter_function(location, gl_setter, buffer, length, count, ptr)

                if _debug_gl_shaders:
                    print("uniform name: {0}, type: {1}, size: {2}, location: {3}, length: {4}, "
                          "count: {5}".format(uniform_name, uniform_type,
                                              uniform_size, location, length, count))

            except KeyError:
                raise GLException("Unsupported Uniform type {0}".format(uniform_type))

            self._uniforms[uniform_name] = self.Uniform(getter, setter)

    def get_all_uniform_blocks(self):
        block_uniforms = []
        for index in range(self.get_num_active(GL_ACTIVE_UNIFORMS)):
            uniform_name, uniform_type, uniform_size = self.query_uniform(index)
            location = self.get_uniform_location(uniform_name)
            if location == -1:
                block_uniforms.append(uniform_name)

        uniform_blocks = []

        for index in range(self.get_num_active(GL_ACTIVE_UNIFORM_BLOCKS)):
            name = self.get_uniform_block_name(index)
            num_active = GLint()
            block_data_size = GLint()
            glGetActiveUniformBlockiv(self._id, index, GL_UNIFORM_BLOCK_DATA_SIZE, block_data_size)
            glGetActiveUniformBlockiv(self._id, index, GL_UNIFORM_BLOCK_ACTIVE_UNIFORMS, num_active)

            # print("UniBlockname:", name, num_active.value, block_data_size.value)

            # Query the indices and offsets of the uniforms:
            indices = (GLuint * num_active.value)()
            offsets = (GLint * len(indices))()

            indices_ptr = cast(addressof(indices), POINTER(GLint))
            offsets_ptr = cast(addressof(offsets), POINTER(GLint))

            glGetActiveUniformBlockiv(
                self._id, index, GL_UNIFORM_BLOCK_ACTIVE_UNIFORM_INDICES, indices_ptr)
            glGetActiveUniformsiv(
                self._id, num_active.value, indices, GL_UNIFORM_OFFSET, offsets_ptr)

            uniform_blocks.append({'name': name,
                                   'block_index': index,
                                   'active_uniforms': num_active.value,
                                   'block_size': block_data_size.value,
                                   'uniforms': block_uniforms,
                                   'indices': indices[:],
                                   'offsets': offsets[:]})
        return uniform_blocks

    def get_uniform_block_name(self, index):
        buf_size = 128
        size = c_int(0)
        name_buf = create_string_buffer(buf_size)
        try:
            glGetActiveUniformBlockName(self._id, index, buf_size, size, name_buf)
            return name_buf.value.decode()
        except GLException:
            return None

    def get_uniform_location(self, name):
        return glGetUniformLocation(self._id, create_string_buffer(name.encode('ascii')))

    def query_uniform(self, index):
        usize = GLint()
        utype = GLenum()
        buf_size = 192
        uname = create_string_buffer(buf_size)
        try:
            glGetActiveUniform(self._id, index, buf_size, None, usize, utype, uname)
            return uname.value.decode(), utype.value, usize.value
        except GLException:
            raise

    def __repr__(self):
        return "{0}(id={1})".format(self.__class__.__name__, self.id)


vertex_source = """#version 330 core
    in vec4 vertices;
    in vec4 colors;
    in vec2 tex_coords;
    out vec4 vertex_colors;
    out vec2 texture_coords;

    uniform vec2 window_size;
    uniform float zoom = 1.0;

    uniform WindowBlock
    {
        vec2 size;
        float aspect;
        float zooom;
    } window;

    void main()
    {
        gl_Position = vec4(vertices.x * 2.0 / window_size.x - 1.0 + window.aspect,
                           vertices.y * 2.0 / window_size.y - 1.0 + window.aspect,
                           vertices.z,
                           vertices.w * zoom + window.zooom);

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
        final_colors = texture(our_texture, texture_coords) + vertex_colors;
    }
"""
