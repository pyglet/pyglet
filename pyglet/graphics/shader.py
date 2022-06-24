from ctypes import *
from weakref import proxy

import pyglet

from pyglet.graphics.vertexbuffer import BufferObject
from pyglet.gl import *


_debug_gl_shaders = pyglet.options['debug_gl_shaders']


class ShaderException(BaseException):
    pass


# TODO: test other shader types, and update if necessary.
_shader_types = {
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
                raise NotImplementedError("Uniform type not yet supported.")

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
                raise NotImplementedError("Uniform type not yet supported.")

            return setter_func

    def __repr__(self):
        return f"Uniform('{self.name}', location={self.location}, length={self.length}, count={self.count})"


class ShaderSource:
    """GLSL source container for making source parsing simpler.

    We support locating out attributes and applying #defines values.

    NOTE: We do assume the source is neat enough to be parsed
    this way and don't contain several statements in one line.
    """

    def __init__(self, source: str, source_type: gl.GLenum):
        """Create a shader source wrapper."""
        self._lines = source.strip().splitlines()
        self._type = source_type

        if not self._lines:
            raise ValueError("Shader source is empty")

        self._version = self._find_glsl_version()

        if pyglet.gl.current_context.get_info().get_opengl_api() == "gles":
            self._lines[0] = "#version 310 es"
            self._lines.insert(1, "precision mediump float;")

            if self._type == gl.GL_GEOMETRY_SHADER:
                self._lines.insert(1, "#extension GL_EXT_geometry_shader : require")

            if self._type == gl.GL_COMPUTE_SHADER:
                self._lines.insert(1, "precision mediump image2D;")

            self._version = self._find_glsl_version()

    def validate(self) -> str:
        """Return the validated shader source."""
        return "\n".join(self._lines)

    def _find_glsl_version(self) -> int:
        if self._lines[0].strip().startswith("#version"):
            try:
                return int(self._lines[0].split()[1])
            except Exception:
                pass

        source = "\n".join(f"{str(i+1).zfill(3)}: {line} " for i, line in enumerate(self._lines))

        raise ShaderException(("Cannot find #version flag in shader source. "
                               "A #version statement is required on the first line.\n"
                               "------------------------------------\n"
                               f"{source}"))


class Shader:
    """OpenGL Shader object"""

    def __init__(self, source_string, shader_type):
        """Create an instance of a Shader object.

        Shader objects are compiled on instantiation. You can
        reuse a Shader object in multiple `ShaderProgram`s.

        :Parameters:
            `source_string` : str
                A string containing the Shader source code.
            `shader_type` : str
                The Shader type, such as "vertex", "fragment", "geometry", etc.
        """
        self._id = None

        if shader_type not in _shader_types:
            raise TypeError("The `shader_type` '{}' is not yet supported".format(shader_type))
        self.type = shader_type

        source_string = ShaderSource(source_string, _shader_types[shader_type]).validate()
        shader_source_utf8 = source_string.encode("utf8")
        source_buffer_pointer = cast(c_char_p(shader_source_utf8), POINTER(c_char))
        source_length = c_int(len(shader_source_utf8))

        shader_id = glCreateShader(_shader_types[shader_type])
        glShaderSource(shader_id, 1, byref(source_buffer_pointer), source_length)
        glCompileShader(shader_id)

        status = c_int(0)
        glGetShaderiv(shader_id, GL_COMPILE_STATUS, byref(status))

        if status.value != GL_TRUE:
            source = self._get_shader_source(shader_id)
            source_lines = "{0}".format("\n".join(f"{str(i+1).zfill(3)}: {line} "
                                        for i, line in enumerate(source.split("\n"))))
            raise GLException(
                (
                    f"The {self.type} shader failed to compile.\n"
                    f"{self._get_shader_log(shader_id)}"
                    "------------------------------------------------------------\n"
                    f"{source_lines}\n"
                    "------------------------------------------------------------"
                )
            )
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
            return ("OpenGL returned the following message when compiling the {0} shader: "
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
    """OpenGL Shader Program"""

    __slots__ = '_id', '_context', '_attributes', '_uniforms', '_uniform_blocks', '__weakref__', '_dsa'

    def __init__(self, *shaders):
        """Create an OpenGL ShaderProgram, from multiple Shaders.

        Link multiple Shader objects together into a ShaderProgram.

        :Parameters:
            `shaders` : `Shader`
                One or more Shader objects
        """
        assert shaders, "At least one Shader object is required."
        self._id = self._link_program(shaders)
        if _debug_gl_shaders:
            print(self._get_program_log())
        self._context = pyglet.gl.current_context
        # Query if Direct State Access is available:
        self._dsa = gl_info.have_version(4, 1) or gl_info.have_extension("GL_ARB_separate_shader_objects")

        self._attributes = self._introspect_attributes()
        self._uniforms = self._introspect_uniforms()
        self._uniform_blocks = self._introspect_uniform_blocks()

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
        program_id = glCreateProgram()
        for shader in shaders:
            glAttachShader(program_id, shader.id)
        glLinkProgram(program_id)

        # Check the link status of program
        status = c_int()
        glGetProgramiv(program_id, GL_LINK_STATUS, status)
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

    def use(self):
        glUseProgram(self._id)

    def stop(self):
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
        except KeyError:
            raise Exception(f"A Uniform with the name `{key}` was not found.\n"
                            f"The spelling may be incorrect, or if not in use it "
                            f"may have been optimized out by the OpenGL driver.")
        try:
            uniform.set(value)
        except GLException:
            raise

    def __getitem__(self, item):
        try:
            uniform = self._uniforms[item]
        except KeyError:
            raise Exception(f"A Uniform with the name `{item}` was not found.\n"
                            f"The spelling may be incorrect, or if not in use it "
                            f"may have been optimized out by the OpenGL driver.")
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
            count, fmt = _attribute_types[a_type]
            attributes[a_name] = dict(type=a_type, size=a_size, location=loc, count=count, format=fmt)

        if _debug_gl_shaders:
            for attribute in attributes.values():
                print(f" Found attribute: {attribute}")

        return attributes

    def _introspect_uniforms(self):
        program = self._id
        uniforms = {}
        for index in range(self._get_number(GL_ACTIVE_UNIFORMS)):
            u_name, u_type, u_size = self._query_uniform(index)
            loc = glGetUniformLocation(program, create_string_buffer(u_name.encode('utf-8')))
            if loc == -1:      # Skip uniforms that may be inside a Uniform Block
                continue
            uniforms[u_name] = _Uniform(program, u_name, u_type, loc, self._dsa)

        if _debug_gl_shaders:
            for uniform in uniforms.values():
                print(f" Found uniform: {uniform}")

        return uniforms

    def _introspect_uniform_blocks(self):
        program = self._id
        uniform_blocks = {}
        for index in range(self._get_number(GL_ACTIVE_UNIFORM_BLOCKS)):
            name = self._get_uniform_block_name(index)

            num_active = GLint()
            block_data_size = GLint()

            glGetActiveUniformBlockiv(program, index, GL_UNIFORM_BLOCK_ACTIVE_UNIFORMS, num_active)
            glGetActiveUniformBlockiv(program, index, GL_UNIFORM_BLOCK_DATA_SIZE, block_data_size)

            indices = (GLuint * num_active.value)()
            indices_ptr = cast(addressof(indices), POINTER(GLint))
            glGetActiveUniformBlockiv(program, index, GL_UNIFORM_BLOCK_ACTIVE_UNIFORM_INDICES, indices_ptr)

            uniforms = {}

            for block_uniform_index in indices:
                uniform_name, u_type, u_size = self._query_uniform(block_uniform_index)

                # Separate uniform name from block name (Only if instance name is provided on the Uniform Block)
                try:
                    _, uniform_name = uniform_name.split(".")
                except ValueError:
                    pass

                gl_type, _, _, length, _ = _uniform_setters[u_type]
                uniforms[block_uniform_index] = (uniform_name, gl_type, length)

            uniform_blocks[name] = UniformBlock(self, name, index, block_data_size.value, uniforms)
            # This might cause an error if index > GL_MAX_UNIFORM_BUFFER_BINDINGS, but surely no
            # one would be crazy enough to use more than 36 uniform blocks, right?
            glUniformBlockBinding(self.id, index, index)

            if _debug_gl_shaders:
                for block in uniform_blocks.values():
                    print(f" Found uniform block: {block}")

        return uniform_blocks

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

    def vertex_list(self, count, mode, batch=None, group=None, **data):
        """Create a VertexList.

        :Parameters:
            `count` : int
                The number of vertices in the list.
            `mode` : int
                OpenGL drawing mode enumeration; for example, one of
                ``GL_POINTS``, ``GL_LINES``, ``GL_TRIANGLES``, etc.
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
        domain = batch.get_domain(False, mode, group, self._id, attributes)

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
        domain = batch.get_domain(True, mode, group, self._id, attributes)

        # Create vertex list and initialize
        vlist = domain.create(count, len(indices))
        start = vlist.start
        vlist.indices = [i + start for i in indices]

        for name, array in initial_arrays:
            vlist.set_attribute_data(name, array)

        return vlist

    def __repr__(self):
        return "{0}(id={1})".format(self.__class__.__name__, self.id)


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
                By default this is 0.

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
            __repr__ = lambda self: str(dict(self._fields_))

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
