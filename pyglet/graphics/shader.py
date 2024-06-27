from __future__ import annotations

import warnings
from ctypes import (
    POINTER, Structure, addressof, byref, c_buffer, c_byte, c_char, c_char_p, c_double, c_float, c_int,
    c_short, c_ubyte, c_uint, c_ushort, cast, create_string_buffer, pointer, sizeof, string_at, Array,
)
from typing import Sequence, Callable, Any, TYPE_CHECKING, Literal
from weakref import proxy

from _ctypes import _SimpleCData, _Pointer

import pyglet
from pyglet.gl import GLException, gl_info, Context
from pyglet.gl.gl import (
    GL_ACTIVE_ATTRIBUTES, GL_ACTIVE_UNIFORMS, GL_ACTIVE_UNIFORM_BLOCKS, GL_ALL_BARRIER_BITS,
    GL_ARRAY_BUFFER, GL_BOOL, GL_BOOL_VEC2, GL_BOOL_VEC3, GL_BOOL_VEC4, GL_BYTE, GL_COMPILE_STATUS, GL_COMPUTE_SHADER,
    GL_DOUBLE, GL_DOUBLE_VEC2, GL_DOUBLE_VEC3, GL_DOUBLE_VEC4, GL_FALSE, GL_FLOAT, GL_FLOAT_MAT2, GL_FLOAT_MAT2x3,
    GL_FLOAT_MAT2x4, GL_FLOAT_MAT3, GL_FLOAT_MAT3x2, GL_FLOAT_MAT3x4, GL_FLOAT_MAT4, GL_FLOAT_MAT4x2, GL_FLOAT_MAT4x3,
    GL_FLOAT_VEC2, GL_FLOAT_VEC3, GL_FLOAT_VEC4, GL_FRAGMENT_SHADER, GL_GEOMETRY_SHADER, GL_IMAGE_1D, GL_IMAGE_1D_ARRAY,
    GL_IMAGE_2D, GL_IMAGE_2D_ARRAY, GL_IMAGE_2D_MULTISAMPLE, GL_IMAGE_2D_MULTISAMPLE_ARRAY, GL_IMAGE_2D_RECT,
    GL_IMAGE_3D, GL_IMAGE_BUFFER, GL_IMAGE_CUBE, GL_IMAGE_CUBE_MAP_ARRAY, GL_INFO_LOG_LENGTH, GL_INT, GL_INT_SAMPLER_1D,
    GL_INT_SAMPLER_1D_ARRAY, GL_INT_SAMPLER_2D, GL_INT_SAMPLER_2D_ARRAY, GL_INT_SAMPLER_2D_MULTISAMPLE,
    GL_INT_SAMPLER_3D, GL_INT_SAMPLER_CUBE, GL_INT_SAMPLER_CUBE_MAP_ARRAY, GL_INT_VEC2, GL_INT_VEC3, GL_INT_VEC4,
    GL_LINK_STATUS, GL_MAP_READ_BIT, GL_MAX_COMPUTE_SHARED_MEMORY_SIZE, GL_MAX_COMPUTE_WORK_GROUP_COUNT,
    GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS, GL_MAX_COMPUTE_WORK_GROUP_SIZE, GL_SAMPLER_1D, GL_SAMPLER_1D_ARRAY,
    GL_SAMPLER_2D, GL_SAMPLER_2D_ARRAY, GL_SAMPLER_2D_MULTISAMPLE, GL_SAMPLER_3D, GL_SAMPLER_CUBE,
    GL_SAMPLER_CUBE_MAP_ARRAY, GL_SHADER_SOURCE_LENGTH, GL_SHORT, GL_TESS_CONTROL_SHADER, GL_TESS_EVALUATION_SHADER,
    GL_TRUE, GL_UNIFORM_BLOCK_ACTIVE_UNIFORMS, GL_UNIFORM_BLOCK_ACTIVE_UNIFORM_INDICES, GL_UNIFORM_BLOCK_DATA_SIZE,
    GL_UNIFORM_BUFFER, GL_UNIFORM_OFFSET, GL_UNSIGNED_BYTE, GL_UNSIGNED_INT, GL_UNSIGNED_INT_SAMPLER_1D,
    GL_UNSIGNED_INT_SAMPLER_1D_ARRAY, GL_UNSIGNED_INT_SAMPLER_2D, GL_UNSIGNED_INT_SAMPLER_2D_ARRAY,
    GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE, GL_UNSIGNED_INT_SAMPLER_3D, GL_UNSIGNED_INT_SAMPLER_CUBE,
    GL_UNSIGNED_INT_SAMPLER_CUBE_MAP_ARRAY, GL_UNSIGNED_INT_VEC2, GL_UNSIGNED_INT_VEC3, GL_UNSIGNED_INT_VEC4,
    GL_UNSIGNED_SHORT, GL_VERTEX_SHADER, GLboolean, GLenum, GLfloat, GLint, GLuint, glAttachShader, glBindBuffer,
    glBindBufferBase, glCompileShader, glCreateProgram, glCreateShader, glDeleteProgram, glDeleteShader, glDetachShader,
    glDispatchCompute, glEnableVertexAttribArray, glGetActiveAttrib, glGetActiveUniform, glGetActiveUniformBlockName,
    glGetActiveUniformBlockiv, glGetActiveUniformsiv, glGetAttribLocation, glGetIntegeri_v, glGetIntegerv,
    glGetProgramInfoLog, glGetProgramiv, glGetShaderInfoLog, glGetShaderSource, glGetShaderiv, glGetUniformLocation,
    glGetUniformfv, glGetUniformiv, glLinkProgram, glMapBufferRange, glMemoryBarrier, glProgramUniform1fv,
    glProgramUniform1iv, glProgramUniform2fv, glProgramUniform2iv, glProgramUniform3fv, glProgramUniform3iv,
    glProgramUniform4fv, glProgramUniform4iv, glProgramUniformMatrix2fv, glProgramUniformMatrix3fv,
    glProgramUniformMatrix4fv, glShaderSource, glUniform1fv, glUniform1iv, glUniform2fv, glUniform2iv, glUniform3fv,
    glUniform3iv, glUniform4fv, glUniform4iv, glUniformBlockBinding, glUniformMatrix2fv, glUniformMatrix3fv,
    glUniformMatrix4fv, glUnmapBuffer, glUseProgram, glVertexAttribDivisor, glVertexAttribPointer,
)
from pyglet.graphics.vertexbuffer import AttributeBufferObject, BufferObject

if TYPE_CHECKING:
    from pyglet.graphics.vertexdomain import IndexedVertexList, VertexList
    from pyglet.graphics import Group, Batch
    from _weakref import CallableProxyType

_debug_gl_shaders = pyglet.options['debug_gl_shaders']


class ShaderException(BaseException):  # noqa: D101
    pass


CTypesDataType = type[_SimpleCData]
CTypesPointer = _Pointer
ShaderType = Literal['vertex', 'fragment', 'geometry', 'compute', 'tesscontrol', 'tessevaluation']
GLDataType = type[GLint] | type[GLfloat] | type[GLboolean] | int
GLFunc = Callable

_c_types: dict[int, CTypesDataType] = {
    GL_BYTE: c_byte,
    GL_UNSIGNED_BYTE: c_ubyte,
    GL_SHORT: c_short,
    GL_UNSIGNED_SHORT: c_ushort,
    GL_INT: c_int,
    GL_UNSIGNED_INT: c_uint,
    GL_FLOAT: c_float,
    GL_DOUBLE: c_double,
}

_shader_types: dict[ShaderType, int] = {
    'compute': GL_COMPUTE_SHADER,
    'fragment': GL_FRAGMENT_SHADER,
    'geometry': GL_GEOMETRY_SHADER,
    'tesscontrol': GL_TESS_CONTROL_SHADER,
    'tessevaluation': GL_TESS_EVALUATION_SHADER,
    'vertex': GL_VERTEX_SHADER,
}

_uniform_getters: dict[GLDataType, Callable] = {
    GLint: glGetUniformiv,
    GLfloat: glGetUniformfv,
    GLboolean: glGetUniformiv,
}

_uniform_setters: dict[int, tuple[GLDataType, GLFunc, GLFunc, int]] = {
    # uniform:    gl_type, legacy_setter, setter, length
    GL_BOOL: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_BOOL_VEC2: (GLint, glUniform1iv, glProgramUniform1iv, 2),
    GL_BOOL_VEC3: (GLint, glUniform1iv, glProgramUniform1iv, 3),
    GL_BOOL_VEC4: (GLint, glUniform1iv, glProgramUniform1iv, 4),

    GL_INT: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_INT_VEC2: (GLint, glUniform2iv, glProgramUniform2iv, 2),
    GL_INT_VEC3: (GLint, glUniform3iv, glProgramUniform3iv, 3),
    GL_INT_VEC4: (GLint, glUniform4iv, glProgramUniform4iv, 4),

    GL_FLOAT: (GLfloat, glUniform1fv, glProgramUniform1fv, 1),
    GL_FLOAT_VEC2: (GLfloat, glUniform2fv, glProgramUniform2fv, 2),
    GL_FLOAT_VEC3: (GLfloat, glUniform3fv, glProgramUniform3fv, 3),
    GL_FLOAT_VEC4: (GLfloat, glUniform4fv, glProgramUniform4fv, 4),

    # 1D Samplers
    GL_SAMPLER_1D: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_SAMPLER_1D_ARRAY: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_INT_SAMPLER_1D: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_INT_SAMPLER_1D_ARRAY: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_UNSIGNED_INT_SAMPLER_1D: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_UNSIGNED_INT_SAMPLER_1D_ARRAY: (GLint, glUniform1iv, glProgramUniform1iv, 1),

    # 2D Samplers
    GL_SAMPLER_2D: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_SAMPLER_2D_ARRAY: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_INT_SAMPLER_2D: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_INT_SAMPLER_2D_ARRAY: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_UNSIGNED_INT_SAMPLER_2D: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_UNSIGNED_INT_SAMPLER_2D_ARRAY: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    # Multisample
    GL_SAMPLER_2D_MULTISAMPLE: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_INT_SAMPLER_2D_MULTISAMPLE: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE: (GLint, glUniform1iv, glProgramUniform1iv, 1),

    # Cube Samplers
    GL_SAMPLER_CUBE: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_INT_SAMPLER_CUBE: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_UNSIGNED_INT_SAMPLER_CUBE: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_SAMPLER_CUBE_MAP_ARRAY: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_INT_SAMPLER_CUBE_MAP_ARRAY: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_UNSIGNED_INT_SAMPLER_CUBE_MAP_ARRAY: (GLint, glUniform1iv, glProgramUniform1iv, 1),

    # 3D Samplers
    GL_SAMPLER_3D: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_INT_SAMPLER_3D: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_UNSIGNED_INT_SAMPLER_3D: (GLint, glUniform1iv, glProgramUniform1iv, 1),

    GL_FLOAT_MAT2: (GLfloat, glUniformMatrix2fv, glProgramUniformMatrix2fv, 4),
    GL_FLOAT_MAT3: (GLfloat, glUniformMatrix3fv, glProgramUniformMatrix3fv, 6),
    GL_FLOAT_MAT4: (GLfloat, glUniformMatrix4fv, glProgramUniformMatrix4fv, 16),

    # TODO: test/implement these:
    # GL_FLOAT_MAT2x3: glUniformMatrix2x3fv, glProgramUniformMatrix2x3fv,
    # GL_FLOAT_MAT2x4: glUniformMatrix2x4fv, glProgramUniformMatrix2x4fv,
    # GL_FLOAT_MAT3x2: glUniformMatrix3x2fv, glProgramUniformMatrix3x2fv,
    # GL_FLOAT_MAT3x4: glUniformMatrix3x4fv, glProgramUniformMatrix3x4fv,
    # GL_FLOAT_MAT4x2: glUniformMatrix4x2fv, glProgramUniformMatrix4x2fv,
    # GL_FLOAT_MAT4x3: glUniformMatrix4x3fv, glProgramUniformMatrix4x3fv,

    GL_IMAGE_1D: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_IMAGE_2D: (GLint, glUniform1iv, glProgramUniform1iv, 2),
    GL_IMAGE_2D_RECT: (GLint, glUniform1iv, glProgramUniform1iv, 3),
    GL_IMAGE_3D: (GLint, glUniform1iv, glProgramUniform1iv, 3),

    GL_IMAGE_1D_ARRAY: (GLint, glUniform1iv, glProgramUniform1iv, 2),
    GL_IMAGE_2D_ARRAY: (GLint, glUniform1iv, glProgramUniform1iv, 3),

    GL_IMAGE_2D_MULTISAMPLE: (GLint, glUniform1iv, glProgramUniform1iv, 2),
    GL_IMAGE_2D_MULTISAMPLE_ARRAY: (GLint, glUniform1iv, glProgramUniform1iv, 3),

    GL_IMAGE_BUFFER: (GLint, glUniform1iv, glProgramUniform1iv, 3),
    GL_IMAGE_CUBE: (GLint, glUniform1iv, glProgramUniform1iv, 1),
    GL_IMAGE_CUBE_MAP_ARRAY: (GLint, glUniform1iv, glProgramUniform1iv, 3),
}

_attribute_types: dict[int, tuple[int, str]] = {
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


# Accessor classes:

class Attribute:
    """Abstract accessor for an attribute in a mapped buffer."""
    stride: int
    element_size: int
    c_type: CTypesDataType
    instance: bool
    normalize: bool
    gl_type: int
    count: int
    location: int
    name: str

    def __init__(self, name: str, location: int, count: int, gl_type: int, normalize: bool, instance: bool) -> None:
        """Create the attribute accessor.

        Args:
            name:
                Name of the vertex attribute.
            location:
                Location (index) of the vertex attribute.
            count:
                Number of components in the attribute.
            gl_type:
                OpenGL type enumerant; for example, ``GL_FLOAT``
            normalize:
                True if OpenGL should normalize the values
            instance:
                True if OpenGL should treat this as an instanced attribute.

        """
        self.name = name
        self.location = location
        self.count = count
        self.gl_type = gl_type
        self.normalize = normalize
        self.instance = instance

        self.c_type = _c_types[gl_type]

        self.element_size = sizeof(self.c_type)
        self.stride = count * self.element_size

    def enable(self) -> None:
        """Enable the attribute."""
        glEnableVertexAttribArray(self.location)

    def set_pointer(self, ptr: int) -> None:
        """Setup this attribute to point to the currently bound buffer at the given offset.

        ``offset`` should be based on the currently bound buffer's ``ptr`` member.

        Args:
            ptr:
                Pointer offset to the currently bound buffer for this attribute.

        """
        glVertexAttribPointer(self.location, self.count, self.gl_type, self.normalize, self.stride, ptr)

    def set_divisor(self) -> None:
        glVertexAttribDivisor(self.location, 1)

    def get_region(self, buffer: AttributeBufferObject, start: int, count: int) -> int:
        """Map a buffer region using this attribute as an accessor.

        The returned region consists of a contiguous array of component
        data elements.  For example, if this attribute uses 3 floats per
        vertex, and the `count` parameter is 4, the number of floats mapped
        will be ``3 * 4 = 12``.

        Args:
            buffer:
                The buffer to map.
            start:
                Offset of the first vertex to map.
            count:
                Number of vertices to map
        """
        return buffer.get_region(start, count)

    def set_region(self, buffer: AttributeBufferObject, start: int, count: int, data: Sequence[float]) -> None:
        """Set the data over a region of the buffer.

        Args:
            buffer:
                The buffer to map.
            start:
                Offset of the first vertex to map.
            count:
                Number of vertices to map
            data:
                A sequence of data components.

        """
        buffer.set_region(start, count, data)

    def __repr__(self) -> str:
        return f"Attribute(name='{self.name}', location={self.location}, count={self.count})"


class _UniformArray:
    """Wrapper of the GLSL array data inside a Uniform.

    Allows access to get and set items for a more Pythonic implementation.
    Types with a length longer than 1 will be returned as tuples as an inner list would not support individual value
    reassignment. Array data must either be set in full, or by indexing.
    """
    _uniform: _Uniform
    _gl_type: GLDataType
    _gl_getter: GLFunc
    _gl_setter: GLFunc
    _is_matrix: bool
    _dsa: bool
    _c_array: Array[GLDataType]
    _ptr: CTypesPointer[GLDataType]
    _uniform: _Uniform

    __slots__ = ('_uniform', '_gl_type', '_gl_getter', '_gl_setter', '_is_matrix', '_dsa', '_c_array', '_ptr')

    def __init__(self, uniform: _Uniform, gl_getter: GLFunc, gl_setter: GLFunc, gl_type: GLDataType, is_matrix: bool,
                 dsa: bool) -> None:
        self._uniform = uniform
        self._gl_type = gl_type
        self._gl_getter = gl_getter
        self._gl_setter = gl_setter
        self._is_matrix = is_matrix
        self._dsa = dsa

        if self._uniform.length > 1:
            self._c_array = (gl_type * self._uniform.length * self._uniform.size)()
        else:
            self._c_array = (gl_type * self._uniform.size)()

        self._ptr = cast(self._c_array, POINTER(gl_type))

    def __len__(self) -> int:
        return self._uniform.size

    def __delitem__(self, key: int) -> None:
        msg = "Deleting items is not support for UniformArrays."
        raise ShaderException(msg)

    def __getitem__(self, key: slice | int) -> list[tuple] | tuple:
        # Return as a tuple. Returning as a list may imply setting inner list elements will update values.
        if isinstance(key, slice):
            sliced_data = self._c_array[key]
            if self._uniform.length > 1:
                return [tuple(data) for data in sliced_data]

            return tuple([data for data in sliced_data])  # noqa: C416

        value = self._c_array[key]
        return tuple(value) if self._uniform.length > 1 else value

    def __setitem__(self, key: slice | int, value: Sequence) -> None:
        if isinstance(key, slice):
            self._c_array[key] = value
            self._update_uniform(self._ptr)
            return

        self._c_array[key] = value

        if self._uniform.length > 1:
            assert len(
                value) == self._uniform.length, (f"Setting this key requires {self._uniform.length} values, "
                                                 f"received {len(value)}.")
            data = (self._gl_type * self._uniform.length)(*value)
        else:
            data = self._gl_type(value)

        self._update_uniform(data, offset=key)

    def get(self) -> _UniformArray:
        self._gl_getter(self._uniform.program, self._uniform.location, self._ptr)
        return self

    def set(self, values: Sequence) -> None:
        assert len(self._c_array) == len(
            values), f"Size of data ({len(values)}) does not match size of the uniform: {len(self._c_array)}."

        self._c_array[:] = values
        self._update_uniform(self._ptr)

    def _update_uniform(self, data: Sequence, offset: int = 0) -> None:
        if offset != 0:
            size = 1
        else:
            size = self._uniform.size

        if self._dsa:
            self._gl_setter(self._uniform.program, self._uniform.location + offset, size, data)
        else:
            glUseProgram(self._uniform.program)
            self._gl_setter(self._uniform.location + offset, size, data)

    def __repr__(self) -> str:
        data = [tuple(data) if self._uniform.length > 1 else data for data in self._c_array]
        return f"UniformArray(uniform={self._uniform}, data={data})"


class _Uniform:
    type: int
    size: int
    location: int
    program: int
    length: int
    get: Callable[[], Array[GLDataType] | GLDataType]
    set: Callable[[float], None] | Callable[[Sequence], None]

    __slots__ = 'type', 'size', 'location', 'length', 'count', 'get', 'set', 'program'

    def __init__(self, program: int, uniform_type: int, size: int, location: int, dsa: bool) -> None:
        self.type = uniform_type
        self.size = size
        self.location = location
        self.program = program

        gl_type, gl_setter_legacy, gl_setter_dsa, length = _uniform_setters[uniform_type]
        gl_setter = gl_setter_dsa if dsa else gl_setter_legacy
        gl_getter = _uniform_getters[gl_type]

        # Argument length of data
        self.length = length

        is_matrix = uniform_type in (GL_FLOAT_MAT2, GL_FLOAT_MAT2x3, GL_FLOAT_MAT2x4,
                                     GL_FLOAT_MAT3, GL_FLOAT_MAT3x2, GL_FLOAT_MAT3x4,
                                     GL_FLOAT_MAT4, GL_FLOAT_MAT4x2, GL_FLOAT_MAT4x3)

        # If it's an array, use the wrapper object.
        if size > 1:
            array = _UniformArray(self, gl_getter, gl_setter, gl_type, is_matrix, dsa)
            self.get = array.get
            self.set = array.set
        else:
            c_array: Array[GLDataType] = (gl_type * length)()
            ptr = cast(c_array, POINTER(gl_type))

            self.get = self._create_getter_func(program, location, gl_getter, c_array, length)
            self.set = self._create_setter_func(program, location, gl_setter, c_array, length, ptr, is_matrix, dsa)

    @staticmethod
    def _create_getter_func(program_id: int, location: int, gl_getter: GLFunc, c_array: Array[GLDataType],
                            length: int) -> Callable[[], Array[GLDataType] | GLDataType]:
        """Factory function for creating simplified Uniform getters."""
        if length == 1:
            def getter_func() -> GLDataType:
                gl_getter(program_id, location, c_array)
                return c_array[0]
        else:
            def getter_func() -> Array[GLDataType]:
                gl_getter(program_id, location, c_array)
                return c_array[:]

        return getter_func

    @staticmethod
    def _create_setter_func(program_id: int, location: int, gl_setter: GLFunc, c_array: Array[GLDataType], length: int,
                            ptr: CTypesPointer[GLDataType], is_matrix: bool, dsa: bool) -> Callable[[float], None]:
        """Factory function for creating simplified Uniform setters."""
        if dsa:  # Bindless updates:

            if is_matrix:
                def setter_func(value: float) -> None:
                    c_array[:] = value
                    gl_setter(program_id, location, 1, GL_FALSE, ptr)
            elif length == 1:
                def setter_func(value: float) -> None:
                    c_array[0] = value
                    gl_setter(program_id, location, 1, ptr)
            elif length > 1:
                def setter_func(values: float) -> None:
                    c_array[:] = values
                    gl_setter(program_id, location, 1, ptr)

            else:
                msg = "Uniform type not yet supported."
                raise ShaderException(msg)

            return setter_func

        if is_matrix:
            def setter_func(value: float) -> None:
                glUseProgram(program_id)
                c_array[:] = value
                gl_setter(location, 1, GL_FALSE, ptr)
        elif length == 1:
            def setter_func(value: float) -> None:
                glUseProgram(program_id)
                c_array[0] = value
                gl_setter(location, 1, ptr)
        elif length > 1:
            def setter_func(values: float) -> None:
                glUseProgram(program_id)
                c_array[:] = values
                gl_setter(location, 1, ptr)
        else:
            msg = "Uniform type not yet supported."
            raise ShaderException(msg)

        return setter_func

    def __repr__(self) -> str:
        return f"Uniform(type={self.type}, size={self.size}, location={self.location})"


class UniformBlock:
    program: CallableProxyType[Callable[..., Any] | Any] | Any
    name: str
    index: int
    size: int
    uniforms: dict[int, tuple[str, GLDataType, int]]
    view_cls: type[Structure] | None
    __slots__ = 'program', 'name', 'index', 'size', 'uniforms', 'view_cls'

    def __init__(self, program: ShaderProgram, name: str, index: int, size: int,
                 uniforms: dict[int, tuple[str, GLDataType, int]]) -> None:
        """Initialize a uniform block for a ShaderProgram."""
        self.program = proxy(program)
        self.name = name
        self.index = index
        self.size = size
        self.uniforms = uniforms
        self.view_cls = None

    def create_ubo(self, index: int = 0) -> UniformBufferObject:
        """Create a new UniformBufferObject from this uniform block.

        Args:
            index:
                The uniform buffer index the returned UBO will bind itself to.
                By default, this is 0.
        """
        if self.view_cls is None:
            self.view_cls = self._introspect_uniforms()
        return UniformBufferObject(self.view_cls, self.size, index)

    def _introspect_uniforms(self) -> type[Structure]:
        """Introspect the block's structure and return a ctypes struct for manipulating the uniform block's members."""
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
            size = offsets[i + 1] - offsets[i]
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

            def __repr__(self) -> str:
                return str(dict(self._fields_))

        return View

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(location={self.index}, size={self.size})"


class UniformBufferObject:
    buffer: BufferObject
    view: Structure
    _view_ptr: CTypesPointer[Structure]
    index: int
    buffer: BufferObject
    __slots__ = 'buffer', 'view', '_view_ptr', 'index'

    def __init__(self, view_class: type[Structure], buffer_size: int, index: int) -> None:
        """Initialize the Uniform Buffer Object with the specified Structure."""
        self.buffer = BufferObject(buffer_size)
        self.view = view_class()
        self._view_ptr = pointer(self.view)
        self.index = index

    @property
    def id(self) -> int:
        return self.buffer.id

    def bind(self, index: int | None = None) -> None:
        glBindBufferBase(GL_UNIFORM_BUFFER, self.index if index is None else index, self.buffer.id)

    def read(self) -> bytes:
        """Read the byte contents of the buffer."""
        glBindBuffer(GL_ARRAY_BUFFER, self.buffer.id)
        ptr = glMapBufferRange(GL_ARRAY_BUFFER, 0, self.buffer.size, GL_MAP_READ_BIT)
        data = string_at(ptr, size=self.buffer.size)
        glUnmapBuffer(GL_ARRAY_BUFFER)
        return data

    def __enter__(self) -> Structure:
        # Return the view to the user in a `with` context:
        return self.view

    def __exit__(self, _exc_type, _exc_val, _exc_tb) -> None:  # noqa: ANN001
        self.bind()
        self.buffer.set_data(self._view_ptr)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.buffer.id})"


# Utility functions:

def _get_number(program_id: int, variable_type: int) -> int:
    """Get the number of active variables of the passed GL type."""
    number = GLint(0)
    glGetProgramiv(program_id, variable_type, byref(number))
    return number.value


def _query_attribute(program_id: int, index: int) -> tuple[str, int, int]:
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


def _introspect_attributes(program_id: int) -> dict[str, Any]:
    """Introspect a Program's Attributes, and return a dict of accessors."""
    attributes = {}

    for index in range(_get_number(program_id, GL_ACTIVE_ATTRIBUTES)):
        a_name, a_type, a_size = _query_attribute(program_id, index)
        loc = glGetAttribLocation(program_id, create_string_buffer(a_name.encode('utf-8')))
        count, fmt = _attribute_types[a_type]
        attributes[a_name] = {
            'type': a_type, 'size': a_size, 'location': loc, 'count': count, 'format': fmt,
            'instance': False,
        }

    if _debug_gl_shaders:
        for attribute in attributes.values():
            print(f" Found attribute: {attribute}")

    return attributes


def _link_program(*shaders: Shader) -> int:
    """Link one or more Shaders into a ShaderProgram.

    Returns:
        The ID assigned to the linked ShaderProgram.
    """
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
        msg = f"Error linking shader program:\n{log.value.decode()}"
        raise ShaderException(msg)

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

    return f"Program '{program_id}' linked successfully."


def _query_uniform(program_id: int, index: int) -> tuple[str, int, int]:
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


def _introspect_uniforms(program_id: int, have_dsa: bool) -> dict[str, _Uniform]:
    """Introspect a Program's uniforms, and return a dict of accessors."""
    uniforms = {}

    for index in range(_get_number(program_id, GL_ACTIVE_UNIFORMS)):
        u_name, u_type, u_size = _query_uniform(program_id, index)

        # Multidimensional arrays cannot be fully inspected via OpenGL calls.
        array_count = u_name.count("[0]")
        if array_count > 1:
            msg = "Multidimensional arrays are not currently supported."
            raise ShaderException(msg)

        loc = glGetUniformLocation(program_id, create_string_buffer(u_name.encode('utf-8')))
        if loc == -1:  # Skip uniforms that may be inside a Uniform Block
            continue

        # Strip [0] from array name for a more user-friendly name.
        if array_count == 1:
            u_name = u_name.strip('[0]')

        assert u_name not in uniforms, f"{u_name} exists twice in the shader. Possible name clash with an array."
        uniforms[u_name] = _Uniform(program_id, u_type, u_size, loc, have_dsa)

    if _debug_gl_shaders:
        for uniform in uniforms.values():
            print(f" Found uniform: {uniform}")

    return uniforms


def _get_uniform_block_name(program_id: int, index: int) -> str:
    """Query the name of a Uniform Block, by index."""
    buf_size = 128
    size = c_int(0)
    name_buf = create_string_buffer(buf_size)
    try:
        glGetActiveUniformBlockName(program_id, index, buf_size, size, name_buf)
        return name_buf.value.decode()
    except GLException:
        msg = f"Unable to query UniformBlock name at index: {index}"
        raise ShaderException(msg)  # noqa: B904


def _introspect_uniform_blocks(program: ShaderProgram | ComputeShaderProgram) -> dict[str, UniformBlock]:
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

            gl_type, _, _, length = _uniform_setters[u_type]
            uniforms[block_uniform_index] = (uniform_name, gl_type, length)

        uniform_blocks[name] = UniformBlock(program, name, index, block_data_size.value, uniforms)
        # This might cause an error if index > GL_MAX_UNIFORM_BUFFER_BINDINGS, but surely no
        # one would be crazy enough to use more than 36 uniform blocks, right?
        glUniformBlockBinding(program_id, index, index)

        if _debug_gl_shaders:
            for block in uniform_blocks.values():
                print(f" Found uniform block: {block}")

    return uniform_blocks


# Shader & program classes:

class ShaderSource:
    """GLSL source container for making source parsing simpler.

    We support locating out attributes and applying #defines values.

    .. note:: We do assume the source is neat enough to be parsed this way and doesn't contain several statements in
              one line.
    """
    _type: GLenum
    _lines: list[str]

    def __init__(self, source: str, source_type: GLenum) -> None:
        """Create a shader source wrapper."""
        self._lines = source.strip().splitlines()
        self._type = source_type

        if not self._lines:
            msg = "Shader source is empty"
            raise ShaderException(msg)

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

        source = "\n".join(f"{str(i + 1).zfill(3)}: {line} " for i, line in enumerate(self._lines))

        msg = (
            "Cannot find #version flag in shader source. "
            "A #version statement is required on the first line.\n"
            "------------------------------------\n"
            f"{source}"
        )
        raise ShaderException(msg)


class Shader:
    """OpenGL shader.

    Shader objects are compiled on instantiation.
    You can reuse a Shader object in multiple ShaderPrograms.
    """
    _context: Context | None
    _id: int | None
    type: ShaderType

    def __init__(self, source_string: str, shader_type: ShaderType) -> None:
        """Initialize a shader type.

        Args:
            source_string:
                A string containing the source of your shader program.

            shader_type:
                A string containing the type of shader program:

                * ``'vertex'``
                * ``'fragment'``
                * ``'geometry'``
                * ``'compute'``
                * ``'tesscontrol'``
                * ``'tessevaluation'``
        """
        self._context = pyglet.gl.current_context
        self._id = None
        self.type = shader_type

        try:
            shader_type = _shader_types[shader_type]
        except KeyError as err:
            msg = (
                f"shader_type '{shader_type}' is invalid."
                f"Valid types are: {list(_shader_types)}"
            )
            raise ShaderException(msg) from err

        source_string = ShaderSource(source_string, shader_type).validate()
        shader_source_utf8 = source_string.encode("utf8")
        source_buffer_pointer = cast(c_char_p(shader_source_utf8), POINTER(c_char))
        source_length = c_int(len(shader_source_utf8))

        shader_id = glCreateShader(shader_type)
        self._id = shader_id
        glShaderSource(shader_id, 1, byref(source_buffer_pointer), source_length)
        glCompileShader(shader_id)

        status = c_int(0)
        glGetShaderiv(shader_id, GL_COMPILE_STATUS, byref(status))

        if status.value != GL_TRUE:
            source = self._get_shader_source(shader_id)
            source_lines = "{0}".format("\n".join(f"{str(i + 1).zfill(3)}: {line} "
                                                  for i, line in enumerate(source.split("\n"))))

            msg = (
                f"Shader compilation failed.\n"
                f"{self._get_shader_log(shader_id)}"
                "------------------------------------------------------------\n"
                f"{source_lines}\n"
                "------------------------------------------------------------"
            )
            raise ShaderException(msg)

        if _debug_gl_shaders:
            print(self._get_shader_log(shader_id))

    @property
    def id(self) -> int:
        return self._id

    def _get_shader_log(self, shader_id: int) -> str:
        log_length = c_int(0)
        glGetShaderiv(shader_id, GL_INFO_LOG_LENGTH, byref(log_length))
        result_str = create_string_buffer(log_length.value)
        glGetShaderInfoLog(shader_id, log_length, None, result_str)
        if result_str.value:
            return (f"OpenGL returned the following message when compiling the "
                    f"'{self.type}' shader: \n{result_str.value.decode('utf8')}")

        return f"{self.type.capitalize()} Shader '{shader_id}' compiled successfully."

    @staticmethod
    def _get_shader_source(shader_id: int) -> str:
        """Get the shader source from the shader object."""
        source_length = c_int(0)
        glGetShaderiv(shader_id, GL_SHADER_SOURCE_LENGTH, source_length)
        source_str = create_string_buffer(source_length.value)
        glGetShaderSource(shader_id, source_length, None, source_str)
        return source_str.value.decode('utf8')

    def delete(self) -> None:
        """Deletes the shader.

        This cannot be undone.
        """
        glDeleteShader(self._id)
        self._id = None

    def __del__(self) -> None:
        if self._id is not None:
            try:
                self._context.delete_shader(self._id)
                if _debug_gl_shaders:
                    print(f"Destroyed {self.type} Shader '{self._id}'")
                self._id = None
            except (AttributeError, ImportError):
                pass  # Interpreter is shutting down

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, type={self.type})"


class ShaderProgram:
    """OpenGL shader program."""
    _id: int | None
    _context: Context | None
    _attributes: dict[str, Any]
    _uniforms: dict[str, _Uniform]
    _uniform_blocks: dict[str, UniformBlock]

    __slots__ = '_id', '_context', '_attributes', '_uniforms', '_uniform_blocks', '__weakref__'

    def __init__(self, *shaders: Shader) -> None:
        """Initialize the ShaderProgram using at least two Shader instances."""
        self._id = None

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
    def id(self) -> int:
        return self._id

    @property
    def attributes(self) -> dict[str, Any]:
        """Attribute metadata dictionary.

        This property returns a dictionary containing metadata of all
        Attributes that were introspected in this ShaderProgram. Modifying
        this dictionary has no effect.
        """
        return self._attributes.copy()

    @property
    def uniforms(self) -> dict[str, Any]:
        """Uniform metadata dictionary.

        This property returns a dictionary containing metadata of all
        Uniforms that were introspected in this ShaderProgram. Modifying
        this dictionary has no effect. To set or get a uniform, the uniform
        name is used as a key on the ShaderProgram instance. For example::

            my_shader_program[uniform_name] = 123
            value = my_shader_program[uniform_name]

        """
        return {n: {'location': u.location, 'length': u.length, 'size': u.size} for n, u in self._uniforms.items()}

    @property
    def uniform_blocks(self) -> dict[str, UniformBlock]:
        """A dictionary of introspected UniformBlocks.

        This property returns a dictionary of
        :py:class:`~pyglet.graphics.shader.UniformBlock` instances.
        They can be accessed by name. For example::

            block = my_shader_program.uniform_blocks['WindowBlock']
            ubo = block.create_ubo()

        """
        return self._uniform_blocks

    def use(self) -> None:
        glUseProgram(self._id)

    @staticmethod
    def stop() -> None:
        glUseProgram(0)

    __enter__ = use
    bind = use
    unbind = stop

    def __exit__(self, *_) -> None:  # noqa: ANN002
        glUseProgram(0)

    def delete(self) -> None:
        glDeleteProgram(self._id)
        self._id = None

    def __del__(self) -> None:
        if self._id is not None:
            try:
                self._context.delete_shader_program(self._id)
                self._id = None
            except (AttributeError, ImportError):
                pass  # Interpreter is shutting down

    def __setitem__(self, key: str, value: Any) -> None:
        try:
            uniform = self._uniforms[key]
        except KeyError as err:
            msg = (f"A Uniform with the name `{key}` was not found.\n"
                   f"The spelling may be incorrect or, if not in use, it "
                   f"may have been optimized out by the OpenGL driver.")
            if _debug_gl_shaders:
                warnings.warn(msg)
                return
            raise ShaderException(msg) from err
        try:
            uniform.set(value)
        except GLException as err:
            raise ShaderException from err

    def __getitem__(self, item: str) -> Any:
        try:
            uniform = self._uniforms[item]
        except KeyError as err:
            msg = (f"A Uniform with the name `{item}` was not found.\n"
                   f"The spelling may be incorrect or, if not in use, it "
                   f"may have been optimized out by the OpenGL driver.")
            if _debug_gl_shaders:
                warnings.warn(msg)
                return None

            raise ShaderException from err
        try:
            return uniform.get()
        except GLException as err:
            raise ShaderException from err

    def _vertex_list_create(self, count: int, mode: int, indices: Sequence[int] | None = None,
                            instances: Sequence[str] | None = None, batch: Batch = None, group: Group = None,
                            **data: Any) -> VertexList | IndexedVertexList:
        attributes = self._attributes.copy()
        initial_arrays = []

        instanced = instances is not None
        indexed = indices is not None

        for name, fmt in data.items():
            try:
                if isinstance(fmt, tuple):
                    fmt, array = fmt  # noqa: PLW2901
                    initial_arrays.append((name, array))
                attributes[name] = {
                    **attributes[name], 'format': fmt,
                    'instance': name in instances if instances else False,
                }
            except KeyError:  # noqa: PERF203
                msg = (
                    f"An attribute with the name `{name}` was not found. Please "
                    f"check the spelling.\nIf the attribute is not in use in the "
                    f"program, it may have been optimized out by the OpenGL driver.\n"
                    f"Valid names: \n{list(attributes)}"
                )
                raise ShaderException(msg)  # noqa: B904

        batch = batch or pyglet.graphics.get_default_batch()
        domain = batch.get_domain(indexed, instanced, mode, group, self, attributes)

        # Create vertex list and initialize
        if indexed:
            vlist = domain.create(count, len(indices))
            start = vlist.start
            vlist.indices = [i + start for i in indices]
        else:
            vlist = domain.create(count)

        for name, array in initial_arrays:
            vlist.set_attribute_data(name, array)

        if instanced:
            vlist.instanced = True

        return vlist

    def vertex_list(self, count: int, mode: int, batch: Batch = None, group: Group = None,
                    **data: Any) -> VertexList:
        """Create a VertexList.

        Args:
            count:
                The number of vertices in the list.
            mode:
                OpenGL drawing mode enumeration; for example, one of
                ``GL_POINTS``, ``GL_LINES``, ``GL_TRIANGLES``, etc.
                This determines how the list is drawn in the given batch.
            batch:
                Batch to add the VertexList to, or ``None`` if a Batch will not be used.
                Using a Batch is strongly recommended.
            group:
                Group to add the VertexList to, or ``None`` if no group is required.
            data:
                Attribute formats and initial data for the vertex list.

        """
        return self._vertex_list_create(count, mode, None, None, batch=batch, group=group, **data)

    def vertex_list_instanced(self, count: int, mode: int, instance_attributes: Sequence[str], batch: Batch = None,
                              group: Group = None, **data: Any) -> VertexList:
        assert len(instance_attributes) > 0, "You must provide at least one attribute name to be instanced."
        return self._vertex_list_create(count, mode, None, instance_attributes, batch=batch, group=group, **data)

    def vertex_list_indexed(self, count: int, mode: int, indices: Sequence[int], batch: Batch = None,
                            group: Group = None, **data: Any) -> IndexedVertexList:
        """Create a IndexedVertexList.

        Args:
            count:
                The number of vertices in the list.
            mode:
                OpenGL drawing mode enumeration; for example, one of
                ``GL_POINTS``, ``GL_LINES``, ``GL_TRIANGLES``, etc.
                This determines how the list is drawn in the given batch.
            indices:
                Sequence of integers giving indices into the vertex list.
            batch:
                Batch to add the VertexList to, or ``None`` if a Batch will not be used.
                Using a Batch is strongly recommended.
            group:
                Group to add the VertexList to, or ``None`` if no group is required.
            data:
                Attribute formats and initial data for the vertex list.
        """
        return self._vertex_list_create(count, mode, indices, None, batch=batch, group=group, **data)

    def vertex_list_instanced_indexed(self, count: int, mode: int, indices: Sequence[int],
                                      instance_attributes: Sequence[str], batch: Batch = None, group: Group = None,
                                      **data: Any) -> IndexedVertexList:
        assert len(instance_attributes) > 0, "You must provide at least one attribute name to be instanced."
        return self._vertex_list_create(count, mode, indices, instance_attributes, batch=batch, group=group, **data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"


class ComputeShaderProgram:
    """OpenGL Compute Shader Program."""
    _context: Context | None
    _id: int | None
    _shader: Shader
    _uniforms: dict[str, Any]
    _uniform_blocks: dict[str, UniformBlock]
    max_work_group_size: tuple[int, int, int]
    max_work_group_count: tuple[int, int, int]
    max_shared_memory_size: int
    max_work_group_invocations: int

    def __init__(self, source: str) -> None:
        """Create an OpenGL ComputeShaderProgram from source."""
        self._id = None

        if not (gl_info.have_version(4, 3) or gl_info.have_extension("GL_ARB_compute_shader")):
            msg = (
                "Compute Shader not supported. OpenGL Context version must be at least "
                "4.3 or higher, or 4.2 with the 'GL_ARB_compute_shader' extension."
            )
            raise ShaderException(msg)

        self._shader = Shader(source, 'compute')
        self._context = pyglet.gl.current_context
        self._id = _link_program(self._shader)

        if _debug_gl_shaders:
            print(_get_program_log(self._id))

        self._uniforms = _introspect_uniforms(self._id, True)
        self._uniform_blocks = _introspect_uniform_blocks(self)

        self.max_work_group_size = self._get_tuple(GL_MAX_COMPUTE_WORK_GROUP_SIZE)  # x, y, z
        self.max_work_group_count = self._get_tuple(GL_MAX_COMPUTE_WORK_GROUP_COUNT)  # x, y, z
        self.max_shared_memory_size = self._get_value(GL_MAX_COMPUTE_SHARED_MEMORY_SIZE)
        self.max_work_group_invocations = self._get_value(GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS)

    @staticmethod
    def _get_tuple(parameter: int) -> tuple[int, int, int]:
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
    def uniforms(self) -> dict[str, dict[str, Any]]:
        return {n: {'location': u.location, 'length': u.length, 'size': u.size} for n, u in self._uniforms.items()}

    @property
    def uniform_blocks(self) -> dict:
        return self._uniform_blocks

    def use(self) -> None:
        glUseProgram(self._id)

    @staticmethod
    def stop() -> None:
        glUseProgram(0)

    __enter__ = use
    bind = use
    unbind = stop

    def __exit__(self, *_) -> None:  # noqa: ANN002
        glUseProgram(0)

    def delete(self) -> None:
        glDeleteProgram(self._id)
        self._id = None

    def __del__(self) -> None:
        if self._id is not None:
            try:
                self._context.delete_shader_program(self._id)
                self._id = None
            except (AttributeError, ImportError):
                pass  # Interpreter is shutting down

    def __setitem__(self, key: str, value: Any) -> None:
        try:
            uniform = self._uniforms[key]
        except KeyError as err:
            msg = (f"A Uniform with the name `{key}` was not found.\n"
                   f"The spelling may be incorrect, or if not in use it "
                   f"may have been optimized out by the OpenGL driver.")
            if _debug_gl_shaders:
                warnings.warn(msg)
                return

            raise ShaderException from err
        try:
            uniform.set(value)
        except GLException as err:
            raise ShaderException from err

    def __getitem__(self, item: str) -> Any:
        try:
            uniform = self._uniforms[item]
        except KeyError as err:
            msg = (f"A Uniform with the name `{item}` was not found.\n"
                   f"The spelling may be incorrect, or if not in use it "
                   f"may have been optimized out by the OpenGL driver.")
            if _debug_gl_shaders:
                warnings.warn(msg)
                return None

            raise ShaderException(msg) from err
        try:
            return uniform.get()
        except GLException as err:
            raise ShaderException from err
