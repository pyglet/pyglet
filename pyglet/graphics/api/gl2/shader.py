from __future__ import annotations

import warnings
from ctypes import (
    POINTER,
    Array,
    Structure,
    byref,
    c_buffer,
    c_byte,
    c_char,
    c_char_p,
    c_double,
    c_float,
    c_int,
    c_short,
    c_ubyte,
    c_uint,
    c_ushort,
    cast,
    create_string_buffer,
)
from typing import TYPE_CHECKING, Any, Callable, Sequence, Type, Union

import pyglet
import pyglet.graphics.api.gl.gl_compat as gl
from pyglet.customtypes import DataTypes, CTypesPointer
from pyglet.graphics.api.gl import GLException
from pyglet.graphics.api.gl.gl_compat import (
    GL_FALSE,
    GL_INFO_LOG_LENGTH,
    GL_LINK_STATUS,
    GL_TRUE,
    glAttachShader,
    glCreateProgram,
    glDeleteProgram,
    glDeleteShader,
    glDetachShader,
    glEnableVertexAttribArray,
    glDisableVertexAttribArray,
    glGetActiveAttrib,
    glGetProgramInfoLog,
    glGetProgramiv,
    glLinkProgram,
    glUseProgram,
    glVertexAttribDivisor,
    glVertexAttribPointer,
)

from pyglet.graphics.shader import ShaderSource, ShaderType, ShaderBase, Attribute, \
    ShaderProgramBase, ShaderException


if TYPE_CHECKING:
    from pyglet.graphics import GeometryMode
    from pyglet.graphics.api.gl.base import OpenGLWindowContext
    from pyglet.graphics import Batch, Group
    from pyglet.graphics.shader import CTypesDataType
    from pyglet.graphics.vertexdomain import IndexedVertexList, VertexList

_debug_api_shaders = pyglet.options['debug_api_shaders']





GLDataType = Union[Type[gl.GLint], Type[gl.GLfloat], Type[gl.GLboolean], int]
GLFunc = Callable

_c_types: dict[int, CTypesDataType] = {
    gl.GL_BYTE: c_byte,
    gl.GL_UNSIGNED_BYTE: c_ubyte,
    gl.GL_SHORT: c_short,
    gl.GL_UNSIGNED_SHORT: c_ushort,
    gl.GL_INT: c_int,
    gl.GL_UNSIGNED_INT: c_uint,
    gl.GL_FLOAT: c_float,
    gl.GL_DOUBLE: c_double,
}

_data_type_to_gl_type: dict[DataTypes, int] = {
    'b': gl.GL_BYTE,            # signed byte
    'B': gl.GL_UNSIGNED_BYTE,   # unsigned byte
    'h': gl.GL_SHORT,           # signed short
    'H': gl.GL_UNSIGNED_SHORT,  # unsigned short
    'i': gl.GL_INT,             # signed int
    'I': gl.GL_UNSIGNED_INT,    # unsigned int
    'f': gl.GL_FLOAT,           # float
    'q': gl.GL_INT,             # signed long long (Requires GL_INT64_NV if available. Just use int.)
    'Q': gl.GL_UNSIGNED_INT,    # unsigned long long (Requires GL_UNSIGNED_INT64_NV if available. Just use uint.)
}

_shader_types: dict[ShaderType, int] = {
    'compute': gl.GL_COMPUTE_SHADER,
    'fragment': gl.GL_FRAGMENT_SHADER,
    'geometry': gl.GL_GEOMETRY_SHADER,
    'tesscontrol': gl.GL_TESS_CONTROL_SHADER,
    'tessevaluation': gl.GL_TESS_EVALUATION_SHADER,
    'vertex': gl.GL_VERTEX_SHADER,
}

_uniform_getters: dict[GLDataType, Callable] = {
    gl.GLint: gl.glGetUniformiv,
    gl.GLfloat: gl.glGetUniformfv,
    gl.GLboolean: gl.glGetUniformiv,
}

_uniform_setters: dict[int, tuple[GLDataType, GLFunc, GLFunc, int]] = {
    # uniform:    gl_type, legacy_setter, setter, length
    gl.GL_BOOL: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_BOOL_VEC2: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 2),
    gl.GL_BOOL_VEC3: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 3),
    gl.GL_BOOL_VEC4: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 4),

    gl.GL_INT: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_INT_VEC2: (gl.GLint, gl.glUniform2iv, gl.glProgramUniform2iv, 2),
    gl.GL_INT_VEC3: (gl.GLint, gl.glUniform3iv, gl.glProgramUniform3iv, 3),
    gl.GL_INT_VEC4: (gl.GLint, gl.glUniform4iv, gl.glProgramUniform4iv, 4),

    gl.GL_FLOAT: (gl.GLfloat, gl.glUniform1fv, gl.glProgramUniform1fv, 1),
    gl.GL_FLOAT_VEC2: (gl.GLfloat, gl.glUniform2fv, gl.glProgramUniform2fv, 2),
    gl.GL_FLOAT_VEC3: (gl.GLfloat, gl.glUniform3fv, gl.glProgramUniform3fv, 3),
    gl.GL_FLOAT_VEC4: (gl.GLfloat, gl.glUniform4fv, gl.glProgramUniform4fv, 4),

    # 1D Samplers
    gl.GL_SAMPLER_1D: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_SAMPLER_1D_ARRAY: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_INT_SAMPLER_1D: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_INT_SAMPLER_1D_ARRAY: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_UNSIGNED_INT_SAMPLER_1D: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_UNSIGNED_INT_SAMPLER_1D_ARRAY: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),

    # 2D Samplers
    gl.GL_SAMPLER_2D: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_SAMPLER_2D_ARRAY: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_INT_SAMPLER_2D: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_INT_SAMPLER_2D_ARRAY: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_UNSIGNED_INT_SAMPLER_2D: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_UNSIGNED_INT_SAMPLER_2D_ARRAY: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    # Multisample
    gl.GL_SAMPLER_2D_MULTISAMPLE: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_INT_SAMPLER_2D_MULTISAMPLE: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_UNSIGNED_INT_SAMPLER_2D_MULTISAMPLE: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),

    # Cube Samplers
    gl.GL_SAMPLER_CUBE: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_INT_SAMPLER_CUBE: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_UNSIGNED_INT_SAMPLER_CUBE: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_SAMPLER_CUBE_MAP_ARRAY: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_INT_SAMPLER_CUBE_MAP_ARRAY: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_UNSIGNED_INT_SAMPLER_CUBE_MAP_ARRAY: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),

    # 3D Samplers
    gl.GL_SAMPLER_3D: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_INT_SAMPLER_3D: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_UNSIGNED_INT_SAMPLER_3D: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),

    gl.GL_FLOAT_MAT2: (gl.GLfloat, gl.glUniformMatrix2fv, gl.glProgramUniformMatrix2fv, 4),
    gl.GL_FLOAT_MAT3: (gl.GLfloat, gl.glUniformMatrix3fv, gl.glProgramUniformMatrix3fv, 6),
    gl.GL_FLOAT_MAT4: (gl.GLfloat, gl.glUniformMatrix4fv, gl.glProgramUniformMatrix4fv, 16),

    # TODO: test/implement these:
    # GL_FLOAT_MAT2x3: glUniformMatrix2x3fv, glProgramUniformMatrix2x3fv,
    # GL_FLOAT_MAT2x4: glUniformMatrix2x4fv, glProgramUniformMatrix2x4fv,
    # GL_FLOAT_MAT3x2: glUniformMatrix3x2fv, glProgramUniformMatrix3x2fv,
    # GL_FLOAT_MAT3x4: glUniformMatrix3x4fv, glProgramUniformMatrix3x4fv,
    # GL_FLOAT_MAT4x2: glUniformMatrix4x2fv, glProgramUniformMatrix4x2fv,
    # GL_FLOAT_MAT4x3: glUniformMatrix4x3fv, glProgramUniformMatrix4x3fv,

    gl.GL_IMAGE_1D: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_IMAGE_2D: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 2),
    gl.GL_IMAGE_2D_RECT: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 3),
    gl.GL_IMAGE_3D: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 3),

    gl.GL_IMAGE_1D_ARRAY: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 2),
    gl.GL_IMAGE_2D_ARRAY: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 3),

    gl.GL_IMAGE_2D_MULTISAMPLE: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 2),
    gl.GL_IMAGE_2D_MULTISAMPLE_ARRAY: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 3),

    gl.GL_IMAGE_BUFFER: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 3),
    gl.GL_IMAGE_CUBE: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 1),
    gl.GL_IMAGE_CUBE_MAP_ARRAY: (gl.GLint, gl.glUniform1iv, gl.glProgramUniform1iv, 3),
}

_attribute_types: dict[int, tuple[int, DataTypes]] = {
    gl.GL_BOOL: (1, '?'),
    gl.GL_BOOL_VEC2: (2, '?'),
    gl.GL_BOOL_VEC3: (3, '?'),
    gl.GL_BOOL_VEC4: (4, '?'),

    gl.GL_INT: (1, 'i'),
    gl.GL_INT_VEC2: (2, 'i'),
    gl.GL_INT_VEC3: (3, 'i'),
    gl.GL_INT_VEC4: (4, 'i'),

    gl.GL_UNSIGNED_INT: (1, 'I'),
    gl.GL_UNSIGNED_INT_VEC2: (2, 'I'),
    gl.GL_UNSIGNED_INT_VEC3: (3, 'I'),
    gl.GL_UNSIGNED_INT_VEC4: (4, 'I'),

    gl.GL_FLOAT: (1, 'f'),
    gl.GL_FLOAT_VEC2: (2, 'f'),
    gl.GL_FLOAT_VEC3: (3, 'f'),
    gl.GL_FLOAT_VEC4: (4, 'f'),

    gl.GL_DOUBLE: (1, 'd'),
    gl.GL_DOUBLE_VEC2: (2, 'd'),
    gl.GL_DOUBLE_VEC3: (3, 'd'),
    gl.GL_DOUBLE_VEC4: (4, 'd'),
}


# Accessor classes:

class GLAttribute(Attribute):
    """Abstract accessor for an attribute in a mapped buffer."""
    gl_type: int
    """OpenGL type enumerant; for example, ``GL_FLOAT``"""

    def __init__(self, name: str, location: int, components: int, data_type: DataTypes, normalize: bool,
                 instance: bool) -> None:
        """Create the attribute accessor.

        Args:
            name:
                Name of the vertex attribute.
            location:
                Location (index) of the vertex attribute.
            components:
                Number of components in the attribute.
            normalize:
                True if OpenGL should normalize the values
            instance:
                True if OpenGL should treat this as an instanced attribute.

        """
        super().__init__(name, location, components, data_type, normalize, instance)
        self.gl_type = _data_type_to_gl_type[self.data_type]

    def enable(self) -> None:
        """Enable the attribute."""
        glEnableVertexAttribArray(self.location)

    def disable(self):
        glDisableVertexAttribArray(self.location)

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
    _idx_to_loc: dict[int, int]

    __slots__ = ('_uniform', '_gl_type', '_gl_getter', '_gl_setter', '_is_matrix', '_dsa', '_c_array', '_ptr',
                 '_idx_to_loc')

    def __init__(self, uniform: _Uniform, gl_getter: GLFunc, gl_setter: GLFunc, gl_type: GLDataType, is_matrix: bool,
                 dsa: bool) -> None:
        self._uniform = uniform
        self._gl_type = gl_type
        self._gl_getter = gl_getter
        self._gl_setter = gl_setter
        self._is_matrix = is_matrix
        self._idx_to_loc = {}  # Array index to uniform location mapping.
        self._dsa = dsa

        if self._uniform.length > 1:
            self._c_array = (gl_type * self._uniform.length * self._uniform.size)()
        else:
            self._c_array = (gl_type * self._uniform.size)()

        self._ptr = cast(self._c_array, POINTER(gl_type))

    def _get_location_for_index(self, index: int) -> int:
        """Get the location for the array name.

        It is not guaranteed that the location ID's of the uniform in the shader program will be a contiguous offset.

        On MacOS, the location ID of index 0 may be 1, and then index 2 might be 5. Whereas on Windows it may be a 1:1
        offset from 0 to index. Here, we store the location ID's of each index to ensure we are setting data on the
        right location.
        """
        loc = gl.glGetUniformLocation(self._uniform.program,
                                create_string_buffer(f"{self._uniform.name}[{index}]".encode()))
        return loc

    def _get_array_loc(self, index: int) -> int:
        try:
            return self._idx_to_loc[index]
        except KeyError:
            loc = self._idx_to_loc[index] = self._get_location_for_index(index)

        if loc == -1:
            msg = f"{self._uniform.name}[{index}] not found.\nThis may have been optimized out by the OpenGL driver if unused."
            raise ShaderException(msg)

        return loc

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

        try:
            value = self._c_array[key]
            return tuple(value) if self._uniform.length > 1 else value
        except IndexError:
            msg = f"{self._uniform.name}[{key}] not found. This may have been optimized out by the OpenGL driver if unused."
            raise ShaderException(msg)

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

        location = self._get_location_for_index(offset)

        if self._dsa:
            if self._is_matrix:
                self._gl_setter(self._uniform.program, location, size, GL_FALSE, data)
            else:
                self._gl_setter(self._uniform.program, location, size, data)
        else:
            glUseProgram(self._uniform.program)
            if self._is_matrix:
                self._gl_setter(location, size, GL_FALSE, data)
            else:
                self._gl_setter(location, size, data)

    def __repr__(self) -> str:
        data = [tuple(data) if self._uniform.length > 1 else data for data in self._c_array]
        return f"UniformArray(uniform={self._uniform}, data={data})"


_gl_matrices: tuple[int, ...] = (
    gl.GL_FLOAT_MAT2, gl.GL_FLOAT_MAT2x3, gl.GL_FLOAT_MAT2x4,
    gl.GL_FLOAT_MAT3, gl.GL_FLOAT_MAT3x2, gl.GL_FLOAT_MAT3x4,
    gl.GL_FLOAT_MAT4, gl.GL_FLOAT_MAT4x2, gl.GL_FLOAT_MAT4x3,
)


class _Uniform:
    type: int
    size: int
    location: int
    program: int
    name: str
    length: int
    get: Callable[[], Array[GLDataType] | GLDataType]
    set: Callable[[float], None] | Callable[[Sequence], None]

    __slots__ = 'type', 'size', 'location', 'length', 'count', 'get', 'set', 'program', 'name'

    def __init__(self, program: int, name: str, uniform_type: int, size: int, location: int, dsa: bool) -> None:
        self.name = name
        self.type = uniform_type
        self.size = size
        self.location = location
        self.program = program

        gl_type, gl_setter_legacy, gl_setter_dsa, length = _uniform_setters[uniform_type]
        gl_setter = gl_setter_dsa if dsa else gl_setter_legacy
        gl_getter = _uniform_getters[gl_type]

        # Argument length of data
        self.length = length

        is_matrix = uniform_type in _gl_matrices

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


def get_maximum_binding_count() -> int:
    """The maximum binding value that can be used for this hardware."""
    val = gl.GLint()
    gl.glGetIntegerv(gl.GL_MAX_UNIFORM_BUFFER_BINDINGS, byref(val))
    return val.value



class UniformBlock:
    """Not supported by OpenGL 2.0"""
    def __init__(self, program: ShaderProgram, name: str, index: int, size: int, binding: int,
                 uniforms: dict[int, tuple[str, GLDataType, int, int]], uniform_count: int) -> None:
        raise NotImplementedError


class UniformBufferObject:
    """Not supported by OpenGL 2.0"""
    def __init__(self, view_class: type[Structure], buffer_size: int, binding: int) -> None:
        """Initialize the Uniform Buffer Object with the specified Structure."""
        raise NotImplementedError


# Utility functions:

def _get_number(program_id: int, variable_type: int) -> int:
    """Get the number of active variables of the passed GL type."""
    number = gl.GLint(0)
    glGetProgramiv(program_id, variable_type, byref(number))
    return number.value


def _query_attribute(program_id: int, index: int) -> tuple[str, int, int]:
    """Query the name, type, and size of an Attribute by index."""
    asize = gl.GLint()
    atype = gl.GLenum()
    buf_size = 192
    aname = create_string_buffer(buf_size)
    try:
        glGetActiveAttrib(program_id, index, buf_size, None, asize, atype, aname)
        return aname.value.decode(), atype.value, asize.value
    except GLException as exc:
        raise ShaderException from exc


def _introspect_attributes(program_id: int) -> dict[str, Attribute]:
    """Introspect a Program's Attributes, and return a dict of accessors."""
    attributes = {}

    for index in range(_get_number(program_id, gl.GL_ACTIVE_ATTRIBUTES)):
        a_name, a_type, a_size = _query_attribute(program_id, index)
        loc = gl.glGetAttribLocation(program_id, create_string_buffer(a_name.encode('utf-8')))
        if loc == -1:  # not a user defined attribute
            continue
        count, fmt = _attribute_types[a_type]
        attributes[a_name] = Attribute(a_name, loc, count, fmt)

    if _debug_api_shaders:
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
    usize = gl.GLint()
    utype = gl.GLenum()
    buf_size = 192
    uname = create_string_buffer(buf_size)
    try:
        gl.glGetActiveUniform(program_id, index, buf_size, None, usize, utype, uname)
        return uname.value.decode(), utype.value, usize.value

    except GLException as exc:
        raise ShaderException from exc


def _introspect_uniforms(program_id: int, have_dsa: bool) -> dict[str, _Uniform]:
    """Introspect a Program's uniforms, and return a dict of accessors."""
    uniforms = {}

    for index in range(_get_number(program_id, gl.GL_ACTIVE_UNIFORMS)):
        u_name, u_type, u_size = _query_uniform(program_id, index)

        # Multidimensional arrays cannot be fully inspected via OpenGL calls and compile errors with 3.3.
        array_count = u_name.count("[0]")
        if array_count > 1 and u_name.count("[0][0]") != 0:
            msg = "Multidimensional arrays are not currently supported."
            raise ShaderException(msg)

        loc = gl.glGetUniformLocation(program_id, create_string_buffer(u_name.encode('utf-8')))
        if loc == -1:  # Skip uniforms that may be inside a Uniform Block
            continue

        # Strip [0] from array name for a more user-friendly name.
        if array_count != 0:
            u_name = u_name.strip('[0]')

        assert u_name not in uniforms, f"{u_name} exists twice in the shader. Possible name clash with an array."
        uniforms[u_name] = _Uniform(program_id, u_name, u_type, u_size, loc, have_dsa)

    if _debug_api_shaders:
        for uniform in uniforms.values():
            print(f" Found uniform: {uniform}")

    return uniforms


def _get_uniform_block_name(program_id: int, index: int) -> str:
    """Query the name of a Uniform Block, by index.

    Not supported by OpenGL 2.0
    """
    raise NotImplementedError


def _introspect_uniform_blocks(program: ShaderProgram | ComputeShaderProgram) -> dict[str, UniformBlock]:
    """Not supported by OpenGL 2.0"""
    return {}



# Shader & program classes:

class GLShaderSource(ShaderSource):
    """GLSL source container for making source parsing simpler.

    We support locating out attributes and applying #defines values.

    .. note:: We do assume the source is neat enough to be parsed this way and doesn't contain several statements in
              one line.
    """
    _type: gl.GLenum
    _lines: list[str]

    def __init__(self, source: str, source_type: gl.GLenum | int) -> None:
        """Create a shader source wrapper."""
        self._lines = source.strip().splitlines()
        self._type = source_type

        if not self._lines:
            msg = "Shader source is empty"
            raise ShaderException(msg)

        self._version = self._find_glsl_version()

        if "es" in pyglet.options.backend:
            self._patch_gles()

    def _patch_gles(self) -> None:
        """Patch the built-in shaders for GLES support.

        Probably will need better handling to not affect user shaders.
        """
        if self._lines[0].strip().startswith("#version"):
            self._lines[0] = ""

            self._lines.insert(0, "precision mediump float;")

            if self._type == gl.GL_VERTEX_SHADER:
                self._lines.insert(1, "uniform mat4 u_projection;")
                self._lines.insert(2, "uniform mat4 u_view;")

                for idx, line in enumerate(self._lines):
                    if "gl_ProjectionMatrix" in line or "gl_ModelViewMatrix" in line:
                        self._lines[idx] = line.replace("gl_ProjectionMatrix", "u_projection").replace(
                            "gl_ModelViewMatrix", "u_view")

        self._version = "es 1.00"

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


class Shader(ShaderBase):
    """OpenGL shader.

    Shader objects are compiled on instantiation.
    You can reuse a Shader object in multiple ShaderPrograms.
    """
    _context: OpenGLWindowContext | None
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
        super().__init__(source_string, shader_type)
        self._context = pyglet.graphics.api.global_backend.current_context
        self._id = None
        self.type = shader_type

        try:
            shader_gl_type = _shader_types[shader_type]
        except KeyError as err:
            msg = (
                f"shader_type '{shader_type}' is invalid."
                f"Valid types are: {list(_shader_types)}"
            )
            raise ShaderException(msg) from err

        supported_types = ("vertex", "fragment")
        if shader_type not in supported_types:
            msg = (f"shader_type '{shader_type}' is invalid."
                   f"Valid types for GL2 are: {supported_types}")
            raise ShaderException(msg)

        source_string = GLShaderSource(source_string, shader_gl_type).validate()
        shader_source_utf8 = source_string.encode("utf8")
        source_buffer_pointer = cast(c_char_p(shader_source_utf8), POINTER(c_char))
        source_length = c_int(len(shader_source_utf8))

        shader_id = gl.glCreateShader(shader_gl_type)
        self._id = shader_id
        gl.glShaderSource(shader_id, 1, byref(source_buffer_pointer), source_length)
        gl.glCompileShader(shader_id)

        status = c_int(0)
        gl.glGetShaderiv(shader_id, gl.GL_COMPILE_STATUS, byref(status))

        if status.value != GL_TRUE:
            source = self._get_shader_source(shader_id)
            source_lines = "{0}".format("\n".join(f"{str(i + 1).zfill(3)}: {line} "
                                                  for i, line in enumerate(source.split("\n"))))

            msg = (f"\n------------------------------------------------------------\n"
                   f"{source_lines}"
                   f"\n------------------------------------------------------------\n"
                   f"Shader compilation failed. Please review the error on the specified line.\n"
                   f"{self._get_shader_log(shader_id)}")

            raise ShaderException(msg)

        if _debug_api_shaders:
            print(self._get_shader_log(shader_id))

    @property
    def id(self) -> int:
        return self._id

    def _get_shader_log(self, shader_id: int) -> str:
        log_length = c_int(0)
        gl.glGetShaderiv(shader_id, GL_INFO_LOG_LENGTH, byref(log_length))
        result_str = create_string_buffer(log_length.value)
        gl.glGetShaderInfoLog(shader_id, log_length, None, result_str)
        if result_str.value:
            return (f"OpenGL returned the following message when compiling the "
                    f"'{self.type}' shader: \n{result_str.value.decode('utf8')}")

        return f"{self.type.capitalize()} Shader '{shader_id}' compiled successfully."

    @staticmethod
    def _get_shader_source(shader_id: int) -> str:
        """Get the shader source from the shader object."""
        source_length = c_int(0)
        gl.glGetShaderiv(shader_id, gl.GL_SHADER_SOURCE_LENGTH, source_length)
        source_str = create_string_buffer(source_length.value)
        gl.glGetShaderSource(shader_id, source_length, None, source_str)
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
                if _debug_api_shaders:
                    print(f"Destroyed {self.type} Shader '{self._id}'")
                self._id = None
            except (AttributeError, ImportError):
                pass  # Interpreter is shutting down

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, type={self.type})"


class ShaderProgram(ShaderProgramBase):
    """OpenGL shader program."""
    _id: int | None
    _context: OpenGLWindowContext | None
    _uniforms: dict[str, _Uniform]

    __slots__ = '_id', '_context', '_attributes', '_uniforms', '_uniform_blocks'

    def __init__(self, *shaders: Shader) -> None:
        """Initialize the ShaderProgram using at least two Shader instances."""
        super().__init__(*shaders)
        self._id = _link_program(*shaders)
        self._context = pyglet.graphics.api.global_backend.current_context

        if _debug_api_shaders:
            print(_get_program_log(self._id))

        # Query if Direct State Access is available:
        # Probably remove this for 2.0, unless someone deliberately wants to force 2.0
        # but leave capability up for the extension being supported. Is that possible?
        have_dsa = pyglet.graphics.api.have_version(4, 1) or pyglet.graphics.api.have_extension("GL_ARB_separate_shader_objects")
        self._attributes = _introspect_attributes(self._id)
        self._uniforms = _introspect_uniforms(self._id, have_dsa)
        self._uniform_blocks = _introspect_uniform_blocks(self)

    @property
    def id(self) -> int:
        return self._id

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
            if _debug_api_shaders:
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
            if _debug_api_shaders:
                warnings.warn(msg)
                return None

            raise ShaderException from err
        try:
            return uniform.get()
        except GLException as err:
            raise ShaderException from err

    def _vertex_list_create(self, count: int, mode: GeometryMode, indices: Sequence[int] | None = None,
                            instances: Sequence[str] | None = None, batch: Batch = None, group: Group = None,
                            **data: Any) -> VertexList | IndexedVertexList:
        attributes = {}
        initial_arrays = []

        instanced = instances is not None
        indexed = indices is not None

        # Probably just remove all of this?
        for name, fmt in data.items():
            current_attrib = self._attributes[name]
            try:
                if isinstance(fmt, tuple):
                    fmt, array = fmt  # noqa: PLW2901
                    initial_arrays.append((name, array))
                    current_attrib.data_type = fmt[0]
                    if len(fmt) == 2:
                        current_attrib.normalize = True

                attributes[name] = current_attrib#, 'format': fmt, 'instance': name in instances if instances else False}
            except KeyError:
                if _debug_api_shaders:
                    msg = (f"The attribute `{name}` was not found in the Shader Program.\n"
                           f"Please check the spelling, or it may have been optimized out by the OpenGL driver.\n"
                           f"Valid names: {list(attributes)}")
                    warnings.warn(msg)
                continue

        if _debug_api_shaders:
            if missing_data := [key for key in attributes if key not in data]:
                msg = (
                    f"No data was supplied for the following found attributes: `{missing_data}`.\n"
                )
                warnings.warn(msg)

        batch = batch or pyglet.graphics.get_default_batch()
        group = group or pyglet.graphics.ShaderGroup(program=self)
        domain = batch.get_domain(indexed, instanced, mode, group, attributes)

        # Create vertex list and initialize
        if indexed:
            vlist = domain.create(count, len(indices))
            start = vlist.start
            vlist.indices = [i + start for i in indices]
        else:
            vlist = domain.create(count)

        for name, array in initial_arrays:
            try:
                vlist.set_attribute_data(name, array)
            except KeyError:  # noqa: PERF203
                continue

        if instanced:
            vlist.instanced = True

        return vlist

    def vertex_list(self, count: int, mode: GeometryMode, batch: Batch = None, group: Group = None,
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

    def vertex_list_instanced(self, count: int, mode: GeometryMode, instance_attributes: Sequence[str], batch: Batch = None,
                              group: Group = None, **data: Any) -> VertexList:
        assert len(instance_attributes) > 0, "You must provide at least one attribute name to be instanced."
        return self._vertex_list_create(count, mode, None, instance_attributes, batch=batch, group=group, **data)

    def vertex_list_indexed(self, count: int, mode: GeometryMode, indices: Sequence[int], batch: Batch = None,
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

    def vertex_list_instanced_indexed(self, count: int, mode: GeometryMode, indices: Sequence[int],
                                      instance_attributes: Sequence[str], batch: Batch = None, group: Group = None,
                                      **data: Any) -> IndexedVertexList:
        assert len(instance_attributes) > 0, "You must provide at least one attribute name to be instanced."
        return self._vertex_list_create(count, mode, indices, instance_attributes, batch=batch, group=group, **data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"


class ComputeShaderProgram:
    """OpenGL Compute Shader Program.

    Not supported by OpenGL 2.0
    """

    def __init__(self, source: str) -> None:
        raise NotImplementedError
