from ctypes import *
from weakref import proxy

import pyglet

from pyglet.gl import *
from pyglet.graphics.vertexbuffer import BufferObject


_debug_gl_shaders = pyglet.options['debug_gl_shaders']


class ShaderException(BaseException):
    pass


_c_types = {
    GL_BYTE: c_byte,
    GL_UNSIGNED_BYTE: c_ubyte,
    GL_SHORT: c_short,
    GL_UNSIGNED_SHORT: c_ushort,
    GL_INT: c_int,
    GL_UNSIGNED_INT: c_uint,
    GL_FLOAT: c_float,
    GL_DOUBLE: c_double,
}

_shader_types = {
    'compute':        GL_COMPUTE_SHADER,
    'fragment':       GL_FRAGMENT_SHADER,
    'geometry':       GL_GEOMETRY_SHADER,
    'tesscontrol':    GL_TESS_CONTROL_SHADER,
    'tessevaluation': GL_TESS_EVALUATION_SHADER,
    'vertex':         GL_VERTEX_SHADER,
}

_uniform_getters = {
    GLint:     glGetUniformiv,
    GLfloat:   glGetUniformfv,
    GLboolean: glGetUniformiv,
}

_uniform_setters = {
    # uniform:    gl_type, legacy_setter, setter, length, count
    GL_BOOL:      (GLint, glUniform1iv, glProgramUniform1iv, 1, 1),
    GL_BOOL_VEC2: (GLint, glUniform1iv, glProgramUniform1iv, 2, 1),
    GL_BOOL_VEC3: (GLint, glUniform1iv, glProgramUniform1iv, 3, 1),
    GL_BOOL_VEC4: (GLint, glUniform1iv, glProgramUniform1iv, 4, 1),

    GL_INT:      (GLint, glUniform1iv, glProgramUniform1iv, 1, 1),
    GL_INT_VEC2: (GLint, glUniform2iv, glProgramUniform2iv, 2, 1),
    GL_INT_VEC3: (GLint, glUniform3iv, glProgramUniform3iv, 3, 1),
    GL_INT_VEC4: (GLint, glUniform4iv, glProgramUniform4iv, 4, 1),

    GL_FLOAT:      (GLfloat, glUniform1fv, glProgramUniform1fv, 1, 1),
    GL_FLOAT_VEC2: (GLfloat, glUniform2fv, glProgramUniform2fv, 2, 1),
    GL_FLOAT_VEC3: (GLfloat, glUniform3fv, glProgramUniform3fv, 3, 1),
    GL_FLOAT_VEC4: (GLfloat, glUniform4fv, glProgramUniform4fv, 4, 1),

    GL_SAMPLER_1D:       (GLint, glUniform1iv, glProgramUniform1iv, 1, 1),
    GL_SAMPLER_2D:       (GLint, glUniform1iv, glProgramUniform1iv, 1, 1),
    GL_SAMPLER_2D_ARRAY: (GLint, glUniform1iv, glProgramUniform1iv, 1, 1),
        
    GL_SAMPLER_3D: (GLint, glUniform1iv, glProgramUniform1iv, 1, 1),

    GL_FLOAT_MAT2: (GLfloat, glUniformMatrix2fv, glProgramUniformMatrix2fv, 4, 1),
    GL_FLOAT_MAT3: (GLfloat, glUniformMatrix3fv, glProgramUniformMatrix3fv, 6, 1),
    GL_FLOAT_MAT4: (GLfloat, glUniformMatrix4fv, glProgramUniformMatrix4fv, 16, 1),

    # TODO: test/implement these:
    # GL_FLOAT_MAT2x3: glUniformMatrix2x3fv, glProgramUniformMatrix2x3fv,
    # GL_FLOAT_MAT2x4: glUniformMatrix2x4fv, glProgramUniformMatrix2x4fv,
    # GL_FLOAT_MAT3x2: glUniformMatrix3x2fv, glProgramUniformMatrix3x2fv,
    # GL_FLOAT_MAT3x4: glUniformMatrix3x4fv, glProgramUniformMatrix3x4fv,
    # GL_FLOAT_MAT4x2: glUniformMatrix4x2fv, glProgramUniformMatrix4x2fv,
    # GL_FLOAT_MAT4x3: glUniformMatrix4x3fv, glProgramUniformMatrix4x3fv,

    GL_IMAGE_1D:       (GLint, glUniform1iv, glProgramUniform1iv, 1, 1),
    GL_IMAGE_2D:       (GLint, glUniform1iv, glProgramUniform1iv, 2, 1),
    GL_IMAGE_2D_RECT:  (GLint, glUniform1iv, glProgramUniform1iv, 3, 1),
    GL_IMAGE_3D:       (GLint, glUniform1iv, glProgramUniform1iv, 3, 1),

    GL_IMAGE_1D_ARRAY: (GLint, glUniform1iv, glProgramUniform1iv, 2, 1),
    GL_IMAGE_2D_ARRAY: (GLint, glUniform1iv, glProgramUniform1iv, 3, 1),

    GL_IMAGE_2D_MULTISAMPLE:       (GLint, glUniform1iv, glProgramUniform1iv, 2, 1),
    GL_IMAGE_2D_MULTISAMPLE_ARRAY: (GLint, glUniform1iv, glProgramUniform1iv, 3, 1),

    GL_IMAGE_BUFFER:         (GLint, glUniform1iv, glProgramUniform1iv, 3, 1),
    GL_IMAGE_CUBE:           (GLint, glUniform1iv, glProgramUniform1iv, 1, 1),
    GL_IMAGE_CUBE_MAP_ARRAY: (GLint, glUniform1iv, glProgramUniform1iv, 3, 1),
}

_attribute_types = {
    GL_BOOL:      (1, '?'),
    GL_BOOL_VEC2: (2, '?'),
    GL_BOOL_VEC3: (3, '?'),
    GL_BOOL_VEC4: (4, '?'),

    GL_INT:      (1, 'i'),
    GL_INT_VEC2: (2, 'i'),
    GL_INT_VEC3: (3, 'i'),
    GL_INT_VEC4: (4, 'i'),

    GL_UNSIGNED_INT:      (1, 'I'),
    GL_UNSIGNED_INT_VEC2: (2, 'I'),
    GL_UNSIGNED_INT_VEC3: (3, 'I'),
    GL_UNSIGNED_INT_VEC4: (4, 'I'),

    GL_FLOAT:      (1, 'f'),
    GL_FLOAT_VEC2: (2, 'f'),
    GL_FLOAT_VEC3: (3, 'f'),
    GL_FLOAT_VEC4: (4, 'f'),

    GL_DOUBLE:      (1, 'd'),
    GL_DOUBLE_VEC2: (2, 'd'),
    GL_DOUBLE_VEC3: (3, 'd'),
    GL_DOUBLE_VEC4: (4, 'd'),
}


# Accessor classes:

class Attribute:
    """Abstract accessor for an attribute in a mapped buffer."""

    def __init__(self, name, location, count, gl_type, normalize):
        """Create the attribute accessor.

        :Parameters:
            `name` : str
                Name of the vertex attribute.
            `location` : int
                Location (index) of the vertex attribute.
            `count` : int
                Number of components in the attribute.
            `gl_type` : int
                OpenGL type enumerant; for example, ``GL_FLOAT``
            `normalize`: bool
                True if OpenGL should normalize the values

        """
        self.name = name
        self.location = location
        self.count = count

        self.gl_type = gl_type
        self.c_type = _c_types[gl_type]
        self.normalize = normalize

        self.align = sizeof(self.c_type)
        self.size = count * self.align
        self.stride = self.size

    def enable(self):
        """Enable the attribute."""
        glEnableVertexAttribArray(self.location)

    def set_pointer(self, ptr):
        """Setup this attribute to point to the currently bound buffer at
        the given offset.

        ``offset`` should be based on the currently bound buffer's ``ptr``
        member.

        :Parameters:
            `offset` : int
                Pointer offset to the currently bound buffer for this
                attribute.

        """
        glVertexAttribPointer(self.location, self.count, self.gl_type, self.normalize, self.stride, ptr)

    def get_region(self, buffer, start, count):
        """Map a buffer region using this attribute as an accessor.

        The returned region consists of a contiguous array of component
        data elements.  For example, if this attribute uses 3 floats per
        vertex, and the `count` parameter is 4, the number of floats mapped
        will be ``3 * 4 = 12``.

        :Parameters:
            `buffer` : `AbstractMappable`
                The buffer to map.
            `start` : int
                Offset of the first vertex to map.
            `count` : int
                Number of vertices to map

        :rtype: `AbstractBufferRegion`
        """
        byte_start = self.stride * start
        byte_size = self.stride * count
        array_count = self.count * count
        ptr_type = POINTER(self.c_type * array_count)
        return buffer.get_region(byte_start, byte_size, ptr_type)

    def set_region(self, buffer, start, count, data):
        """Set the data over a region of the buffer.

        :Parameters:
            `buffer` : AbstractMappable`
                The buffer to modify.
            `start` : int
                Offset of the first vertex to set.
            `count` : int
                Number of vertices to set.
            `data` : A sequence of data components.
        """
        byte_start = self.stride * start
        byte_size = self.stride * count
        array_count = self.count * count
        data = (self.c_type * array_count)(*data)
        buffer.set_data_region(data, byte_start, byte_size)

    def __repr__(self):
        return f"Attribute(name='{self.name}', location={self.location}, count={self.count})"


class _Uniform:
    __slots__ = 'program', 'name', 'type', 'location', 'length', 'count', 'get', 'set'

    def __init__(self, program, name, uniform_type, location, dsa):
        self.program = program
        self.name = name
        self.type = uniform_type
        self.location = location

        gl_type, gl_setter_legacy, gl_setter_dsa, length, count = _uniform_setters[uniform_type]
        gl_setter = gl_setter_dsa if dsa else gl_setter_legacy
        gl_getter = _uniform_getters[gl_type]

        self.length = length
        self.count = count

        is_matrix = uniform_type in (GL_FLOAT_MAT2, GL_FLOAT_MAT2x3, GL_FLOAT_MAT2x4,
                                     GL_FLOAT_MAT3, GL_FLOAT_MAT3x2, GL_FLOAT_MAT3x4,
                                     GL_FLOAT_MAT4, GL_FLOAT_MAT4x2, GL_FLOAT_MAT4x3)

        c_array = (gl_type * length)()
        ptr = cast(c_array, POINTER(gl_type))

        self.get = self._create_getter_func(program, location, gl_getter, c_array, length)
        self.set = self._create_setter_func(program, location, gl_setter, c_array, length, count, ptr, is_matrix, dsa)

    @staticmethod
    def _create_getter_func(program, location, gl_getter, c_array, length):
        """Factory function for creating simplified Uniform getters"""

        if length == 1:
            def getter_func():
                gl_getter(program, location, c_array)
                return c_array[0]
        else:
            def getter_func():
                gl_getter(program, location, c_array)
                return c_array[:]

        return getter_func

    @staticmethod
    def _create_setter_func(program, location, gl_setter, c_array, length, count, ptr, is_matrix, dsa):
        """Factory function for creating simplified Uniform setters"""
        if dsa:     # Bindless updates:

            if is_matrix:
                def setter_func(value):
                    c_array[:] = value
                    gl_setter(program, location, count, GL_FALSE, ptr)
            elif length == 1 and count == 1:
                def setter_func(value):
                    c_array[0] = value
                    gl_setter(program, location, count, ptr)
            elif length > 1 and count == 1:
                def setter_func(values):
                    c_array[:] = values
                    gl_setter(program, location, count, ptr)
            else:
                raise ShaderException("Uniform type not yet supported.")

            return setter_func

        else:

            if is_matrix:
                def setter_func(value):
                    glUseProgram(program)
                    c_array[:] = value
                    gl_setter(location, count, GL_FALSE, ptr)
            elif length == 1 and count == 1:
                def setter_func(value):
                    glUseProgram(program)
                    c_array[0] = value
                    gl_setter(location, count, ptr)
            elif length > 1 and count == 1:
                def setter_func(values):
                    glUseProgram(program)
                    c_array[:] = values
                    gl_setter(location, count, ptr)
            else:
                raise ShaderException("Uniform type not yet supported.")

            return setter_func

    def __repr__(self):
        return f"Uniform('{self.name}', location={self.location}, length={self.length}, count={self.count})"


class UniformBlock:
    __slots__ = 'program', 'name', 'index', 'size', 'uniforms', 'view_cls'

    def __init__(self, program, name, index, size, uniforms):
        self.program = proxy(program)
        self.name = name
        self.index = index
        self.size = size
        self.uniforms = uniforms
        self.view_cls = None

    def create_ubo(self, index=0):
        """
        Create a new UniformBufferObject from this uniform block.

        :Parameters:
            `index` : int
                The uniform buffer index the returned UBO will bind itself to.
                By default, this is 0.

        :rtype: :py:class:`~pyglet.graphics.shader.UniformBufferObject`
        """
        if self.view_cls is None:
            self.view_cls = self._introspect_uniforms()
        return UniformBufferObject(self.view_cls, self.size, index)

    def _introspect_uniforms(self):
        """Introspect the block's structure and return a ctypes struct for
        manipulating the uniform block's members.
        """
        p_id = self.program.id
        index = self.index

        active_count = len(self.uniforms)

        # Query the uniform index order and each uniform's offset:
        indices = (GLuint * active_count)()
        offsets = (GLint * active_count)()
        indices_ptr = cast(addressof(indices), POINTER(GLint))
        offsets_ptr = cast(addressof(offsets), POINTER(GLint))
        glGetActiveUniformBlockiv(p_id, index, GL_UNIFORM_BLOCK_ACTIVE_UNIFORM_INDICES, indices_ptr)
        glGetActiveUniformsiv(p_id, active_count, indices, GL_UNIFORM_OFFSET, offsets_ptr)

        # Offsets may be returned in non-ascending order, sort them with the corresponding index:
        _oi = sorted(zip(offsets, indices), key=lambda x: x[0])
        offsets = [x[0] for x in _oi] + [self.size]
        indices = (GLuint * active_count)(*(x[1] for x in _oi))

        # # Query other uniform information:
        # gl_types = (GLint * active_count)()
        # mat_stride = (GLint * active_count)()
        # gl_types_ptr = cast(addressof(gl_types), POINTER(GLint))
        # stride_ptr = cast(addressof(mat_stride), POINTER(GLint))
        # glGetActiveUniformsiv(p_id, active_count, indices, GL_UNIFORM_TYPE, gl_types_ptr)
        # glGetActiveUniformsiv(p_id, active_count, indices, GL_UNIFORM_MATRIX_STRIDE, stride_ptr)

        view_fields = []
        for i in range(active_count):
            u_name, gl_type, length = self.uniforms[indices[i]]
            size = offsets[i+1] - offsets[i]
            c_type_size = sizeof(gl_type)
            actual_size = c_type_size * length
            padding = size - actual_size

            # TODO: handle stride for multiple matrixes in the same UBO (crashes now)
            # m_stride = mat_stride[i]

            arg = (u_name, gl_type * length) if length > 1 else (u_name, gl_type)
            view_fields.append(arg)

            if padding > 0:
                padding_bytes = padding // c_type_size
                view_fields.append((f'_padding{i}', gl_type * padding_bytes))

        # Custom ctypes Structure for Uniform access:
        class View(Structure):
            _fields_ = view_fields

            def __repr__(self):
                return str(dict(self._fields_))

        return View

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, index={self.index})"


class UniformBufferObject:
    __slots__ = 'buffer', 'view', '_view_ptr', 'index'

    def __init__(self, view_class, buffer_size, index):
        self.buffer = BufferObject(buffer_size)
        self.view = view_class()
        self._view_ptr = pointer(self.view)
        self.index = index

    @property
    def id(self):
        return self.buffer.id

    def bind(self, index=None):
        glBindBufferBase(GL_UNIFORM_BUFFER, self.index if index is None else index, self.buffer.id)

    def read(self):
        """Read the byte contents of the buffer"""
        glBindBuffer(GL_ARRAY_BUFFER, self.buffer.id)
        ptr = glMapBufferRange(GL_ARRAY_BUFFER, 0, self.buffer.size, GL_MAP_READ_BIT)
        data = string_at(ptr, size=self.buffer.size)
        glUnmapBuffer(GL_ARRAY_BUFFER)
        return data

    def __enter__(self):
        # Return the view to the user in a `with` context:
        return self.view

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.bind()
        self.buffer.set_data(self._view_ptr)

    def __repr__(self):
        return "{0}(id={1})".format(self.__class__.__name__, self.buffer.id)


# Utility functions:

def _get_number(program_id: int, variable_type: int) -> int:
    """Get the number of active variables of the passed GL type."""
    number = GLint(0)
    glGetProgramiv(program_id, variable_type, byref(number))
    return number.value


def _query_attribute(program_id: int, index: int):
    """Query the name, type, and size of an Attribute by index."""
    asize = GLint()
    atype = GLenum()
    buf_size = 192
    aname = create_string_buffer(buf_size)
    try:
        glGetActiveAttrib(program_id, index, buf_size, None, asize, atype, aname)
        return aname.value.decode(), atype.value, asize.value
    except GLException as exc:
        raise ShaderException from exc


def _introspect_attributes(program_id: int) -> dict:
    """Introspect a Program's Attributes, and return a dict of accessors."""
    attributes = {}

    for index in range(_get_number(program_id, GL_ACTIVE_ATTRIBUTES)):
        a_name, a_type, a_size = _query_attribute(program_id, index)
        loc = glGetAttribLocation(program_id, create_string_buffer(a_name.encode('utf-8')))
        count, fmt = _attribute_types[a_type]
        attributes[a_name] = dict(type=a_type, size=a_size, location=loc, count=count, format=fmt)

    if _debug_gl_shaders:
        for attribute in attributes.values():
            print(f" Found attribute: {attribute}")

    return attributes


def _link_program(*shaders) -> int:
    """Link one or more Shaders into a ShaderProgram."""
    program_id = glCreateProgram()
    for shader in shaders:
        glAttachShader(program_id, shader.id)
    glLinkProgram(program_id)

    # Check the link status of program
    status = c_int()
    glGetProgramiv(program_id, GL_LINK_STATUS, byref(status))
    if not status.value:
        length = c_int()
        glGetProgramiv(program_id, GL_INFO_LOG_LENGTH, length)
        log = c_buffer(length.value)
        glGetProgramInfoLog(program_id, len(log), None, log)
        raise ShaderException("Error linking shader program:\n{}".format(log.value.decode()))

    # Shader objects no longer needed
    for shader in shaders:
        glDetachShader(program_id, shader.id)

    return program_id


def _get_program_log(program_id: int) -> str:
    """Query a ShaderProgram link logs."""
    result = c_int(0)
    glGetProgramiv(program_id, GL_INFO_LOG_LENGTH, byref(result))
    result_str = create_string_buffer(result.value)
    glGetProgramInfoLog(program_id, result, None, result_str)

    if result_str.value:
        return f"OpenGL returned the following message when linking the program: \n{result_str.value}"
    else:
        return f"Program '{program_id}' linked successfully."


def _query_uniform(program_id: int, index: int):
    """Query the name, type, and size of a Uniform by index."""
    usize = GLint()
    utype = GLenum()
    buf_size = 192
    uname = create_string_buffer(buf_size)
    try:
        glGetActiveUniform(program_id, index, buf_size, None, usize, utype, uname)
        return uname.value.decode(), utype.value, usize.value

    except GLException as exc:
        raise ShaderException from exc


def _introspect_uniforms(program_id: int, have_dsa: bool) -> dict:
    """Introspect a Program's uniforms, and return a dict of accessors."""
    uniforms = {}

    for index in range(_get_number(program_id, GL_ACTIVE_UNIFORMS)):
        u_name, u_type, u_size = _query_uniform(program_id, index)
        loc = glGetUniformLocation(program_id, create_string_buffer(u_name.encode('utf-8')))
        if loc == -1:      # Skip uniforms that may be inside a Uniform Block
            continue
        uniforms[u_name] = _Uniform(program_id, u_name, u_type, loc, have_dsa)

    if _debug_gl_shaders:
        for uniform in uniforms.values():
            print(f" Found uniform: {uniform}")

    return uniforms


def _get_uniform_block_name(program_id: int, index: int) -> str:
    """Query the name of a Uniform Block, by index"""
    buf_size = 128
    size = c_int(0)
    name_buf = create_string_buffer(buf_size)
    try:
        glGetActiveUniformBlockName(program_id, index, buf_size, size, name_buf)
        return name_buf.value.decode()
    except GLException:
        raise ShaderException(f"Unable to query UniformBlock name at index: {index}")


def _introspect_uniform_blocks(program) -> dict:
    uniform_blocks = {}
    program_id = program.id

    for index in range(_get_number(program_id, GL_ACTIVE_UNIFORM_BLOCKS)):
        name = _get_uniform_block_name(program_id, index)

        num_active = GLint()
        block_data_size = GLint()

        glGetActiveUniformBlockiv(program_id, index, GL_UNIFORM_BLOCK_ACTIVE_UNIFORMS, num_active)
        glGetActiveUniformBlockiv(program_id, index, GL_UNIFORM_BLOCK_DATA_SIZE, block_data_size)

        indices = (GLuint * num_active.value)()
        indices_ptr = cast(addressof(indices), POINTER(GLint))
        glGetActiveUniformBlockiv(program_id, index, GL_UNIFORM_BLOCK_ACTIVE_UNIFORM_INDICES, indices_ptr)

        uniforms = {}

        for block_uniform_index in indices:
            uniform_name, u_type, u_size = _query_uniform(program_id, block_uniform_index)

            # Separate uniform name from block name (Only if instance name is provided on the Uniform Block)
            try:
                _, uniform_name = uniform_name.split(".")
            except ValueError:
                pass

            gl_type, _, _, length, _ = _uniform_setters[u_type]
            uniforms[block_uniform_index] = (uniform_name, gl_type, length)

        uniform_blocks[name] = UniformBlock(program, name, index, block_data_size.value, uniforms)
        # This might cause an error if index > GL_MAX_UNIFORM_BUFFER_BINDINGS, but surely no
        # one would be crazy enough to use more than 36 uniform blocks, right?
        glUniformBlockBinding(program_id, index, index)

        if _debug_gl_shaders:
            for block in uniform_blocks.values():
                print(f" Found uniform block: {block}")

    return uniform_blocks


# Program definitions:

class ShaderSource:
    """GLSL source container for making source parsing simpler.

    We support locating out attributes and applying #defines values.

    NOTE: We do assume the source is neat enough to be parsed
    this way and don't contain several statements in one line.
    """

    def __init__(self, source: str, source_type: GLenum):
        """Create a shader source wrapper."""
        self._lines = source.strip().splitlines()
        self._type = source_type

        if not self._lines:
            raise ShaderException("Shader source is empty")

        self._version = self._find_glsl_version()

        if pyglet.gl.current_context.get_info().get_opengl_api() == "gles":
            self._lines[0] = "#version 310 es"
            self._lines.insert(1, "precision mediump float;")

            if self._type == GL_GEOMETRY_SHADER:
                self._lines.insert(1, "#extension GL_EXT_geometry_shader : require")

            if self._type == GL_COMPUTE_SHADER:
                self._lines.insert(1, "precision mediump image2D;")

            self._version = self._find_glsl_version()

    def validate(self) -> str:
        """Return the validated shader source."""
        return "\n".join(self._lines)

    def _find_glsl_version(self) -> int:
        if self._lines[0].strip().startswith("#version"):
            try:
                return int(self._lines[0].split()[1])
            except (ValueError, IndexError):
                pass

        source = "\n".join(f"{str(i+1).zfill(3)}: {line} " for i, line in enumerate(self._lines))

        raise ShaderException(("Cannot find #version flag in shader source. "
                               "A #version statement is required on the first line.\n"
                               "------------------------------------\n"
                               f"{source}"))


class Shader:
    """OpenGL shader.

    Shader objects are compiled on instantiation.
    You can reuse a Shader object in multiple ShaderPrograms.

    `shader_type` is one of ``'compute'``, ``'fragment'``, ``'geometry'``,
    ``'tesscontrol'``, ``'tessevaluation'``, or ``'vertex'``.
    """

    def __init__(self, source_string: str, shader_type: str):
        self._id = None
        self.type = shader_type

        try:
            shader_type = _shader_types[shader_type]
        except KeyError as err:
            raise ShaderException(f"shader_type '{shader_type}' is invalid."
                                  f"Valid types are: {list(_shader_types)}") from err

        source_string = ShaderSource(source_string, shader_type).validate()
        shader_source_utf8 = source_string.encode("utf8")
        source_buffer_pointer = cast(c_char_p(shader_source_utf8), POINTER(c_char))
        source_length = c_int(len(shader_source_utf8))

        shader_id = glCreateShader(shader_type)
        glShaderSource(shader_id, 1, byref(source_buffer_pointer), source_length)
        glCompileShader(shader_id)

        status = c_int(0)
        glGetShaderiv(shader_id, GL_COMPILE_STATUS, byref(status))

        if status.value != GL_TRUE:
            source = self._get_shader_source(shader_id)
            source_lines = "{0}".format("\n".join(f"{str(i+1).zfill(3)}: {line} "
                                        for i, line in enumerate(source.split("\n"))))

            raise ShaderException(f"Shader compilation failed.\n"
                                  f"{self._get_shader_log(shader_id)}"
                                  "------------------------------------------------------------\n"
                                  f"{source_lines}\n"
                                  "------------------------------------------------------------")

        elif _debug_gl_shaders:
            print(self._get_shader_log(shader_id))

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
            return ("OpenGL returned the following message when compiling the '{0}' shader: "
                    "\n{1}".format(self.type, result_str.value.decode('utf8')))
        else:
            return f"{self.type.capitalize()} Shader '{shader_id}' compiled successfully."

    @staticmethod
    def _get_shader_source(shader_id):
        """Get the shader source from the shader object"""
        source_length = c_int(0)
        glGetShaderiv(shader_id, GL_SHADER_SOURCE_LENGTH, source_length)
        source_str = create_string_buffer(source_length.value)
        glGetShaderSource(shader_id, source_length, None, source_str)
        return source_str.value.decode('utf8')

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
    """OpenGL shader program."""

    __slots__ = '_id', '_context', '_attributes', '_uniforms', '_uniform_blocks', '__weakref__'

    def __init__(self, *shaders: Shader):
        assert shaders, "At least one Shader object is required."
        self._id = _link_program(*shaders)
        self._context = pyglet.gl.current_context

        if _debug_gl_shaders:
            print(_get_program_log(self._id))

        # Query if Direct State Access is available:
        have_dsa = gl_info.have_version(4, 1) or gl_info.have_extension("GL_ARB_separate_shader_objects")
        self._attributes = _introspect_attributes(self._id)
        self._uniforms = _introspect_uniforms(self._id, have_dsa)
        self._uniform_blocks = _introspect_uniform_blocks(self)

    @property
    def id(self):
        return self._id

    @property
    def attributes(self):
        return self._attributes

    @property
    def uniforms(self):
        return self._uniforms

    @property
    def uniform_blocks(self):
        return self._uniform_blocks

    def use(self):
        glUseProgram(self._id)

    @staticmethod
    def stop():
        glUseProgram(0)

    __enter__ = use
    bind = use
    unbind = stop

    def __exit__(self, *_):
        glUseProgram(0)

    def __del__(self):
        try:
            self._context.delete_shader_program(self.id)
        except Exception:
            # Interpreter is shutting down,
            # or ShaderProgram failed to link.
            pass

    def __setitem__(self, key, value):
        try:
            uniform = self._uniforms[key]
        except KeyError as err:
            raise ShaderException(f"A Uniform with the name `{key}` was not found.\n"
                                  f"The spelling may be incorrect, or if not in use it "
                                  f"may have been optimized out by the OpenGL driver.") from err
        try:
            uniform.set(value)
        except GLException as err:
            raise ShaderException from err

    def __getitem__(self, item):
        try:
            uniform = self._uniforms[item]
        except KeyError as err:
            raise ShaderException(f"A Uniform with the name `{item}` was not found.\n"
                                  f"The spelling may be incorrect, or if not in use it "
                                  f"may have been optimized out by the OpenGL driver.") from err
        try:
            return uniform.get()
        except GLException as err:
            raise ShaderException from err

    def vertex_list(self, count, mode, batch=None, group=None, **data):
        """Create a VertexList.

        :Parameters:
            `count` : int
                The number of vertices in the list.
            `mode` : int
                OpenGL drawing mode enumeration; for example, one of
                ``GL_POINTS``, ``GL_LINES``, ``GL_TRIANGLES``, etc.
                This determines how the list is drawn in the given batch.
            `batch` : `~pyglet.graphics.Batch`
                Batch to add the VertexList to, or ``None`` if a Batch will not be used.
                Using a Batch is strongly recommended.
            `group` : `~pyglet.graphics.Group`
                Group to add the VertexList to, or ``None`` if no group is required.
            `**data` : str or tuple
                Attribute formats and initial data for the vertex list.

        :rtype: :py:class:`~pyglet.graphics.vertexdomain.VertexList`
        """
        attributes = self._attributes.copy()
        initial_arrays = []

        for name, fmt in data.items():
            try:
                if isinstance(fmt, tuple):
                    fmt, array = fmt
                    initial_arrays.append((name, array))
                attributes[name] = {**attributes[name], **{'format': fmt}}
            except KeyError:
                raise ShaderException(f"\nThe attribute `{name}` doesn't exist. Valid names: \n{list(attributes)}")

        batch = batch or pyglet.graphics.get_default_batch()
        domain = batch.get_domain(False, mode, group, self, attributes)

        # Create vertex list and initialize
        vlist = domain.create(count)

        for name, array in initial_arrays:
            vlist.set_attribute_data(name, array)

        return vlist

    def vertex_list_indexed(self, count, mode, indices, batch=None, group=None, **data):
        """Create a IndexedVertexList.

        :Parameters:
            `count` : int
                The number of vertices in the list.
            `mode` : int
                OpenGL drawing mode enumeration; for example, one of
                ``GL_POINTS``, ``GL_LINES``, ``GL_TRIANGLES``, etc.
                This determines how the list is drawn in the given batch.
            `indices` : sequence of int
                Sequence of integers giving indices into the vertex list.
            `batch` : `~pyglet.graphics.Batch`
                Batch to add the VertexList to, or ``None`` if a Batch will not be used.
                Using a Batch is strongly recommended.
            `group` : `~pyglet.graphics.Group`
                Group to add the VertexList to, or ``None`` if no group is required.
            `**data` : str or tuple
                Attribute formats and initial data for the vertex list.

        :rtype: :py:class:`~pyglet.graphics.vertexdomain.IndexedVertexList`
        """
        attributes = self._attributes.copy()
        initial_arrays = []

        for name, fmt in data.items():
            try:
                if isinstance(fmt, tuple):
                    fmt, array = fmt
                    initial_arrays.append((name, array))
                attributes[name] = {**attributes[name], **{'format': fmt}}
            except KeyError:
                raise ShaderException(f"\nThe attribute `{name}` doesn't exist. Valid names: \n{list(attributes)}")

        batch = batch or pyglet.graphics.get_default_batch()
        domain = batch.get_domain(True, mode, group, self, attributes)

        # Create vertex list and initialize
        vlist = domain.create(count, len(indices))
        start = vlist.start
        vlist.indices = [i + start for i in indices]

        for name, array in initial_arrays:
            vlist.set_attribute_data(name, array)

        return vlist

    def __repr__(self):
        return "{0}(id={1})".format(self.__class__.__name__, self.id)


class ComputeShaderProgram:
    """OpenGL Compute Shader Program"""

    __slots__ = '_shader', '_id', '_context', '_uniforms', '_uniform_blocks', '__weakref__', 'limits'

    def __init__(self, source: str):
        """Create an OpenGL ComputeShaderProgram from source."""
        if not (gl_info.have_version(4, 3) or gl_info.have_extension("GL_ARB_compute_shader")):
            raise ShaderException("Compute Shader not supported. OpenGL Context version must be at least "
                                  "4.3 or higher, or 4.2 with the 'GL_ARB_compute_shader' extension.")

        self._shader = Shader(source, 'compute')
        self._context = pyglet.gl.current_context
        self._id = _link_program(self._shader)

        if _debug_gl_shaders:
            print(_get_program_log(self._id))

        self._uniforms = _introspect_uniforms(self._id, True)
        self._uniform_blocks = _introspect_uniform_blocks(self)

        self.limits = {
            'work_group_count':       self._get_tuple(GL_MAX_COMPUTE_WORK_GROUP_COUNT),
            'work_group_size':        self._get_tuple(GL_MAX_COMPUTE_WORK_GROUP_SIZE),
            'work_group_invocations': self._get_value(GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS),
            'shared_memory_size':     self._get_value(GL_MAX_COMPUTE_SHARED_MEMORY_SIZE),
        }

    @staticmethod
    def _get_tuple(parameter: int):
        val_x = GLint()
        val_y = GLint()
        val_z = GLint()
        for i, value in enumerate((val_x, val_y, val_z)):
            glGetIntegeri_v(parameter, i, byref(value))
        return val_x.value, val_y.value, val_z.value

    @staticmethod
    def _get_value(parameter: int) -> int:
        val = GLint()
        glGetIntegerv(parameter, byref(val))
        return val.value

    @staticmethod
    def dispatch(x: int = 1, y: int = 1, z: int = 1, barrier: int = GL_ALL_BARRIER_BITS) -> None:
        """Launch one or more compute work groups.

        The ComputeShaderProgram should be active (bound) before calling
        this method. The x, y, and z parameters specify the number of local
        work groups that will be  dispatched in the X, Y and Z dimensions.
        """
        glDispatchCompute(x, y, z)
        if barrier:
            glMemoryBarrier(barrier)

    @property
    def id(self) -> int:
        return self._id

    @property
    def uniforms(self) -> dict:
        return self._uniforms

    @property
    def uniform_blocks(self) -> dict:
        return self._uniform_blocks

    def use(self) -> None:
        glUseProgram(self._id)

    @staticmethod
    def stop():
        glUseProgram(0)

    __enter__ = use
    bind = use
    unbind = stop

    def __exit__(self, *_):
        glUseProgram(0)

    def __del__(self):
        try:
            self._context.delete_shader_program(self.id)
        except Exception:
            # Interpreter is shutting down,
            # or ShaderProgram failed to link.
            pass

    def __setitem__(self, key, value):
        try:
            uniform = self._uniforms[key]
        except KeyError as err:
            raise ShaderException(f"A Uniform with the name `{key}` was not found.\n"
                                  f"The spelling may be incorrect, or if not in use it "
                                  f"may have been optimized out by the OpenGL driver.") from err
        try:
            uniform.set(value)
        except GLException as err:
            raise ShaderException from err

    def __getitem__(self, item):
        try:
            uniform = self._uniforms[item]
        except KeyError as err:
            raise ShaderException(f"A Uniform with the name `{item}` was not found.\n"
                                  f"The spelling may be incorrect, or if not in use it "
                                  f"may have been optimized out by the OpenGL driver.") from err
        try:
            return uniform.get()
        except GLException as err:
            raise ShaderException from err
