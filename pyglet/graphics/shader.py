from ctypes import *

from pyglet.graphics.vertexbuffer import create_buffer
from pyglet import options
from pyglet.gl import *


_debug_gl_shaders = options['debug_gl_shaders']


# TODO: test other shader types, and update pyglet GL bindings if necessary.
_shader_types = {
    'vertex': GL_VERTEX_SHADER,
    'fragment': GL_FRAGMENT_SHADER,
    'geometry': GL_GEOMETRY_SHADER,
}

_uniform_getters = {
    GLint:   glGetUniformiv,
    GLfloat: glGetUniformfv,
}

_uniform_setters = {
    # uniform type: (gl_type, setter, length, count)
    GL_INT:      (GLint, glUniform1iv, 1, 1),
    GL_INT_VEC2: (GLint, glUniform2iv, 2, 1),
    GL_INT_VEC3: (GLint, glUniform3iv, 3, 1),
    GL_INT_VEC4: (GLint, glUniform4iv, 4, 1),

    GL_FLOAT:      (GLfloat, glUniform1fv, 1, 1),
    GL_FLOAT_VEC2: (GLfloat, glUniform2fv, 2, 1),
    GL_FLOAT_VEC3: (GLfloat, glUniform3fv, 3, 1),
    GL_FLOAT_VEC4: (GLfloat, glUniform4fv, 4, 1),

    GL_SAMPLER_2D: (GLint, glUniform1i, 1, 1),

    GL_FLOAT_MAT2: (GLfloat, glUniformMatrix2fv, 4, 1),
    GL_FLOAT_MAT3: (GLfloat, glUniformMatrix3fv, 6, 1),
    GL_FLOAT_MAT4: (GLfloat, glUniformMatrix4fv, 16, 1),

    # TODO: test/implement these:
    # GL_FLOAT_MAT2x3: glUniformMatrix2x3fv,
    # GL_FLOAT_MAT2x4: glUniformMatrix2x4fv,
    #
    # GL_FLOAT_MAT3x2: glUniformMatrix3x2fv,
    # GL_FLOAT_MAT3x4: glUniformMatrix3x4fv,
    #
    # GL_FLOAT_MAT4x2: glUniformMatrix4x2fv,
    # GL_FLOAT_MAT4x3: glUniformMatrix4x3fv,
}


class _Uniform:
    __slots__ = 'setter', 'getter'

    def __init__(self, setter, getter):
        self.setter = setter
        self.getter = getter


def _create_getter_func(program_id, location, gl_getter, c_array, length):
    """Factory function for creating simplified Uniform getters"""

    if length == 1:
        def getter_func():
            gl_getter(program_id, location, c_array)
            return c_array[0]
    else:
        def getter_func():
            gl_getter(program_id, location, c_array)
            return c_array[:]

    return getter_func


def _create_setter_func(location, gl_setter, c_array, length, count, ptr, is_matrix):
    """Factory function for creating simplified Uniform setters"""

    if is_matrix:
        def setter_func(value):
            c_array[:] = value
            gl_setter(location, count, GL_FALSE, ptr)

    elif length == 1 and count == 1:
        def setter_func(value):
            c_array[0] = value
            gl_setter(location, count, ptr)
    elif length > 1 and count == 1:
        def setter_func(values):
            c_array[:] = values
            gl_setter(location, count, ptr)

    else:
        raise NotImplementedError("Uniform type not yet supported.")

    return setter_func


class Shader:
    """OpenGL Shader object"""

    def __init__(self, source_string, shader_type):
        """Create an instance of a Shader object.

        Shader objects are compiled on instantiation. You can
        reuse a Shader object in multiple `ShaderProgram`s.

        :Parameters:
            `source_string` : str
                A string containing the Shader code.
            `shader_type` : str
                The Shader type, such as "vertex" or "fragment".
        """
        if shader_type not in _shader_types.keys():
            raise TypeError("The `shader_type` must be 'vertex' or 'fragment'.")
        self._source = source_string
        self.type = shader_type

        shader_source_utf8 = self._source.encode("utf8")
        source_buffer_pointer = cast(c_char_p(shader_source_utf8), POINTER(c_char))
        source_length = c_int(len(shader_source_utf8))

        shader_id = glCreateShader(_shader_types[self.type])
        glShaderSource(shader_id, 1, byref(source_buffer_pointer), source_length)
        glCompileShader(shader_id)

        status = c_int(0)
        glGetShaderiv(shader_id, GL_COMPILE_STATUS, byref(status))

        if status.value != GL_TRUE:
            raise GLException("The {0} shader failed to compile. "
                              "\n{1}".format(self.type, self._get_shader_log(shader_id)))
        elif _debug_gl_shaders:
            print("Shader compliation log: {0}".format(self._get_shader_log(shader_id)))

        self._id = shader_id

    @property
    def id(self):
        return self._id

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
            print("Destroyed {0} shader object id {1}.".format(self.type, self.id))

    def __repr__(self):
        return "{0}(id={1}, type={2})".format(self.__class__.__name__, self.id, self.type)


class ShaderProgram:
    """OpenGL Shader Program"""

    __slots__ = '_id', '_active', '_uniforms', '_uniform_blocks'

    # Cache UBOs to ensure all Shader Programs are using the same object.
    # If the UBOs are recreated each time, they will not
    uniform_buffers = {}

    def __init__(self, *shaders):
        """Create an OpenGL ShaderProgram, from multiple Shaders.

        Link one or more Shader objects together into a ShaderProgram.

        :Parameters:
            `shaders` : `Shader`
                One or more Shader objects
        """
        assert shaders, "At least one Shader object is required."
        self._id = self._link_program(shaders)
        self._active = False

        self._uniforms = {}
        self._uniform_blocks = {}

        self._introspect_uniforms()
        self._introspect_uniform_blocks()

        for block in self._uniform_blocks.values():
            if block.name in self.uniform_buffers:
                if _debug_gl_shaders:
                    print("Skipping cached Uniform Buffer Object: `{0}`".format(block.name))
                continue
            self.uniform_buffers[block.name] = UniformBufferObject(uniform_block=block)

        if _debug_gl_shaders:
            print(self._get_program_log())

    @property
    def id(self):
        return self._id

    @property
    def is_active(self):
        return self._active

    def _get_program_log(self):
        result = c_int(0)
        glGetProgramiv(self._id, GL_INFO_LOG_LENGTH, byref(result))
        result_str = create_string_buffer(result.value)
        glGetProgramInfoLog(self._id, result, None, result_str)
        if result_str.value:
            return ("OpenGL returned the following message when linking the program: "
                    "\n{0}".format(result_str.value))
        else:
            return "Program linked successfully."

    @staticmethod
    def _link_program(shaders):
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

    __enter__ = use_program

    __exit__ = stop_program

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
        except KeyError:
            raise Exception("Uniform with the name `{0}` was not found.".format(key))

        try:
            uniform.setter(value)
        except GLException:
            raise

    def __getitem__(self, item):
        try:
            uniform = self._uniforms[item]
        except KeyError:
            raise Exception("Uniform with the name `{0}` was not found.".format(item))

        try:
            return uniform.getter()
        except GLException:
            raise

    def _get_num_active(self, variable_type):
        """Get the number of active variables of the passed GL type."""
        num_active = GLint(0)
        glGetProgramiv(self._id, variable_type, byref(num_active))
        return num_active.value

    def _introspect_uniforms(self):
        for index in range(self._get_num_active(GL_ACTIVE_UNIFORMS)):
            uniform_name, u_type, u_size = self._query_uniform(index)
            loc = self._get_uniform_location(uniform_name)

            if loc == -1:      # Skip uniforms that may be in Uniform Blocks
                continue

            try:
                gl_type, gl_setter, length, count = _uniform_setters[u_type]
                gl_getter = _uniform_getters[gl_type]

                is_matrix = u_type in (GL_FLOAT_MAT2, GL_FLOAT_MAT2x3, GL_FLOAT_MAT2x4,
                                       GL_FLOAT_MAT3, GL_FLOAT_MAT3x2, GL_FLOAT_MAT3x4,
                                       GL_FLOAT_MAT4, GL_FLOAT_MAT4x2, GL_FLOAT_MAT4x3)

                # Create persistant mini c_array for getters and setters:
                c_array = (gl_type * length)()
                ptr = cast(c_array, POINTER(gl_type))

                # Create custom dedicated getters and setters for each uniform:
                getter = _create_getter_func(self._id, loc, gl_getter, c_array, length)
                setter = _create_setter_func(loc, gl_setter, c_array, length, count, ptr, is_matrix)

                if _debug_gl_shaders:
                    print("Found uniform: {0}, type: {1}, size: {2}, location: {3}, length: {4},"
                          " count: {5}".format(uniform_name, u_type, u_size, loc, length, count))

            except KeyError:
                raise GLException("Unsupported Uniform type {0}".format(u_type))

            self._uniforms[uniform_name] = _Uniform(setter=setter, getter=getter)

    def _introspect_uniform_blocks(self):
        p_id = self._id

        block_uniforms = {}

        for index in range(self._get_num_active(GL_ACTIVE_UNIFORMS)):
            uniform_name, u_type, u_size = self._query_uniform(index)
            location = self._get_uniform_location(uniform_name)
            if location == -1:
                block_name, uniform_name = uniform_name.split(".")
                if block_name not in block_uniforms:
                    block_uniforms[block_name] = {}

                gl_type, _, length, _ = _uniform_setters[u_type]

                block_uniforms[block_name][index] = (uniform_name, gl_type, length)

        for index in range(self._get_num_active(GL_ACTIVE_UNIFORM_BLOCKS)):
            name = self._get_uniform_block_name(index)
            num_active = GLint()
            block_data_size = GLint()
            glGetActiveUniformBlockiv(p_id, index, GL_UNIFORM_BLOCK_DATA_SIZE, block_data_size)
            glGetActiveUniformBlockiv(p_id, index, GL_UNIFORM_BLOCK_ACTIVE_UNIFORMS, num_active)

            block = UniformBlock(p_id, name, index, block_data_size.value, block_uniforms[name])
            self._uniform_blocks[name] = block

    def _get_uniform_block_name(self, index):
        buf_size = 128
        size = c_int(0)
        name_buf = create_string_buffer(buf_size)
        try:
            glGetActiveUniformBlockName(self._id, index, buf_size, size, name_buf)
            return name_buf.value.decode()
        except GLException:
            return None

    def _get_uniform_location(self, name):
        return glGetUniformLocation(self._id, create_string_buffer(name.encode('utf-8')))

    def _query_uniform(self, index):
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


class UniformBlock:
    __slots__ = 'program_id', 'name', 'index', 'size', 'uniforms'

    def __init__(self, program_id, name, index, size, uniforms):
        self.program_id = program_id
        self.name = name
        self.index = index
        self.size = size
        self.uniforms = uniforms

    def __repr__(self):
        return "{0}(name={1})".format(self.__class__.__name__, self.name)


class UniformBufferObject:
    __slots__ = 'block', 'buffer', 'view', '_view', '_view_ptr'

    def __init__(self, uniform_block):
        assert type(uniform_block) == UniformBlock, "Must be a UniformBlock instance"
        self.block = uniform_block
        self.buffer = create_buffer(self.block.size, target=GL_UNIFORM_BUFFER)
        glBindBufferBase(GL_UNIFORM_BUFFER, self.block.index, self.buffer.id)

        self.view = self._introspect_uniforms()
        self._view_ptr = pointer(self.view)

    def _introspect_uniforms(self):
        p_id = self.block.program_id
        index = self.block.index

        # Query the number of active Uniforms:
        num_active = GLint()
        indices = (GLuint * num_active.value)()
        indices_ptr = cast(addressof(indices), POINTER(GLint))
        glGetActiveUniformBlockiv(p_id, index, GL_UNIFORM_BLOCK_ACTIVE_UNIFORMS, num_active)
        glGetActiveUniformBlockiv(p_id, index, GL_UNIFORM_BLOCK_ACTIVE_UNIFORM_INDICES, indices_ptr)

        # Create objects and pointers for query values, to be used in the next step:
        offsets = (GLint * num_active.value)()
        gl_types = (GLuint * num_active.value)()
        mat_stride = (GLuint * num_active.value)()
        offsets_ptr = cast(addressof(offsets), POINTER(GLint))
        gl_types_ptr = cast(addressof(gl_types), POINTER(GLint))
        stride_ptr = cast(addressof(mat_stride), POINTER(GLint))

        # Query the indices, offsets, and types uniforms:
        glGetActiveUniformsiv(p_id, num_active.value, indices, GL_UNIFORM_OFFSET, offsets_ptr)
        glGetActiveUniformsiv(p_id, num_active.value, indices, GL_UNIFORM_TYPE, gl_types_ptr)
        glGetActiveUniformsiv(p_id, num_active.value, indices, GL_UNIFORM_MATRIX_STRIDE, stride_ptr)

        offsets = offsets[:] + [self.block.size]
        args = []

        for i in range(num_active.value):
            u_name, gl_type, length = self.block.uniforms[i]
            start = offsets[i]
            size = offsets[i+1] - start
            c_type_size = sizeof(gl_type)
            actual_size = c_type_size * length
            padding = size - actual_size
            # TODO: handle stride for multiple matrixes in the same UBO (crashes now)
            m_stride = mat_stride[i]

            arg = (u_name, gl_type * length) if length > 1 else (u_name, gl_type)
            args.append(arg)

            if padding > 0:
                padding_bytes = padding // c_type_size
                args.append(('_padding' + str(i), gl_type * padding_bytes))

        # Custom ctypes Structure for Uniform access:
        repr_fn = lambda self: str(dict(self._fields_))
        view = type(self.block.name + 'View', (Structure,), {'_fields_': args, '__repr__': repr_fn})

        return view()

    def __enter__(self):
        # Return the view to the user in a `with` context:
        return self.view

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.buffer.set_data(self._view_ptr)
        self.buffer.bind()

    def __repr__(self):
        return "{0}(id={1})".format(self.block.name + 'Buffer', self.buffer.id)
