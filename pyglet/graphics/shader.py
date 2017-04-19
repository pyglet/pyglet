from collections import namedtuple

from pyglet.gl import *
from ctypes import *


# TODO: test other shader types, and update pyglet GL bindings if necessary.
_shader_types = {
    'vertex': GL_VERTEX_SHADER,
    'fragment': GL_FRAGMENT_SHADER,
    # 'geometry': GL_GEOMETRY_SHADER,
}

Uniform = namedtuple('Uniform', 'location uniform_type')
Attribute = namedtuple('Attribute', 'location attribute_type')


class Shader:
    # TODO: create proper Exception for failed compilation.
    def __init__(self, source_string, shader_type):
        if shader_type not in _shader_types.keys():
            raise TypeError("Only vertex and fragment staders are currently supported")
        self._source = source_string
        self.shader_type = _shader_types[shader_type]
        self.id = self._compile_shader()

    def _compile_shader(self):
        shader_source = self._source.encode("utf8")
        shader_id = glCreateShader(self.shader_type)
        source_buffer = c_char_p(shader_source)
        source_buffer_pointer = cast(pointer(source_buffer), POINTER(POINTER(c_char)))
        source_length = c_int(len(shader_source) + 1)
        # shader id, count, string, length:
        glShaderSource(shader_id, 1, source_buffer_pointer, source_length)
        glCompileShader(shader_id)
        # TODO: use the pyglet debug settings
        self._get_shader_log(shader_id)
        return shader_id

    @staticmethod
    def _get_shader_log(shader_id):
        status = c_int(0)
        glGetShaderiv(shader_id, GL_COMPILE_STATUS, byref(status))
        log_length = c_int(0)
        glGetShaderiv(shader_id, GL_INFO_LOG_LENGTH, byref(log_length))
        result_str = create_string_buffer(log_length.value)
        glGetShaderInfoLog(shader_id, log_length, None, result_str)
        if result_str.value:
            print("Error compiling shader: {}".format(result_str.value.decode('utf8')))
        else:
            print("Shader compiled successfully.")

    def __del__(self):
        try:
            glDeleteShader(self.id)
        except ImportError:
            pass


class ShaderProgram:
    """OpenGL Shader Program"""
    def __init__(self, *shaders):
        self.id = self._link_program(shaders)
        self._program_active = False
        # TODO: move these out of this module eventually?
        self._uniforms = {}
        self._attributes = {}
        self._parse_all_uniforms()
        self._parse_all_attributes()

    @staticmethod
    def _get_program_log(program_id):
        result = c_int(0)
        # glGetProgramiv(program_id, GL_LINK_STATUS, byref(result))
        # glGetProgramiv(program_id, GL_ATTACHED_SHADERS, byref(result))
        glGetProgramiv(program_id, GL_INFO_LOG_LENGTH, byref(result))
        result_str = create_string_buffer(result.value)
        glGetProgramInfoLog(program_id, result, None, result_str)
        if result_str.value:
            print("Error linking program: {}".format(result_str.value))
        else:
            print("Program linked successfully")

    def _link_program(self, shaders):
        program_id = glCreateProgram()
        for shader in shaders:
            glAttachShader(program_id, shader.id)
        glLinkProgram(program_id)
        self._get_program_log(program_id)
        return program_id

    def use_program(self):
        glUseProgram(self.id)
        self._program_active = True

    def stop_program(self):
        glUseProgram(0)
        self._program_active = False

    def __enter__(self):
        self.use_program()

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop_program()

    def __del__(self):
        try:
            glDeleteProgram(self.id)
        except ImportError:
            pass

    ############################################################
    # Temporary methods that might better fit in another module:
    ############################################################

    def __setitem__(self, key, value):
        if key not in self._uniforms:
            raise KeyError("variable name was not found")
        if not self._program_active:
            raise Exception("Shader Program is not active.")

        location = self._uniforms[key].location
        uniform_type = self._uniforms[key].uniform_type
        # TODO: support setting other types
        try:
            glUniform1f(location, value)
        except GLException:
            raise

    def __getitem__(self, item):
        if item not in self._uniforms:
            raise KeyError("Uniform name was not found")

        location = self._uniforms[item].location
        variable_type = self._uniforms[item].uniform_type
        # TODO: support retrieving other types
        fetched_uniform = GLfloat()
        glGetUniformfv(self.id, location, fetched_uniform)

        return fetched_uniform.value

    def _parse_all_uniforms(self):
        for i in range(self.get_num_active(GL_ACTIVE_UNIFORMS)):
            uniform_name = self.get_active_uniform(i)
            uniform_type = self.get_uniform_type(uniform_name)
            location = self.get_uniform_location(uniform_name)
            self._uniforms[uniform_name] = Uniform(location, uniform_type)

    def _parse_all_attributes(self):
        for i in range(self.get_num_active(GL_ACTIVE_ATTRIBUTES)):
            attrib_name = self.get_active_attrib(i)
            attrib_type = self.get_attrib_type(attrib_name)
            location = self.get_attrib_location(attrib_name)
            self._attributes[attrib_name] = Attribute(location, attrib_type)

    def get_num_active(self, variable_type):
        """Get the number of active variables of the passed type.

        :param variable_type: Either GL_ACTIVE_ATTRIBUTES, or GL_ACTIVE_UNIFORMS
        :return:
        """
        num_active = GLint(0)
        glGetProgramiv(self.id, variable_type, byref(num_active))
        return num_active.value

    def get_attrib_type(self, name):
        location = self.get_attrib_location(name)
        if location == -1:
            print("Attribute name not found!")
        else:
            buf_size = 128
            size = GLint()
            attr_type = GLenum()
            name_buf = create_string_buffer(buf_size)
            glGetActiveAttrib(self.id, location, buf_size, None, size, attr_type, name_buf)
            return attr_type.value

    def get_uniform_type(self, name):
        location = self.get_uniform_location(name)
        if location == -1:
            print("Uniform name not found!")
        else:
            buf_size = 128
            size = GLint()
            uni_type = GLenum()
            name_buf = create_string_buffer(buf_size)
            glGetActiveUniform(self.id, location, buf_size, None, size, uni_type, name_buf)
            return uni_type.value

    def get_active_attrib(self, index):
        buf_size = 128
        size = c_int(0)
        attr_type = c_uint(0)
        name_buf = create_string_buffer(buf_size)
        try:
            glGetActiveAttrib(self.id, index, buf_size, None, size, attr_type, name_buf)
            return name_buf.value.decode()
        except GLException:
            return None

    def get_active_uniform(self, index):
        buf_size = 128
        size = c_int(0)
        attr_type = c_uint(0)
        name_buf = create_string_buffer(buf_size)
        try:
            glGetActiveUniform(self.id, index, buf_size, None, size, attr_type, name_buf)
            return name_buf.value.decode()
        except GLException:
            return None

    def get_attrib_location(self, name):
        return glGetAttribLocation(self.id, create_string_buffer(name.encode('ascii')))

    def get_uniform_location(self, name):
        return glGetUniformLocation(self.id, create_string_buffer(name.encode('ascii')))

    # def upload_data(self, vertices, name, size=3, stride=0, vert_pointer=0):
    #     location = self.get_attrib_location(name)
    #     if location == -1:
    #         return
    #     attr_type = GL_FLOAT
    #
    #     glBindVertexArray(self._vao_id)
    #     vertex_buffer = self._create_vertex_buffer()
    #     # self._vertex_buffers.append(vertex_buffer)
    #
    #     glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer.value)
    #     glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_DYNAMIC_DRAW)
    #
    #     glVertexAttribPointer(location, size, attr_type, False, stride, vert_pointer)
    #
    #     glEnableVertexAttribArray(location)
    #     glBindVertexArray(0)

    # def draw(self, mode, size):
    #     glBindVertexArray(self._vao_id)
    #     glDrawArrays(mode, 0, size)
    #     glBindVertexArray(0)
    #
    #     # glBindVertexArray(self._vertex_array)
    #     #
    #     # primcount = 1
    #     # starts = (GLint * primcount)()
    #     # sizes = (GLsizei * primcount)(size)
    #     # glMultiDrawArrays(mode, starts, sizes, primcount)
    #     #
    #     # glBindVertexArray(0)
