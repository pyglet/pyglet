import ctypes
from weakref import proxy
from ctypes import *

import pyglet

from pyglet.graphics import vertexbuffer
from pyglet.gl import *


_debug_gl_shaders = pyglet.options['debug_gl_shaders']


# TODO: test other shader types, and update if necessary.
shader_types = {
    'vertex': GL_VERTEX_SHADER,
    'geometry': GL_GEOMETRY_SHADER,
    'fragment': GL_FRAGMENT_SHADER,
}

_uniform_getters = {
    GLint:     glGetUniformiv,
    GLfloat:   glGetUniformfv,
    GLboolean: glGetUniformiv,
}

_uniform_setters = {
    # uniform type: (gl_type, setter, length, count)
    GL_BOOL:      (GLint, glUniform1iv, 1, 1),
    GL_BOOL_VEC2: (GLint, glUniform1iv, 2, 1),
    GL_BOOL_VEC3: (GLint, glUniform1iv, 3, 1),
    GL_BOOL_VEC4: (GLint, glUniform1iv, 4, 1),

    GL_INT:      (GLint, glUniform1iv, 1, 1),
    GL_INT_VEC2: (GLint, glUniform2iv, 2, 1),
    GL_INT_VEC3: (GLint, glUniform3iv, 3, 1),
    GL_INT_VEC4: (GLint, glUniform4iv, 4, 1),

    GL_FLOAT:      (GLfloat, glUniform1fv, 1, 1),
    GL_FLOAT_VEC2: (GLfloat, glUniform2fv, 2, 1),
    GL_FLOAT_VEC3: (GLfloat, glUniform3fv, 3, 1),
    GL_FLOAT_VEC4: (GLfloat, glUniform4fv, 4, 1),

    GL_SAMPLER_1D:       (GLint, glUniform1iv, 1, 1),
    GL_SAMPLER_2D:       (GLint, glUniform1iv, 1, 1),
    GL_SAMPLER_2D_ARRAY: (GLint, glUniform1iv, 1, 1),
        
    GL_SAMPLER_3D: (GLint, glUniform1iv, 1, 1),

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

_attribute_types = {
    GL_BOOL: (1, '?'),
    GL_BOOL_VEC2: (2, '?'),
    GL_BOOL_VEC3: (3, '?'),
    GL_BOOL_VEC4: (4, '?'),

    GL_INT: (1, 'i'),
    GL_INT_VEC2: (2, 'i'),
    GL_INT_VEC3: (3, 'i'),
    GL_INT_VEC4: (4, 'i'),

    GL_UNSIGNED_INT: (1, 'I'),
    GL_UNSIGNED_INT_VEC2: (2, 'I'),
    GL_UNSIGNED_INT_VEC3: (3, 'I'),
    GL_UNSIGNED_INT_VEC4: (4, 'I'),

    GL_FLOAT: (1, 'f'),
    GL_FLOAT_VEC2: (2, 'f'),
    GL_FLOAT_VEC3: (3, 'f'),
    GL_FLOAT_VEC4: (4, 'f'),

    GL_DOUBLE: (1, 'd'),
    GL_DOUBLE_VEC2: (2, 'd'),
    GL_DOUBLE_VEC3: (3, 'd'),
    GL_DOUBLE_VEC4: (4, 'd'),
}


class _Attribute:
    __slots__ = 'program', 'name', 'type', 'size', 'location', 'count', 'format'

    def __init__(self, program, name, attr_type, size, location):
        self.program = program
        self.name = name
        self.type = attr_type
        self.size = size
        self.location = location
        self.count, self.format = _attribute_types[attr_type]

    def __repr__(self):
        return f"Attribute('{self.name}', program={self.program}, " \
               f"location={self.location}, count={self.count}, format={self.format})"


class _Uniform:
    __slots__ = 'program', 'name', 'type', 'location', 'length', 'count', 'get', 'set'

    def __init__(self, program, name, uniform_type, gl_type, location, length, count, gl_setter, gl_getter):
        self.program = program
        self.name = name
        self.type = uniform_type
        self.location = location
        self.length = length
        self.count = count

        is_matrix = uniform_type in (GL_FLOAT_MAT2, GL_FLOAT_MAT2x3, GL_FLOAT_MAT2x4,
                                     GL_FLOAT_MAT3, GL_FLOAT_MAT3x2, GL_FLOAT_MAT3x4,
                                     GL_FLOAT_MAT4, GL_FLOAT_MAT4x2, GL_FLOAT_MAT4x3)

        c_array = (gl_type * length)()
        ptr = cast(c_array, POINTER(gl_type))

        self.get = self._create_getter_func(program, location, gl_getter, c_array, length)
        self.set = self._create_setter_func(location, gl_setter, c_array, length, count, ptr, is_matrix)

    @staticmethod
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

    @staticmethod
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

    def __repr__(self):
        return f"Uniform('{self.name}', location={self.location}, length={self.length}, count={self.count})"


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
        self._id = None

        if shader_type not in shader_types:
            raise TypeError("The `shader_type` '{}' is not yet supported".format(shader_type))
        self.type = shader_type

        shader_source_utf8 = source_string.encode("utf8")
        source_buffer_pointer = cast(c_char_p(shader_source_utf8), POINTER(c_char))
        source_length = c_int(len(shader_source_utf8))

        shader_id = glCreateShader(shader_types[shader_type])
        glShaderSource(shader_id, 1, byref(source_buffer_pointer), source_length)
        glCompileShader(shader_id)

        status = c_int(0)
        glGetShaderiv(shader_id, GL_COMPILE_STATUS, byref(status))

        if status.value != GL_TRUE:
            raise GLException("The {0} shader failed to compile. "
                              "\n{1}".format(self.type, self._get_shader_log(shader_id)))
        elif _debug_gl_shaders:
            print(f"Shader '{shader_id}' compilation log: '{self._get_shader_log(shader_id)}'")

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
            if _debug_gl_shaders:
                print(f"Destroyed {self.type} Shader '{self._id}'")
        except Exception:
            # Interpreter is shutting down,
            # or Shader failed to compile.
            pass

    def __repr__(self):
        return "{0}(id={1}, type={2})".format(self.__class__.__name__, self.id, self.type)


class ShaderProgram:
    """OpenGL Shader Program"""

    __slots__ = '_id', '_context', '_active', '_attributes', '_uniforms', '_uniform_blocks', '__weakref__'

    def __init__(self, *shaders):
        """Create an OpenGL ShaderProgram, from multiple Shaders.

        Link multiple Shader objects together into a ShaderProgram.

        :Parameters:
            `shaders` : `Shader`
                One or more Shader objects
        """
        assert shaders, "At least one Shader object is required."
        self._id = self._link_program(shaders)
        self._context = pyglet.gl.current_context
        self._active = False

        self._attributes = {}
        self._uniforms = {}
        self._uniform_blocks = {}

        self._introspect_attributes()
        self._introspect_uniforms()
        self._introspect_uniform_blocks()

        if _debug_gl_shaders:
            print(self._get_program_log())

    @property
    def id(self):
        return self._id

    @property
    def is_active(self):
        return self._active

    @property
    def attributes(self):
        return self._attributes

    @property
    def uniforms(self):
        return self._uniforms.keys()

    @property
    def uniform_blocks(self):
        return self._uniform_blocks

    @property
    def formats(self):
        return tuple(f"{atr.name}{atr.count}{atr.format}" for atr in self._attributes.values())

    def _get_program_log(self):
        result = c_int(0)
        glGetProgramiv(self._id, GL_INFO_LOG_LENGTH, byref(result))
        result_str = create_string_buffer(result.value)
        glGetProgramInfoLog(self._id, result, None, result_str)
        if result_str.value:
            return f"OpenGL returned the following message when linking the program: \n{result_str.value}"
        else:
            return f"Program '{self._id}' linked successfully."

    @staticmethod
    def _link_program(shaders):
        # TODO: catch exceptions when linking Program:
        program_id = glCreateProgram()
        for shader in shaders:
            glAttachShader(program_id, shader.id)
        glLinkProgram(program_id)
        for shader in shaders:
            glDetachShader(program_id, shader.id)
        return program_id

    def use(self):
        glUseProgram(self._id)
        self._active = True

    def stop(self):
        glUseProgram(0)
        self._active = False

    __enter__ = use
    bind = use
    unbind = stop

    def __exit__(self, *_):
        glUseProgram(0)
        self._active = False

    def __del__(self):
        try:
            self._context.delete_shader_program(self.id)
        except Exception:
            # Interpreter is shutting down,
            # or ShaderProgram failed to link.
            pass

    def __setitem__(self, key, value):
        if not self._active:
            raise Exception("Shader Program is not active.")

        try:
            uniform = self._uniforms[key]
        except KeyError:
            raise Exception("Uniform with the name `{0}` was not found.".format(key))

        try:
            uniform.set(value)
        except GLException:
            raise

    def __getitem__(self, item):
        try:
            uniform = self._uniforms[item]
        except KeyError:
            raise Exception("Uniform with the name `{0}` was not found.".format(item))

        try:
            return uniform.get()
        except GLException:
            raise

    def _get_number(self, variable_type):
        """Get the number of active variables of the passed GL type."""
        number = GLint(0)
        glGetProgramiv(self._id, variable_type, byref(number))
        return number.value

    def _introspect_attributes(self):
        program = self._id
        attributes = {}
        for index in range(self._get_number(GL_ACTIVE_ATTRIBUTES)):
            a_name, a_type, a_size = self._query_attribute(index)
            loc = glGetAttribLocation(program, create_string_buffer(a_name.encode('utf-8')))
            attributes[a_name] = _Attribute(program, a_name, a_type, a_size, loc)
        self._attributes = attributes

        if _debug_gl_shaders:
            for attribute in attributes.values():
                print(f"Found attribute: {attribute}")

    def _introspect_uniforms(self):
        prg_id = self._id
        for index in range(self._get_number(GL_ACTIVE_UNIFORMS)):
            u_name, u_type, u_size = self._query_uniform(index)
            loc = glGetUniformLocation(prg_id, create_string_buffer(u_name.encode('utf-8')))

            if loc == -1:      # Skip uniforms that may be inside of a Uniform Block
                continue

            try:
                gl_type, gl_setter, length, count = _uniform_setters[u_type]
                gl_getter = _uniform_getters[gl_type]

                if _debug_gl_shaders:
                    print("Found uniform: {0}, type: {1}, size: {2}, location: {3}, length: {4},"
                          " count: {5}".format(u_name, u_type, u_size, loc, length, count))

            except KeyError:
                raise GLException("Unsupported Uniform type {0}".format(u_type))

            self._uniforms[u_name] = _Uniform(prg_id, u_name, u_type, gl_type, loc, length, count, gl_setter, gl_getter)

    def _introspect_uniform_blocks(self):
        p_id = self._id

        uniform_blocks = {}

        for index in range(self._get_number(GL_ACTIVE_UNIFORM_BLOCKS)):
            name = self._get_uniform_block_name(index)

            uniform_blocks[name] = {}
            
            num_active = GLint()
            block_data_size = GLint()

            glGetActiveUniformBlockiv(p_id, index, GL_UNIFORM_BLOCK_DATA_SIZE, block_data_size)
            glGetActiveUniformBlockiv(p_id, index, GL_UNIFORM_BLOCK_ACTIVE_UNIFORMS, num_active)
            
            indices = (GLuint * num_active.value)()
            indices_ptr = cast(addressof(indices), POINTER(GLint))
            glGetActiveUniformBlockiv(p_id, index, GL_UNIFORM_BLOCK_ACTIVE_UNIFORM_INDICES, indices_ptr)
            
            for i in range(num_active.value):
                uniform_name, u_type, u_size = self._query_uniform(indices[i])
                
                # Separate uniform name from block name (Only if instance name is provided on the Uniform Block)
                try:
                    _, uniform_name = uniform_name.split(".")
                except ValueError:
                    pass
                
                gl_type, _, length, _ = _uniform_setters[u_type]
                
                uniform_blocks[name][i] = (uniform_name, gl_type, length)

            self._uniform_blocks[name] = UniformBlock(self, name, index, block_data_size.value, uniform_blocks[name])

    def _get_uniform_block_name(self, index):
        buf_size = 128
        size = c_int(0)
        name_buf = create_string_buffer(buf_size)
        try:
            glGetActiveUniformBlockName(self._id, index, buf_size, size, name_buf)
            return name_buf.value.decode()
        except GLException:
            return None

    def _query_attribute(self, index):
        asize = GLint()
        atype = GLenum()
        buf_size = 192
        aname = create_string_buffer(buf_size)
        try:
            glGetActiveAttrib(self._id, index, buf_size, None, asize, atype, aname)
            return aname.value.decode(), atype.value, asize.value
        except GLException:
            raise

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
    __slots__ = 'program', 'name', 'index', 'size', 'uniforms'

    def __init__(self, program, name, index, size, uniforms):
        self.program = proxy(program)
        self.name = name
        self.index = index
        self.size = size
        self.uniforms = uniforms

    def create_ubo(self, index=0):
        return UniformBufferObject(self, index)

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, index={self.index})"


class UniformBufferObject:
    __slots__ = 'block', 'buffer', 'view', '_view', '_view_ptr', 'index'

    def __init__(self, block, index):
        assert type(block) == UniformBlock, "Must be a UniformBlock instance"
        self.block = block
        self.buffer = vertexbuffer.create_buffer(self.block.size, target=GL_UNIFORM_BUFFER, mappable=False)
        self.buffer.bind()
        self.view = self._introspect_uniforms()
        self._view_ptr = pointer(self.view)
        self.index = index
        # glUniformBlockBinding(self.block.program.id, self.block.index, self.index)

    @property
    def id(self):
        return self.buffer.id

    def _introspect_uniforms(self):
        p_id = self.block.program.id
        index = self.block.index

        # Query the number of active Uniforms:
        num_active = GLint()
        glGetActiveUniformBlockiv(p_id, index, GL_UNIFORM_BLOCK_ACTIVE_UNIFORMS, num_active)

        # Query the uniform index order and each uniform's offset:
        indices = (GLuint * num_active.value)()
        offsets = (GLint * num_active.value)()
        indices_ptr = cast(addressof(indices), POINTER(GLint))
        offsets_ptr = cast(addressof(offsets), POINTER(GLint))
        glGetActiveUniformBlockiv(p_id, index, GL_UNIFORM_BLOCK_ACTIVE_UNIFORM_INDICES, indices_ptr)
        glGetActiveUniformsiv(p_id, num_active.value, indices, GL_UNIFORM_OFFSET, offsets_ptr)

        # Offsets may be returned in non-ascending order, sort them with the corresponding index:
        _oi = sorted(zip(offsets, indices), key=lambda x: x[0])
        offsets = [x[0] for x in _oi] + [self.block.size]
        indices = (GLuint * num_active.value)(*(x[1] for x in _oi))

        # Query other uniform information:
        gl_types = (GLint * num_active.value)()
        mat_stride = (GLint * num_active.value)()
        gl_types_ptr = cast(addressof(gl_types), POINTER(GLint))
        stride_ptr = cast(addressof(mat_stride), POINTER(GLint))
        glGetActiveUniformsiv(p_id, num_active.value, indices, GL_UNIFORM_TYPE, gl_types_ptr)
        glGetActiveUniformsiv(p_id, num_active.value, indices, GL_UNIFORM_MATRIX_STRIDE, stride_ptr)

        args = []

        for i in range(num_active.value):
            u_name, gl_type, length = self.block.uniforms[indices[i]]
            size = offsets[i+1] - offsets[i]
            c_type_size = sizeof(gl_type)
            actual_size = c_type_size * length
            padding = size - actual_size

            # TODO: handle stride for multiple matrixes in the same UBO (crashes now)
            m_stride = mat_stride[i]

            arg = (u_name, gl_type * length) if length > 1 else (u_name, gl_type)
            args.append(arg)

            if padding > 0:
                padding_bytes = padding // c_type_size
                args.append((f'_padding{i}', gl_type * padding_bytes))

        # Custom ctypes Structure for Uniform access:
        class View(ctypes.Structure):
            _fields_ = args
            __repr__ = lambda self: str(dict(self._fields_))

        return View()

    def bind(self, index=None):
        glUniformBlockBinding(self.block.program.id, self.block.index, index or self.index)
        glBindBufferBase(GL_UNIFORM_BUFFER, index or self.index, self.buffer.id)

    def read(self):
        """Read the byte contents of the buffer"""
        glBindBuffer(GL_UNIFORM_BUFFER, self.buffer.id)
        ptr = glMapBufferRange(GL_UNIFORM_BUFFER, 0, self.buffer.size, GL_MAP_READ_BIT)
        data = string_at(ptr, size=self.buffer.size)
        glUnmapBuffer(GL_UNIFORM_BUFFER)
        return data

    def __enter__(self):
        # Return the view to the user in a `with` context:
        glUniformBlockBinding(self.block.program.id, self.block.index, self.index)
        glBindBufferBase(GL_UNIFORM_BUFFER, self.index, self.buffer.id)
        return self.view

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.buffer.set_data(self._view_ptr)

    def __repr__(self):
        return "{0}(id={1})".format(self.block.name + 'Buffer', self.buffer.id)
