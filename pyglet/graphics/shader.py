from pyglet.gl import *
from ctypes import *


class ShaderProgram:
    """OpenGL Shader Program"""
    def __init__(self, vertex_source, fragment_source, debug=False):
        """Create an OpenGL Shader Program.

        Create an OpenGL Shader Program, that consists of vertex
        and fragment shaders.

        :param vertex_source: A string containing a GLSL vertex
        shader definition.
        :param fragment_source: A string containing a GLSL fragment
        shader definition.
        :param debug: If True, print some shader compilation logs
        and some error logs to the terminal.
        """
        self._debug = debug
        self._vertex = self._compile_shader(vertex_source, GL_VERTEX_SHADER)
        self._fragment = self._compile_shader(fragment_source, GL_FRAGMENT_SHADER)
        self._program = self._link_program()
        self._program_active = False
        # TODO: move these out of this module eventually?
        self._vertex_array = self._create_vertex_array()
        self._vertex_buffers = []
        self._variable_dict = {}
        self._parse_all_variables()

    def _compile_shader(self, shader_source, shader_type):
        shader_source = shader_source.encode("ascii")
        shader_id = glCreateShader(shader_type)
        source_buffer = c_char_p(shader_source)
        source_buffer_pointer = cast(pointer(source_buffer), POINTER(POINTER(c_char)))
        source_length = c_int(len(shader_source) + 1)
        # shader id, count, string, length:
        glShaderSource(shader_id, 1, source_buffer_pointer, source_length)
        glCompileShader(shader_id)

        if self._debug:
            self._get_shader_log(shader_id)

        return shader_id

    def _get_shader_log(self, shader_id):
        result = c_int(0)
        glGetShaderiv(shader_id, GL_COMPILE_STATUS, byref(result))
        glGetShaderiv(shader_id, GL_INFO_LOG_LENGTH, byref(result))
        result_str = create_string_buffer(result.value)
        glGetShaderInfoLog(shader_id, result, None, result_str)
        if self._debug:
            if result_str.value:
                print("Error compiling shader: {}".format(result_str.value))
            else:
                print("Shader compiled successfully")

    def _get_program_log(self, program_id):
        result = c_int(0)
        glGetProgramiv(program_id, GL_LINK_STATUS, byref(result))
        glGetProgramiv(program_id, GL_ATTACHED_SHADERS, byref(result))
        glGetProgramiv(program_id, GL_INFO_LOG_LENGTH, byref(result))
        result_str = create_string_buffer(result.value)
        glGetProgramInfoLog(program_id, result, None, result_str)
        if self._debug:
            if result_str.value:
                print("Error linking program: {}".format(result_str.value))
            else:
                print("Program linked successfully")

    def _link_program(self):
        program_id = glCreateProgram()
        glAttachShader(program_id, self._vertex)
        glAttachShader(program_id, self._fragment)
        glLinkProgram(program_id)
        glDeleteShader(self._vertex)
        glDeleteShader(self._fragment)

        if self._debug:
            self._get_program_log(program_id)

        return program_id

    def use_program(self):
        glUseProgram(self._program)
        self._program_active = True

    def stop_program(self):
        glUseProgram(0)
        self._program_active = False

    def __enter__(self):
        self.use_program()

    def __exit__(self, exception_type, exception_value, traceback):
        self.stop_program()

    def __del__(self):
        if self._program:
            try:
                glDeleteProgram(self._program)
            except ImportError:
                pass

    ############################################################
    # Temporary methods that might better fit in another module:
    ############################################################

    def __setitem__(self, key, value):
        if key not in self._variable_dict:
            raise KeyError("variable name was not found")
        # TODO: unset the program afterwards, if it wasn't active?
        if not self._program_active:
            self.use_program()

        location = self._variable_dict[key]['location']
        variable_type = self._variable_dict[key]['var_type']
        # TODO: support setting other types
        try:
            glUniform1f(location, value)
        except GLException:
            raise

    def __getitem__(self, item):

        if item not in self._variable_dict:
            raise KeyError("variable name was not found")

        location = self._variable_dict[item]['location']
        variable_type = self._variable_dict[item]['var_type']
        # TODO: support retrieving other types
        fetched_uniform = GLfloat()
        glGetUniformfv(self._program, location, fetched_uniform)

        return fetched_uniform.value

    def _create_vertex_buffer(self):
        vertex_buffer = GLuint(0)
        glGenBuffers(1, vertex_buffer)
        return vertex_buffer

    def _create_vertex_array(self):
        vertex_array = GLuint(0)
        glGenVertexArrays(1, vertex_array)
        return vertex_array

    def _parse_all_variables(self):
        # TODO: fill in other useful values
        for i in range(self.get_num_active(GL_ACTIVE_ATTRIBUTES)):
            attrib_name = self.get_active_attrib(i)
            attrib_type = self.get_attrib_type(attrib_name)
            location = self.get_attrib_location(attrib_name)
            self._variable_dict[attrib_name] = dict(var_type=attrib_type,
                                                    location=location)
        for i in range(self.get_num_active(GL_ACTIVE_UNIFORMS)):
            uniform_name = self.get_active_uniform(i)
            uniform_type = self.get_uniform_type(uniform_name)
            location = self.get_uniform_location(uniform_name)
            self._variable_dict[uniform_name] = dict(var_type=uniform_type,
                                                     location=location)

    def get_num_active(self, variable_type):
        """Get the number of active variables of the passed type.

        :param variable_type: Either GL_ACTIVE_ATTRIBUTES, or GL_ACTIVE_UNIFORMS
        :return:
        """
        num_active = GLint(0)
        glGetProgramiv(self._program, variable_type, byref(num_active))
        return num_active.value

    def get_attrib_type(self, name):
        location = self.get_attrib_location(name)
        if location == -1 and self._debug:
            print("Attribute name not found!")
        else:
            buf_size = 128
            size = GLint()
            attr_type = GLenum()
            name_buf = create_string_buffer(buf_size)
            glGetActiveAttrib(self._program, location, buf_size, None, size, attr_type, name_buf)
            return attr_type.value

    def get_uniform_type(self, name):
        location = self.get_uniform_location(name)
        if location == -1 and self._debug:
            print("Uniform name not found!")
        else:
            buf_size = 128
            size = GLint()
            uni_type = GLenum()
            name_buf = create_string_buffer(buf_size)
            glGetActiveUniform(self._program, location, buf_size, None, size, uni_type, name_buf)
            return uni_type.value

    def get_active_attrib(self, index):
        buf_size = 128
        size = c_int(0)
        attr_type = c_uint(0)
        name_buf = create_string_buffer(buf_size)
        try:
            glGetActiveAttrib(self._program, index, buf_size, None, size, attr_type, name_buf)
            return name_buf.value.decode()
        except GLException:
            return None

    def get_active_uniform(self, index):
        buf_size = 128
        size = c_int(0)
        attr_type = c_uint(0)
        name_buf = create_string_buffer(buf_size)
        try:
            glGetActiveUniform(self._program, index, buf_size, None, size, attr_type, name_buf)
            return name_buf.value.decode()
        except GLException:
            return None

    def get_attrib_location(self, name):
        return glGetAttribLocation(self._program, create_string_buffer(name.encode('ascii')))

    def get_uniform_location(self, name):
        return glGetUniformLocation(self._program, create_string_buffer(name.encode('ascii')))

    def upload_data(self, vertices, name, size=3, stride=0, vert_pointer=0):
        location = self.get_attrib_location(name)
        if location == -1:
            return      # TODO: raise an exception
        attr_type = GL_FLOAT    # TODO: query this
        glBindVertexArray(self._vertex_array)
        vertex_buffer = self._create_vertex_buffer()
        self._vertex_buffers.append(vertex_buffer)
        glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer)
        glBufferData(GL_ARRAY_BUFFER, sizeof(vertices), vertices, GL_DYNAMIC_DRAW)
        glVertexAttribPointer(location, size, attr_type, False, stride, vert_pointer)
        glEnableVertexAttribArray(location)
        glBindVertexArray(0)

    def draw(self, mode, size):
        glBindVertexArray(self._vertex_array)
        glDrawArrays(mode, 0, size)
        glBindVertexArray(0)
