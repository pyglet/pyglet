from __future__ import annotations

import re
import warnings
import weakref
from collections import defaultdict
from ctypes import (
    POINTER,
    Array,
    Structure,
    addressof,
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
    pointer,
    sizeof, c_void_p,
)
from typing import TYPE_CHECKING, Any, Callable, Sequence, Type, Union

import pyglet
from pyglet.graphics.api.gl import GLException, gl, OpenGLSurfaceContext
from pyglet.graphics.api.gl import (
    GL_FALSE,
    GL_INFO_LOG_LENGTH,
    GL_LINK_STATUS,
    GL_TRUE,
    GL_UNIFORM_BUFFER,
)
from pyglet.graphics.shader import ShaderSource, ShaderType, ShaderBase, Attribute, \
    ShaderProgramBase, UniformBufferObjectBase, GraphicsAttribute, AttributeView
from pyglet.graphics.shader import ShaderException

from pyglet.graphics.api.gl.buffer import BufferObject
from pyglet.graphics import GeometryMode

if TYPE_CHECKING:
    from _weakref import CallableProxyType
    from pyglet.customtypes import CTypesPointer, DataTypes, CType
    from pyglet.graphics import Batch, Group
    from pyglet.graphics.api.gl.vertexdomain import InstanceVertexList, InstanceIndexedVertexList
    from pyglet.graphics.vertexdomain import IndexedVertexList, VertexList

_debug_api_shaders = pyglet.options.debug_api_shaders


GLDataType = Union[Type[gl.GLint], Type[gl.GLfloat], Type[gl.GLboolean], int]
GLFunc = Callable

_c_types: dict[int, CType] = {
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


class GLAttribute(GraphicsAttribute):
    """Abstract accessor for an attribute in a mapped buffer."""
    gl_type: int
    """OpenGL type enumerant; for example, ``GL_FLOAT``"""

    def __init__(self, attribute: Attribute, view: AttributeView) -> None:
        """Create the attribute accessor.

        Args:
            attribute: The base shader Attribute object.
            view: The view intended for the buffer of this Attribute.
        """
        self._context = pyglet.graphics.api.core.current_context
        super().__init__(attribute, view)
        data_type = self.attribute.fmt.data_type
        self.gl_type = _data_type_to_gl_type[data_type]

        # If the data type is not normalized and is not a float, consider it an int pointer.
        self._is_int = data_type != "f" and self.attribute.fmt.normalized is False

    def enable(self) -> None:
        """Enable the attribute."""
        self._context.glEnableVertexAttribArray(self.attribute.location)

    def disable(self) -> None:
        self._context.glDisableVertexAttribArray(self.attribute.location)

    def set_pointer(self) -> None:
        """Setup this attribute to point to the currently bound buffer at the given offset."""
        if self._is_int:
            self._context.glVertexAttribIPointer(self.attribute.location, self.attribute.fmt.components, self.gl_type,
                                                self.view.stride, c_void_p(self.view.offset))
        else:
            self._context.glVertexAttribPointer(self.attribute.location, self.attribute.fmt.components, self.gl_type,
                                                self.attribute.fmt.normalized, self.view.stride, c_void_p(self.view.offset))

    def set_divisor(self) -> None:
        self._context.glVertexAttribDivisor(self.attribute.location, self.attribute.fmt.divisor)



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

    __slots__ = (
        '_c_array',
        '_context',
        '_dsa',
        '_gl_getter',
        '_gl_setter',
        '_gl_type',
        '_idx_to_loc',
        '_is_matrix',
        '_ptr',
        '_uniform',
    )

    def __init__(
        self, uniform: _Uniform, gl_getter: GLFunc, gl_setter: GLFunc, gl_type: GLDataType, is_matrix: bool, dsa: bool,
    ) -> None:
        self._context = pyglet.graphics.api.core.current_context
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
            self._context.glUseProgram(self._uniform.program)
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

    __slots__ = 'count', 'get', 'length', 'location', 'name', 'program', 'set', 'size', 'type'

    def __init__(self, ctx, program: int, name: str, uniform_type: int, size: int, location: int, dsa: bool) -> None:
        self.name = name
        self.type = uniform_type
        self.size = size
        self.location = location
        self.program = program

        gl_type, gl_setter_legacy, gl_setter_dsa, length = ctx.uniform_setters[uniform_type]
        gl_setter = gl_setter_dsa if dsa else gl_setter_legacy
        gl_getter = ctx.uniform_getters[gl_type]

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
            self.set = self._create_setter_func(ctx, program, location, gl_setter, c_array, length, ptr, is_matrix, dsa)

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
    def _create_setter_func(context: OpenGLSurfaceContext,program_id: int, location: int, gl_setter: GLFunc,
                            c_array: Array[GLDataType], length: int, ptr: CTypesPointer[GLDataType],
                            is_matrix: bool, dsa: bool) -> Callable[[float], None]:
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
                context.glUseProgram(program_id)
                c_array[:] = value
                gl_setter(location, 1, GL_FALSE, ptr)
        elif length == 1:
            def setter_func(value: float) -> None:
                context.glUseProgram(program_id)
                c_array[0] = value
                gl_setter(location, 1, ptr)
        elif length > 1:
            def setter_func(values: float) -> None:
                context.glUseProgram(program_id)
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
    return pyglet.graphics.api.core.current_context.get_info().MAX_UNIFORM_BUFFER_BINDINGS


class _UBOBindingManager:
    """Manages the global Uniform Block binding assignments in the OpenGL context."""
    _in_use: set[int]
    _pool: list[int]
    _max_binding_count: int
    _ubo_names: dict[str, int]
    _ubo_programs: defaultdict[Any, weakref.WeakSet[ShaderProgram]]

    def __init__(self) -> None:
        self._ubo_programs = defaultdict(weakref.WeakSet)
        # Reserve 'WindowBlock' for 0.
        self._ubo_names = {'WindowBlock': 0}
        self._max_binding_count = get_maximum_binding_count()
        self._pool = list(range(1, self._max_binding_count))
        self._in_use = {0}

    @property
    def max_value(self) -> int:
        return self._max_binding_count

    def get_name(self, binding: int) -> str | None:
        """Return the uniform name associated with the binding number."""
        for name, current_binding in self._ubo_names.items():
            if binding == current_binding:
                return name
        return None

    def binding_exists(self, binding: int) -> bool:
        """Check if a binding index value is in use."""
        return binding in self._in_use

    def add_explicit_binding(self, shader_program: ShaderProgram, ub_name: str, binding: int) -> None:
        """Used when a uniform block has set its own binding point."""
        self._ubo_programs[ub_name].add(shader_program)
        self._ubo_names[ub_name] = binding
        if binding in self._pool:
            self._pool.remove(binding)
        self._in_use.add(binding)

    def get_binding(self, shader_program: ShaderProgram, ub_name: str) -> int:
        """Retrieve a global Uniform Block Binding ID value."""
        self._ubo_programs[ub_name].add(shader_program)

        if ub_name in self._ubo_names:
            return self._ubo_names[ub_name]

        self._check_freed_bindings()

        binding = self._get_new_binding()
        self._ubo_names[ub_name] = binding
        return binding

    def _check_freed_bindings(self) -> None:
        """Find and remove any Uniform Block names that no longer have a shader in use."""
        for ubo_name in list(self._ubo_programs):
            if ubo_name != 'WindowBlock' and not self._ubo_programs[ubo_name]:
                del self._ubo_programs[ubo_name]
                # Return the binding number to the pool.
                self.return_binding(self._ubo_names[ubo_name])
                del self._ubo_names[ubo_name]

    def _get_new_binding(self) -> int:
        if not self._pool:
            msg = "All Uniform Buffer Bindings are in use."
            raise ValueError(msg)

        number = self._pool.pop(0)
        self._in_use.add(number)
        return number

    def return_binding(self, index: int) -> None:
        if index in self._in_use:
            self._pool.append(index)
            self._in_use.remove(index)
        else:
            msg = f"Uniform binding point: {index} is not in use."
            raise ValueError(msg)

# Regular expression to detect array indices like [0], [1], etc.
array_regex = re.compile(r"(\w+)\[(\d+)\]")

class UniformBlock:
    program: CallableProxyType[Callable[..., Any] | Any] | Any
    name: str
    index: int
    size: int
    binding: int
    uniforms: dict[int, tuple[str, GLDataType, int, int]]
    view_cls: type[Structure] | None
    __slots__ = '_context', 'binding', 'index', 'name', 'program', 'size', 'uniform_count', 'uniforms', 'view_cls'

    def __init__(self, program: ShaderProgram, name: str, index: int, size: int, binding: int,
                 uniforms: dict[int, tuple[str, GLDataType, int, int]], uniform_count: int) -> None:
        """Initialize a uniform block for a ShaderProgram."""
        self._context = pyglet.graphics.api.core.current_context
        self.program = weakref.proxy(program)
        self.name = name
        self.index = index
        self.size = size
        self.binding = binding
        self.uniforms = uniforms
        self.uniform_count = uniform_count
        self.view_cls = self._create_structure()

    def _create_structure(self):
        return self._introspect_uniforms()

    def bind(self, ubo: UniformBufferObject) -> None:
        """Bind buffer to the binding point."""
        self._context.glBindBufferBase(GL_UNIFORM_BUFFER, self.binding, ubo.buffer.id)

    def create_ubo(self) -> UniformBufferObject:
        """Create a new UniformBufferObject from this uniform block."""
        return UniformBufferObject(self._context, self.view_cls, self.size, self.binding)

    def set_binding(self, binding: int) -> None:
        """Rebind the Uniform Block to a new binding index number.

        This only affects the program this Uniform Block is derived from.

        Binding value of 0 is reserved for the Pyglet's internal uniform block named ``WindowBlock``.

        .. warning:: By setting a binding manually, the user is expected to manage all Uniform Block bindings
                     for all shader programs manually. Since the internal global ID's will be unaware of changes set
                     by this function, collisions may occur if you use a lower number.

        .. note:: You must call ``create_ubo`` to get another Uniform Buffer Object after calling this,
                  as the previous buffers are still bound to the old binding point.
        """
        assert binding != 0, "Binding 0 is reserved for the internal Pyglet 'WindowBlock'."
        assert pyglet.graphics.api.core.current_context is not None, "No context available."
        manager: _UBOBindingManager = pyglet.graphics.api.core.current_context.ubo_manager
        if binding >= manager.max_value:
            msg = f"Binding value exceeds maximum allowed by hardware: {manager.max_value}"
            raise ShaderException(msg)
        existing_name = manager.get_name(binding)
        if existing_name and existing_name != self.name:
            msg = f"Binding: {binding} was in use by {existing_name}, and has been overridden."
            warnings.warn(msg)

        self.binding = binding
        self._context.glUniformBlockBinding(self.program.id, self.index, self.binding)

    def _introspect_uniforms(self) -> type[Structure]:
        """Introspect the block's structure and return a ctypes struct for manipulating the uniform block's members."""
        p_id = self.program.id
        index = self.index

        active_count = self.uniform_count

        # Query the uniform index order and each uniform's offset:
        indices = (gl.GLuint * active_count)()
        offsets = (gl.GLint * active_count)()
        indices_ptr = cast(addressof(indices), POINTER(gl.GLint))
        offsets_ptr = cast(addressof(offsets), POINTER(gl.GLint))
        self._context.glGetActiveUniformBlockiv(p_id, index, gl.GL_UNIFORM_BLOCK_ACTIVE_UNIFORM_INDICES, indices_ptr)
        self._context.glGetActiveUniformsiv(p_id, active_count, indices, gl.GL_UNIFORM_OFFSET, offsets_ptr)

        # Offsets may be returned in non-ascending order, sort them with the corresponding index:
        _oi = sorted(zip(offsets, indices), key=lambda x: x[0])
        offsets = [x[0] for x in _oi] + [self.size]
        indices = (gl.GLuint * active_count)(*(x[1] for x in _oi))

        # # Query other uniform information:
        # gl_types = (gl.GLint * active_count)()
        # mat_stride = (gl.GLint * active_count)()
        # gl_types_ptr = cast(addressof(gl_types), POINTER(gl.GLint))
        # stride_ptr = cast(addressof(mat_stride), POINTER(gl.GLint))
        # gl.glGetActiveUniformsiv(p_id, active_count, indices, gl.GL_UNIFORM_TYPE, gl_types_ptr)
        # gl.glGetActiveUniformsiv(p_id, active_count, indices, gl.GL_UNIFORM_MATRIX_STRIDE, stride_ptr)

        array_sizes = {}
        dynamic_structs = {}
        p_count = 0

        def rep_func(s):
            names_fields = ", ".join((f"{k}={v.__name__}" for k, v in dict(s._fields_).items()))
            return f"UBOView({names_fields})"

        def build_ctypes_struct(name: str, struct_dict: dict) -> type:
            fields = []
            for field_name, field_type in struct_dict.items():
                if isinstance(field_type, dict):
                    # Recursive call for nested structures
                    element_struct = build_ctypes_struct(field_name, field_type)
                    field_type = element_struct  # noqa: PLW2901
                    if field_name in array_sizes and array_sizes[field_name] > 1:
                        field_type = element_struct * array_sizes[field_name]  # noqa: PLW2901
                else:
                    # This handles base types like c_float_Array_2, which isn't a dict.
                    fields.append((field_name, field_type))
                    continue
                fields.append((field_name, field_type))

            return type(name.title(), (Structure,), {"_fields_": fields, "__repr__": rep_func})

        # Build a ctypes Structure of the uniforms including arrays and nested structures.
        for i in range(active_count):
            u_name, gl_type, length, u_size = self.uniforms[indices[i]]

            parts = u_name.split(".")

            current_structure = dynamic_structs
            for part_idx, part in enumerate(parts):
                part_name = part
                match = array_regex.match(part_name)
                if match:  # It's an array
                    arr_name, index = match.groups()
                    part_name = arr_name

                    if part_idx != len(parts) - 1:
                        index = int(index)  # Convert the index to an integer

                        # Track array sizes for the current array name
                        array_sizes[arr_name] = max(array_sizes.get(arr_name, 0), index + 1)
                        if array_sizes[arr_name] > 1:
                            break

                        if arr_name not in current_structure:
                            current_structure[arr_name] = {}

                        current_structure = current_structure[arr_name]  # Move to the correct index of the array
                        continue

                # The end should be a regular attribute
                if part_idx == len(parts) - 1:  # The last part is the actual type
                    if u_size > 1:
                        # If size > 1, treat as an array of type
                        if length > 1:
                            current_structure[part_name] = (gl_type * length) * u_size
                        else:
                            current_structure[part_name] = gl_type * u_size
                    else:
                        if length > 1:
                            current_structure[part_name] = gl_type * length
                        else:
                            current_structure[part_name] = gl_type

                    offset_size = offsets[i + 1] - offsets[i]
                    c_type_size = sizeof(current_structure[part_name])
                    padding = offset_size - c_type_size

                    # TODO: Cannot get a different stride on my hardware. Needs testing.
                    # is_matrix = gl_types[i] in _gl_matrices
                    # if is_matrix:
                    #     stride_padding = (mat_stride[i] // 4) * 4 - offset_size
                    #     if stride_padding > 0:
                    #         view_fields.append((f'_matrix_stride{i}', c_byte * stride_padding))

                    if padding > 0:
                        current_structure[f'_padding{p_count}'] = c_byte * padding
                        p_count += 1
                else:
                    if part_name not in current_structure:
                        current_structure[part_name] = {}
                    current_structure = current_structure[part_name]  # Drill down into nested structures

        # Custom ctypes Structure for Uniform access:
        return build_ctypes_struct('View', dynamic_structs)

    def _actual_binding_point(self) -> int:
        """Queries OpenGL to find what the bind point currently is."""
        binding = gl.GLint()
        gl.glGetActiveUniformBlockiv(self.program.id, self.index, gl.GL_UNIFORM_BLOCK_BINDING, binding)
        return binding.value

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(program={self.program.id}, location={self.index}, size={self.size}, "
                f"binding={self.binding})")


class UniformBufferObject(UniformBufferObjectBase):
    buffer: BufferObject
    view: Structure
    _view_ptr: CTypesPointer[Structure]
    binding: int

    __slots__ = '_view_ptr', 'binding', 'buffer', 'view'

    def __init__(self, context: OpenGLSurfaceContext, view_class: type[Structure], buffer_size: int, binding: int) -> None:
        """Initialize the Uniform Buffer Object with the specified Structure."""
        self._context = context
        self.buffer = BufferObject(context, buffer_size, target=GL_UNIFORM_BUFFER)
        self.view = view_class()
        self._view_ptr = pointer(self.view)
        self.binding = binding

    @property
    def id(self) -> int:
        """The buffer ID associated with this UBO."""
        return self.buffer.id

    def read(self) -> Array:
        """Read the byte contents of the buffer."""
        return self.buffer.get_data()

    def __enter__(self) -> Structure:
        return self.view

    def __exit__(self, _exc_type, _exc_val, _exc_tb) -> None:  # noqa: ANN001
        self.buffer.set_data(self._view_ptr)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.buffer.id}, binding={self.binding})"


# Utility functions:

def _get_number(ctx, program_id: int, variable_type: int) -> int:
    """Get the number of active variables of the passed GL type."""
    number = gl.GLint(0)
    ctx.glGetProgramiv(program_id, variable_type, byref(number))
    return number.value


def _query_attribute(ctx, program_id: int, index: int) -> tuple[str, int, int]:
    """Query the name, type, and size of an Attribute by index."""
    asize = gl.GLint()
    atype = gl.GLenum()
    buf_size = 192
    aname = create_string_buffer(buf_size)
    try:
        ctx.glGetActiveAttrib(program_id, index, buf_size, None, asize, atype, aname)
        return aname.value.decode(), atype.value, asize.value
    except GLException as exc:
        raise ShaderException from exc


def _introspect_attributes(ctx, program_id: int) -> dict[str, Attribute]:
    """Introspect a Program's Attributes, and return a dict of accessors."""
    attributes = {}

    for index in range(_get_number(ctx, program_id, gl.GL_ACTIVE_ATTRIBUTES)):
        a_name, a_type, a_size = _query_attribute(ctx, program_id, index)
        loc = ctx.glGetAttribLocation(program_id, create_string_buffer(a_name.encode('utf-8')))
        if loc == -1:  # not a user defined attribute
            continue
        count, fmt = _attribute_types[a_type]
        attributes[a_name] = Attribute(a_name, loc, count, fmt)

    if _debug_api_shaders:
        for attribute in attributes.values():
            print(f" Found attribute: {attribute}")

    return attributes


def _link_program(ctx, *shaders: Shader) -> int:
    """Link one or more Shaders into a ShaderProgram.

    Returns:
        The ID assigned to the linked ShaderProgram.
    """
    program_id = ctx.glCreateProgram()
    for shader in shaders:
        ctx.glAttachShader(program_id, shader.id)
    ctx.glLinkProgram(program_id)

    # Check the link status of program
    status = c_int()
    ctx.glGetProgramiv(program_id, GL_LINK_STATUS, byref(status))
    if not status.value:
        length = c_int()
        ctx.glGetProgramiv(program_id, GL_INFO_LOG_LENGTH, length)
        log = c_buffer(length.value)
        ctx.glGetProgramInfoLog(program_id, len(log), None, log)
        msg = f"Error linking shader program:\n{log.value.decode()}"
        raise ShaderException(msg)

    # Shader objects no longer needed
    for shader in shaders:
        ctx.glDetachShader(program_id, shader.id)

    return program_id


def _get_program_log(ctx, program_id: int) -> str:
    """Query a ShaderProgram link logs."""
    result = c_int(0)
    ctx.glGetProgramiv(program_id, GL_INFO_LOG_LENGTH, byref(result))
    result_str = create_string_buffer(result.value)
    ctx.glGetProgramInfoLog(program_id, result, None, result_str)

    if result_str.value:
        return f"OpenGL returned the following message when linking the program: \n{result_str.value}"

    return f"Program '{program_id}' linked successfully."


def _query_uniform(ctx, program_id: int, index: int) -> tuple[str, int, int]:
    """Query the name, type, and size of a Uniform by index."""
    usize = gl.GLint()
    utype = gl.GLenum()
    buf_size = 192
    uname = create_string_buffer(buf_size)
    try:
        ctx.glGetActiveUniform(program_id, index, buf_size, None, usize, utype, uname)
        return uname.value.decode(), utype.value, usize.value

    except GLException as exc:
        raise ShaderException from exc


def _introspect_uniforms(ctx, program_id: int, have_dsa: bool) -> dict[str, _Uniform]:
    """Introspect a Program's uniforms, and return a dict of accessors."""
    uniforms = {}

    for index in range(_get_number(ctx, program_id, gl.GL_ACTIVE_UNIFORMS)):
        u_name, u_type, u_size = _query_uniform(ctx, program_id, index)

        # Multidimensional arrays cannot be fully inspected via OpenGL calls and compile errors with 3.3.
        array_count = u_name.count("[0]")
        if array_count > 1 and u_name.count("[0][0]") != 0:
            msg = "Multidimensional arrays are not currently supported."
            raise ShaderException(msg)

        loc = ctx.glGetUniformLocation(program_id, create_string_buffer(u_name.encode('utf-8')))
        if loc == -1:  # Skip uniforms that may be inside a Uniform Block
            continue

        # Strip [0] from array name for a more user-friendly name.
        if array_count != 0:
            u_name = u_name.strip('[0]')

        assert u_name not in uniforms, f"{u_name} exists twice in the shader. Possible name clash with an array."
        uniforms[u_name] = _Uniform(ctx, program_id, u_name, u_type, u_size, loc, have_dsa)

    if _debug_api_shaders:
        for uniform in uniforms.values():
            print(f" Found uniform: {uniform}")

    return uniforms


def _get_uniform_block_name(ctx, program_id: int, index: int) -> str:
    """Query the name of a Uniform Block, by index."""
    buf_size = 128
    size = c_int(0)
    name_buf = create_string_buffer(buf_size)
    try:
        ctx.glGetActiveUniformBlockName(program_id, index, buf_size, size, name_buf)
        return name_buf.value.decode()
    except GLException:
        msg = f"Unable to query UniformBlock name at index: {index}"
        raise ShaderException(msg)  # noqa: B904


def _introspect_uniform_blocks(ctx, program: ShaderProgram | ComputeShaderProgram) -> dict[str, UniformBlock]:
    uniform_blocks = {}
    program_id = program.id

    for index in range(_get_number(ctx, program_id, gl.GL_ACTIVE_UNIFORM_BLOCKS)):
        name = _get_uniform_block_name(ctx, program_id, index)

        num_active = gl.GLint()
        block_data_size = gl.GLint()
        binding = gl.GLint()

        ctx.glGetActiveUniformBlockiv(program_id, index, gl.GL_UNIFORM_BLOCK_ACTIVE_UNIFORMS, num_active)
        ctx.glGetActiveUniformBlockiv(program_id, index, gl.GL_UNIFORM_BLOCK_DATA_SIZE, block_data_size)
        ctx.glGetActiveUniformBlockiv(program_id, index, gl.GL_UNIFORM_BLOCK_BINDING, binding)

        indices = (gl.GLuint * num_active.value)()
        indices_ptr = cast(addressof(indices), POINTER(gl.GLint))
        ctx.glGetActiveUniformBlockiv(program_id, index, gl.GL_UNIFORM_BLOCK_ACTIVE_UNIFORM_INDICES, indices_ptr)

        uniforms: dict[int, tuple[str, GLDataType, int, int]] = {}

        if not hasattr(pyglet.graphics.api.core.current_context, "ubo_manager"):
            pyglet.graphics.api.core.current_context.ubo_manager = _UBOBindingManager()

        manager = pyglet.graphics.api.core.current_context.ubo_manager

        for block_uniform_index in indices:
            uniform_name, u_type, u_size = _query_uniform(ctx, program_id, block_uniform_index)

            # Remove block name.
            if uniform_name.startswith(f"{name}."):
                uniform_name = uniform_name[len(name) + 1:]  # Strip 'block_name.' part

            if uniform_name.count("[0][0]") > 0:
                msg = "Multidimensional arrays are not currently supported."
                raise ShaderException(msg)

            gl_type, _, _, length = ctx.uniform_setters[u_type]
            uniforms[block_uniform_index] = (uniform_name, gl_type, length, u_size)

        binding_index = binding.value
        if pyglet.options.shader_bind_management:
            # If no binding is specified in GLSL, then assign it internally.
            if binding.value == 0:
                binding_index = manager.get_binding(program, name)

                # This might cause an error if index > GL_MAX_UNIFORM_BUFFER_BINDINGS, but surely no
                # one would be crazy enough to use more than 36 uniform blocks, right?
                ctx.glUniformBlockBinding(program_id, index, binding_index)
            else:
                # If a binding was manually set in GLSL, just check if the values collide to warn the user.
                _block_name = manager.get_name(binding.value)
                if _block_name and _block_name != name:
                    msg = (f"{program} explicitly set '{name}' to {binding.value} in the shader. '{_block_name}' has "
                           f"been overridden.")
                    warnings.warn(msg)
                manager.add_explicit_binding(program, name, binding.value)

        uniform_blocks[name] = UniformBlock(program, name, index, block_data_size.value, binding_index, uniforms,
                                            len(indices))

        if _debug_api_shaders:
            for block in uniform_blocks.values():
                print(f" Found uniform block: {block}")

    return uniform_blocks


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

        if pyglet.graphics.api.core.current_context.get_info().get_opengl_api() == "gles":
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
    _context: OpenGLSurfaceContext | None
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
        self._context = pyglet.graphics.api.core.current_context
        self._id = None
        self.type = shader_type

        shader_gl_type = _shader_types[shader_type]
        source_string = self.get_string_class()(source_string, shader_gl_type).validate()
        shader_source_utf8 = source_string.encode("utf8")
        source_buffer_pointer = cast(c_char_p(shader_source_utf8), POINTER(c_char))
        source_length = c_int(len(shader_source_utf8))

        shader_id = self._context.glCreateShader(shader_gl_type)
        self._id = shader_id
        self._context.glShaderSource(shader_id, 1, byref(source_buffer_pointer), source_length)
        self._context.glCompileShader(shader_id)

        status = c_int(0)
        self._context.glGetShaderiv(shader_id, gl.GL_COMPILE_STATUS, byref(status))

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

    @staticmethod
    def get_string_class() -> type[GLShaderSource]:
        return GLShaderSource

    @classmethod
    def supported_shaders(cls: type[Shader]) -> tuple[ShaderType, ...]:
        return 'vertex', 'fragment', 'compute', 'geometry', 'tesscontrol', 'tessevaluation'

    @property
    def id(self) -> int:
        return self._id

    def _get_shader_log(self, shader_id: int) -> str:
        log_length = c_int(0)
        self._context.glGetShaderiv(shader_id, GL_INFO_LOG_LENGTH, byref(log_length))
        result_str = create_string_buffer(log_length.value)
        self._context.glGetShaderInfoLog(shader_id, log_length, None, result_str)
        if result_str.value:
            return (f"OpenGL returned the following message when compiling the "
                    f"'{self.type}' shader: \n{result_str.value.decode('utf8')}")

        return f"{self.type.capitalize()} Shader '{shader_id}' compiled successfully."

    def _get_shader_source(self, shader_id: int) -> str:
        """Get the shader source from the shader object."""
        source_length = c_int(0)
        self._context.glGetShaderiv(shader_id, gl.GL_SHADER_SOURCE_LENGTH, source_length)
        source_str = create_string_buffer(source_length.value)
        self._context.glGetShaderSource(shader_id, source_length, None, source_str)
        return source_str.value.decode('utf8')

    def delete(self) -> None:
        """Deletes the shader.

        This cannot be undone.
        """
        self._context.glDeleteShader(self._id)
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
    _context: OpenGLSurfaceContext | None
    _uniforms: dict[str, _Uniform]
    _uniform_blocks: dict[str, UniformBlock]

    __slots__ = '_attributes', '_context', '_id', '_uniform_blocks', '_uniforms'

    def __init__(self, *shaders: Shader) -> None:
        """Initialize the ShaderProgram using at least two Shader instances."""
        super().__init__(*shaders)

        self._context = pyglet.graphics.api.core.current_context
        self._id = _link_program(self._context, *shaders)

        if _debug_api_shaders:
            print(_get_program_log(self._id))

        # Query if Direct State Access is available:

        have_dsa = pyglet.graphics.api.have_version(4, 1) or pyglet.graphics.api.have_extension("GL_ARB_separate_shader_objects")
        self._attributes = _introspect_attributes(self._context, self._id)
        self._uniforms = _introspect_uniforms(self._context, self._id, have_dsa)
        self._uniform_blocks = self._get_uniform_blocks()

    def _get_uniform_blocks(self) -> dict[str, UniformBlock]:
        """Return Uniform Block information."""
        return _introspect_uniform_blocks(self._context, self)

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
        self._context.glUseProgram(self._id)

    def stop(self) -> None:
        self._context.glUseProgram(0)

    __enter__ = use
    bind = use
    unbind = stop

    def __exit__(self, *_) -> None:  # noqa: ANN002
        self._context.glUseProgram(0)

    def delete(self) -> None:
        self._context.glDeleteProgram(self._id)
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
            msg = (
                f"A Uniform with the name `{item}` was not found.\n"
                f"The spelling may be incorrect or, if not in use, it "
                f"may have been optimized out by the OpenGL driver."
            )
            if _debug_api_shaders:
                warnings.warn(msg)
                return None

            raise ShaderException from err
        try:
            return uniform.get()
        except GLException as err:
            raise ShaderException from err

    def _vertex_list_create(self, count: int, mode: GeometryMode, indices: Sequence[int] | None = None,
                            instances: dict[str, int] | None = None, batch: Batch = None, group: Group = None,
                            **data: Any) -> VertexList | InstanceVertexList | IndexedVertexList | InstanceIndexedVertexList:
        assert isinstance(mode, GeometryMode), f"Mode {mode} is not geometry mode."
        attributes = {}
        initial_arrays = []

        indexed = indices is not None

        # Probably just remove all of this?
        for name, fmt in data.items():
            try:
                current_attrib = self._attributes[name]
            except KeyError:
                msg = f"Attribute {name} not found. Existing attributes: {list(self._attributes.keys())}"
                raise ShaderException(msg) from None
            try:
                if isinstance(fmt, tuple):
                    fmt, array = fmt  # noqa: PLW2901
                    initial_arrays.append((name, array))
                    normalize = len(fmt) == 2
                    current_attrib.set_data_type(fmt[0], normalize)

                attributes[name] = current_attrib#, 'format': fmt, 'instance': name in instances if instances else False}
            except KeyError:
                if _debug_api_shaders:
                    msg = (f"The attribute `{name}` was not found in the Shader Program.\n"
                           f"Please check the spelling, or it may have been optimized out by the OpenGL driver.\n"
                           f"Valid names: {list(attributes)}")
                    warnings.warn(msg)
                continue

        if instances:
            for name, divisor in instances.items():
                attributes[name].set_divisor(divisor)

        if _debug_api_shaders and (missing_data := [key for key in attributes if key not in data]):
            msg = (
                f"No data was supplied for the following found attributes: `{missing_data}`.\n"
            )
            warnings.warn(msg)

        batch = batch or pyglet.graphics.get_default_batch()
        group = group or pyglet.graphics.ShaderGroup(program=self)
        domain = batch.get_domain(indexed, bool(instances), mode, group, attributes)

        # Create vertex list and initialize
        vlist = domain.create(group, count, indices)

        for name, array in initial_arrays:
            vlist.set_attribute_data(name, array)

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

    def vertex_list_instanced(self, count: int, mode: GeometryMode, instance_attributes: Sequence[str],
                              batch: Batch | None = None, group: Group | None = None, **data: Any) -> InstanceVertexList:
        assert len(instance_attributes) > 0, "You must provide at least one attribute name to be instanced."
        return self._vertex_list_create(count, mode, None, instance_attributes, batch=batch, group=group, **data)

    def vertex_list_indexed(self, count: int, mode: GeometryMode, indices: Sequence[int],
                            batch: Batch | None = None, group: Group | None = None, **data: Any) -> IndexedVertexList:
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

    def vertex_list_instanced_indexed(self, count: int, *, mode: GeometryMode, indices: Sequence[int],
                                      instance_attributes: Sequence[str],
                                      batch: Batch | None = None, group: Group | None = None,
                                      **data: Any) -> IndexedVertexList:
        assert len(instance_attributes) > 0, "You must provide at least one attribute name to be instanced."
        return self._vertex_list_create(count, mode, indices, instance_attributes, batch=batch, group=group, **data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"


class ComputeShaderProgram:
    """OpenGL Compute Shader Program."""
    _context: OpenGLSurfaceContext | None
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

        if not (pyglet.graphics.api.have_version(4, 3) or pyglet.graphics.api.have_extension("GL_ARB_compute_shader")):
            msg = (
                "Compute Shader not supported. OpenGL Context version must be at least "
                "4.3 or higher, or 4.2 with the 'GL_ARB_compute_shader' extension."
            )
            raise ShaderException(msg)

        self._shader = Shader(source, 'compute')
        self._context = pyglet.graphics.api.core.current_context
        self._id = _link_program(self._context, self._shader)

        if _debug_api_shaders:
            print(_get_program_log(self._id))

        self._uniforms = _introspect_uniforms(self._id, True)
        self._uniform_blocks = _introspect_uniform_blocks(self._context, self)

        self.max_work_group_size = self._get_tuple(gl.GL_MAX_COMPUTE_WORK_GROUP_SIZE)  # x, y, z
        self.max_work_group_count = self._get_tuple(gl.GL_MAX_COMPUTE_WORK_GROUP_COUNT)  # x, y, z
        self.max_shared_memory_size = self._get_value(gl.GL_MAX_COMPUTE_SHARED_MEMORY_SIZE)
        self.max_work_group_invocations = self._get_value(gl.GL_MAX_COMPUTE_WORK_GROUP_INVOCATIONS)

    @staticmethod
    def _get_tuple(parameter: int) -> tuple[int, int, int]:
        val_x = gl.GLint()
        val_y = gl.GLint()
        val_z = gl.GLint()
        for i, value in enumerate((val_x, val_y, val_z)):
            gl.glGetIntegeri_v(parameter, i, byref(value))
        return val_x.value, val_y.value, val_z.value

    @staticmethod
    def _get_value(parameter: int) -> int:
        val = gl.GLint()
        gl.glGetIntegerv(parameter, byref(val))
        return val.value

    def dispatch(self, x: int = 1, y: int = 1, z: int = 1, barrier: int = gl.GL_ALL_BARRIER_BITS) -> None:
        """Launch one or more compute work groups.

        The ComputeShaderProgram should be active (bound) before calling
        this method. The x, y, and z parameters specify the number of local
        work groups that will be  dispatched in the X, Y and Z dimensions.
        """
        self._context.glDispatchCompute(x, y, z)
        if barrier:
            self._context.glMemoryBarrier(barrier)

    @property
    def id(self) -> int:
        return self._id

    @property
    def uniforms(self) -> dict[str, dict[str, Any]]:
        return {n: {'location': u.location, 'length': u.length, 'size': u.size} for n, u in self._uniforms.items()}

    @property
    def uniform_blocks(self) -> dict[str, UniformBlock]:
        return self._uniform_blocks

    def use(self) -> None:
        self._context.glUseProgram(self._id)

    def stop(self) -> None:
        self._context.glUseProgram(0)

    __enter__ = use
    bind = use
    unbind = stop

    def __exit__(self, *_) -> None:  # noqa: ANN002
        self._context.glUseProgram(0)

    def delete(self) -> None:
        self._context.glDeleteProgram(self._id)
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
            if _debug_api_shaders:
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
            if _debug_api_shaders:
                warnings.warn(msg)
                return None

            raise ShaderException(msg) from err
        try:
            return uniform.get()
        except GLException as err:
            raise ShaderException from err
