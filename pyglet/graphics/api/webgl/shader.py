from __future__ import annotations

import re
import warnings
import weakref
from collections import defaultdict
from ctypes import (
    POINTER,
    Array,
    Structure,
    c_buffer,
    c_byte,
    c_double,
    c_float,
    c_int,
    c_short,
    c_ubyte,
    c_uint,
    c_ushort,
    cast,
    pointer,
    sizeof,
)
from typing import TYPE_CHECKING, Any, Callable, Sequence, Type, Union

import pyglet

# from pyglet.graphics.api.webgl.buffer import BufferObject
from pyglet.graphics import GeometryMode
from pyglet.graphics.api.webgl import gl
from pyglet.graphics.api.webgl.buffer import BufferObject
from pyglet.graphics.api.webgl.gl import (
    GL_FALSE,
    GL_INFO_LOG_LENGTH,
    GL_LINK_STATUS,
    GL_TRUE,
    GL_UNIFORM_BUFFER,
)
from pyglet.graphics.shader import (
    Attribute,
    ShaderBase,
    ShaderException,
    ShaderProgramBase,
    ShaderSource,
    ShaderType,
    UniformBufferObjectBase,
    AttributeView,
    GraphicsAttribute,
)

try:
    import js
except ImportError:
    pass


class GLException(Exception):
    pass


if TYPE_CHECKING:
    from _weakref import CallableProxyType

    from pyglet.customtypes import CTypesPointer, DataTypes
    from pyglet.graphics import Batch, Group
    from pyglet.graphics.api.webgl.context import OpenGLSurfaceContext
    from pyglet.graphics.api.webgl.webgl_js import WebGL2RenderingContext, WebGLProgram, WebGLRenderingContext
    from pyglet.graphics.shader import CTypesDataType
    from pyglet.graphics.vertexdomain import IndexedVertexList, VertexList

_debug_api_shaders = pyglet.options.debug_api_shaders


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
    'b': gl.GL_BYTE,  # signed byte
    'B': gl.GL_UNSIGNED_BYTE,  # unsigned byte
    'h': gl.GL_SHORT,  # signed short
    'H': gl.GL_UNSIGNED_SHORT,  # unsigned short
    'i': gl.GL_INT,  # signed int
    'I': gl.GL_UNSIGNED_INT,  # unsigned int
    'f': gl.GL_FLOAT,  # float
    'q': gl.GL_INT,  # signed long long (Requires GL_INT64_NV if available. Just use int.)
    'Q': gl.GL_UNSIGNED_INT,  # unsigned long long (Requires GL_UNSIGNED_INT64_NV if available. Just use uint.)
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


# Accessor classes:

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
        self._gl = pyglet.graphics.api.core.current_context.gl
        super().__init__(attribute, view)
        data_type = self.attribute.fmt.data_type
        self.gl_type = _data_type_to_gl_type[data_type]

        # If the data type is not normalized and is not a float, consider it an int pointer.
        self._is_int = data_type != "f" and self.attribute.fmt.normalized is False

    def enable(self) -> None:
        """Enable the attribute."""
        self._gl.enableVertexAttribArray(self.attribute.location)

    def disable(self) -> None:
        self._gl.disableVertexAttribArray(self.attribute.location)

    def set_pointer(self) -> None:
        """Setup this attribute to point to the currently bound buffer at the given offset."""
        if self._is_int:
            self._gl.vertexAttribIPointer(
                self.attribute.location,
                self.attribute.fmt.components,
                self.gl_type,
                self.view.stride,
                self.view.offset,
            )
        else:
            self._gl.vertexAttribPointer(
                self.attribute.location,
                self.attribute.fmt.components,
                self.gl_type,
                self.attribute.fmt.normalized,
                self.view.stride,
                self.view.offset,
            )

    def set_divisor(self) -> None:
        self._gl.vertexAttribDivisor(self.attribute.location, self.attribute.fmt.divisor)



class _UniformArray:
    """Wrapper of the GLSL array data inside a Uniform.

    Allows access to get and set items for a more Pythonic implementation.
    Types with a length longer than 1 will be returned as tuples as an inner list would not support individual value
    reassignment. Array data must either be set in full, or by indexing.
    """

    _gl: WebGLRenderingContext
    _uniform: _Uniform
    _gl_type: GLDataType
    _gl_getter: GLFunc
    _gl_setter: GLFunc
    _is_matrix: bool
    _c_array: Array[GLDataType]
    _ptr: CTypesPointer[GLDataType]
    _idx_to_loc: dict[int, int]

    __slots__ = (
        '_c_array',
        '_gl',
        '_gl_getter',
        '_gl_setter',
        '_gl_type',
        '_idx_to_loc',
        '_is_matrix',
        '_ptr',
        '_uniform',
    )

    def __init__(
        self, uniform: _Uniform, gl_getter: GLFunc, gl_setter: GLFunc, gl_type: GLDataType, is_matrix: bool,
    ) -> None:
        self._uniform = uniform
        self._gl_type = gl_type
        self._gl_getter = gl_getter
        self._gl_setter = gl_setter
        self._is_matrix = is_matrix
        self._idx_to_loc = {}  # Array index to uniform location mapping.
        self._gl = pyglet.graphics.api.core.current_context.gl

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
        loc = self._gl.getUniformLocation(self._uniform.program, f"{self._uniform.name}[{index}]")
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
            assert len(value) == self._uniform.length, (
                f"Setting this key requires {self._uniform.length} values, received {len(value)}."
            )
            data = (self._gl_type * self._uniform.length)(*value)
        else:
            data = self._gl_type(value)

        self._update_uniform(data, offset=key)

    def get(self) -> _UniformArray:
        self._gl_getter(self._uniform.program, self._uniform.location, self._ptr)
        return self

    def set(self, values: Sequence) -> None:
        assert len(self._c_array) == len(values), (
            f"Size of data ({len(values)}) does not match size of the uniform: {len(self._c_array)}."
        )

        self._c_array[:] = values
        self._update_uniform(self._ptr)

    def _update_uniform(self, data: Sequence, offset: int = 0) -> None:
        if offset != 0:
            size = 1
        else:
            size = self._uniform.size

        location = self._get_location_for_index(offset)

        self._gl.useProgram(self._uniform.program)
        if self._is_matrix:
            self._gl_setter(location, GL_FALSE, data)
        else:
            self._gl_setter(location, data)

    def __repr__(self) -> str:
        data = [tuple(data) if self._uniform.length > 1 else data for data in self._c_array]
        return f"UniformArray(uniform={self._uniform}, data={data})"


_gl_matrices: tuple[int, ...] = (
    gl.GL_FLOAT_MAT2,
    gl.GL_FLOAT_MAT2x3,
    gl.GL_FLOAT_MAT2x4,
    gl.GL_FLOAT_MAT3,
    gl.GL_FLOAT_MAT3x2,
    gl.GL_FLOAT_MAT3x4,
    gl.GL_FLOAT_MAT4,
    gl.GL_FLOAT_MAT4x2,
    gl.GL_FLOAT_MAT4x3,
)


class _Uniform:
    _ctx: OpenGLSurfaceContext | None
    type: int
    size: int
    location: int
    program: int | WebGLProgram
    name: str
    length: int
    get: Callable[[], Array[GLDataType] | GLDataType]
    set: Callable[[float], None] | Callable[[Sequence], None]

    __slots__ = '_ctx', 'count', 'get', 'length', 'location', 'name', 'program', 'set', 'size', 'type'

    def __init__(self, program: int | WebGLProgram, name: str, uniform_type: int, size: int, location: int) -> None:
        self._ctx = pyglet.graphics.api.core.current_context
        self.name = name
        self.type = uniform_type
        self.size = size
        self.location = location
        self.program = program

        gl_type, gl_setter, length = self._ctx._uniform_setters[uniform_type]
        gl_getter = self._ctx.gl.getUniform

        # Argument length of data
        self.length = length

        is_matrix = uniform_type in _gl_matrices

        # If it's an array, use the wrapper object.
        if size > 1:
            array = _UniformArray(self, gl_getter, gl_setter, gl_type, is_matrix)
            self.get = array.get
            self.set = array.set
        else:
            c_array: Array[GLDataType] = (gl_type * length)()
            ptr = cast(c_array, POINTER(gl_type))

            self.get = self._create_getter_func(program, location, gl_getter, length)
            self.set = self._create_setter_func(
                self._ctx.gl, program, location, gl_setter, c_array, length, ptr, is_matrix,
            )

    @staticmethod
    def _create_getter_func(
        program_id: int | WebGLRenderingContext,
        location: int,
        gl_getter: GLFunc,
        length: int,
    ) -> Callable[[], Array[GLDataType] | GLDataType]:
        """Factory function for creating simplified Uniform getters."""
        def getter_func() -> GLDataType:
            return gl_getter(program_id, location)

        return getter_func

    @staticmethod
    def _create_setter_func(
        gl_ctx: WebGLRenderingContext,
        program_id: int | WebGLProgram,
        location: int,
        gl_setter: GLFunc,
        c_array: Array[GLDataType],
        length: int,
        ptr: CTypesPointer[GLDataType],
        is_matrix: bool,
    ) -> Callable[[float], None]:
        """Factory function for creating simplified Uniform setters."""
        if is_matrix:

            def setter_func(value: float) -> None:
                gl_ctx.useProgram(program_id)
                gl_setter(location, GL_FALSE, value)
        elif length == 1:

            def setter_func(value: float) -> None:
                gl_ctx.useProgram(program_id)
                gl_setter(location, value)
        elif length > 1:

            def setter_func(values: float) -> None:
                gl_ctx.useProgram(program_id)
                gl_setter(location, values)
        else:
            msg = "Uniform type not yet supported."
            raise ShaderException(msg)

        return setter_func

    def __repr__(self) -> str:
        return f"Uniform(type={self.type}, size={self.size}, location={self.location}, length={self.length})"


def get_maximum_binding_count() -> int:
    """The maximum binding value that can be used for this hardware."""
    return gl.glGetParameter(gl.GL_MAX_UNIFORM_BUFFER_BINDINGS)


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
        self._max_binding_count = 5  # get_maximum_binding_count()
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


def get_std140_size_and_alignment(gl_type):
    """Returns (size, alignment) for a given WebGL uniform type."""
    std140_layout = {
        c_float: (4, 4),
        c_int: (4, 4),
        c_uint: (4, 4),
        gl.FLOAT_VEC2: (8, 8),
        gl.FLOAT_VEC3: (12, 16),  # Vec3 is padded to 16
        gl.FLOAT_VEC4: (16, 16),
        gl.INT_VEC2: (8, 8),
        gl.INT_VEC3: (12, 16),
        gl.INT_VEC4: (16, 16),
        gl.UNSIGNED_INT_VEC2: (8, 8),
        gl.UNSIGNED_INT_VEC3: (12, 16),
        gl.UNSIGNED_INT_VEC4: (16, 16),
        gl.FLOAT_MAT2: (32, 16),  # 2 * vec4
        gl.FLOAT_MAT3: (48, 16),  # 3 * vec4
        gl.FLOAT_MAT4: (64, 16),  # 4 * vec4
    }
    return std140_layout.get(gl_type, (0, 0))


def compute_std140_offsets(uniforms):
    """Manually computes std140-compliant offsets for uniforms in a UBO."""
    offset = 0
    offsets = {}

    for name, c_type, length, size in uniforms.values():
        type_size = sizeof(c_type * length)
        align_size = min(16, type_size)  # Align to std140

        # Align offset
        if offset % align_size != 0:
            offset += align_size - (offset % align_size)

        # Store computed offset
        offsets[name] = offset
        offset += type_size * size  # Account for array sizes

    return offsets


class UniformBlock:  # noqa: D101
    ctx: OpenGLSurfaceContext | None
    program: CallableProxyType[Callable[..., Any] | Any] | Any
    name: str
    index: int
    size: int
    binding: int
    uniforms: dict[int, tuple[str, GLDataType, int, int]]
    view_cls: type[Structure] | None
    __slots__ = 'binding', 'ctx', 'index', 'name', 'program', 'size', 'uniform_count', 'uniforms', 'view_cls'

    def __init__(
        self,
        program: ShaderProgram,
        name: str,
        index: int,
        size: int,
        binding: int,
        uniforms: dict[int, tuple[str, GLDataType, int, int]],
        uniform_count: int,
    ) -> None:
        """Initialize a uniform block for a ShaderProgram."""
        self.ctx = pyglet.graphics.api.core.current_context
        assert self.ctx
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
        self.ctx.gl.bindBufferBase(GL_UNIFORM_BUFFER, self.binding, ubo.buffer.id)

    def create_ubo(self) -> UniformBufferObject:
        """Create a new UniformBufferObject from this uniform block."""
        return UniformBufferObject(self.ctx, self.view_cls, self.size, self.binding)

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
        self.ctx.gl.uniformBlockBinding(self.program.id, self.index, self.binding)

    def _introspect_uniforms(self) -> type[Structure]:
        """Introspect the block's structure and return a ctypes struct for manipulating the uniform block's members."""
        p_id = self.program.id
        index = self.index

        active_count = self.uniform_count

        # Query the uniform index order and each uniform's offset:
        # indices = gl.glGetActiveUniformBlockiv(p_id, index, gl.GL_UNIFORM_BLOCK_ACTIVE_UNIFORM_INDICES, indices_ptr)
        # offsets = gl.glGetActiveUniformsiv(p_id, active_count, indices, gl.GL_UNIFORM_OFFSET, offsets_ptr)

        # Offsets may be returned in non-ascending order, sort them with the corresponding index:
        # _oi = sorted(zip(offsets, indices), key=lambda x: x[0])
        # offsets = [x[0] for x in _oi] + [self.size]
        # indices = (gl.GLuint * active_count)(*(x[1] for x in _oi))

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

        rep_func = lambda s: str(dict(s._fields_))

        def build_ctypes_struct(name, uniform_offsets):
            """Dynamically constructs a ctypes structure for UBO representation."""
            fields = []
            prev_offset = 0

            for uniform_name, offset in sorted(uniform_offsets.items(), key=lambda x: x[1]):
                parts = uniform_name.split(".")
                for uniform in self.uniforms.values():
                    if uniform[0] == uniform_name:
                        _, base_ctype, length, size = uniform
                        break

                if size > 1:
                    c_type *= (base_ctype * length) * size  # Make it an array
                else:
                    c_type = base_ctype * length

                # Handle padding for std140 alignment
                padding = offset - prev_offset
                if padding > 0:
                    fields.append((f'_padding{prev_offset}', c_byte * padding))

                fields.append((uniform_name, c_type))
                prev_offset = offset + sizeof(c_type)

            return type(name, (Structure,), {"_fields_": fields, "__repr__": rep_func})

        uniform_offsets = compute_std140_offsets(self.uniforms)

        # Custom ctypes Structure for Uniform access:
        return build_ctypes_struct('View', uniform_offsets)

    def _actual_binding_point(self) -> int:
        """Queries OpenGL to find what the bind point currently is."""
        return self.ctx.gl.getActiveUniformBlockParameter(self.program.id, self.index, gl.GL_UNIFORM_BLOCK_BINDING)

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(program={self.program.id}, location={self.index}, size={self.size}, "
            f"binding={self.binding})"
        )


class UniformBufferObject(UniformBufferObjectBase):
    buffer: BufferObject
    view: Structure
    _view_ptr: CTypesPointer[Structure]
    binding: int

    __slots__ = '_view_ptr', 'binding', 'buffer', 'view'

    def __init__(self, context: OpenGLSurfaceContext, view_class: type[Structure], buffer_size: int, binding: int) -> None:
        """Initialize the Uniform Buffer Object with the specified Structure."""
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


def _get_number(gl_ctx: WebGLRenderingContext, program_id: WebGLProgram, variable_type: int) -> int:
    """Get the number of active variables of the passed GL type."""
    return gl_ctx.getProgramParameter(program_id, variable_type)


def _introspect_attributes(program_id: WebGLProgram) -> dict[str, Attribute]:
    """Introspect a Program's Attributes, and return a dict of accessors."""
    _gl = pyglet.graphics.api.core.current_context.gl
    attributes = {}

    if not _gl.getProgramParameter(program_id, gl.GL_LINK_STATUS):
        print("Shader program not linked!")
        return {}

    count = _get_number(_gl, program_id, gl.GL_ACTIVE_ATTRIBUTES)
    for index in range(count):
        idx_attribs = _gl.getActiveAttrib(program_id, index)
        if not idx_attribs:
            raise ShaderException(f"Attribute Index {index} not found in Program.")

        a_name, a_type, a_size = idx_attribs.name, idx_attribs.type, idx_attribs.size
        loc = _gl.getAttribLocation(program_id, a_name)
        if loc == -1:  # not a user defined attribute
            continue
        count, fmt = _attribute_types[a_type]
        attributes[a_name] = Attribute(a_name, loc, count, fmt)

    if _debug_api_shaders:
        for attribute in attributes.values():
            print(f" Found attribute: {attribute}")

    return attributes


def _link_program(gl: WebGLRenderingContext, *shaders: Shader) -> int:
    """Link one or more Shaders into a ShaderProgram.

    Returns:
        The ID assigned to the linked ShaderProgram.
    """
    program_id = gl.createProgram()
    for shader in shaders:
        gl.attachShader(program_id, shader.id)
    gl.linkProgram(program_id)

    # Check the link status of program
    status = gl.getProgramParameter(program_id, GL_LINK_STATUS)
    if not status:
        length = gl.getProgramParameter(program_id, GL_INFO_LOG_LENGTH)
        log = c_buffer(length.value)
        gl.getProgramInfoLog(program_id, len(log), None, log)
        msg = f"Error linking shader program:\n{log.value.decode()}"
        raise ShaderException(msg)

    # Shader objects no longer needed
    for shader in shaders:
        gl.detachShader(program_id, shader.id)

    return program_id


def _query_uniform(gl_ctx, program_id: WebGLProgram, index: int) -> tuple[str, int, int]:
    """Query the name, type, and size of a Uniform by index."""
    try:
        info = gl_ctx.getActiveUniform(program_id, index)
        return info.name, info.type, info.size

    except GLException as exc:
        raise ShaderException from exc


def _introspect_uniforms(gl_ctx: WebGLRenderingContext, program_id: WebGLProgram) -> dict[str, _Uniform]:
    """Introspect a Program's uniforms, and return a dict of accessors."""
    uniforms = {}

    for index in range(_get_number(gl_ctx, program_id, gl.GL_ACTIVE_UNIFORMS)):
        u_name, u_type, u_size = _query_uniform(gl_ctx, program_id, index)

        # Multidimensional arrays cannot be fully inspected via OpenGL calls and compile errors with 3.3.
        array_count = u_name.count("[0]")
        if array_count > 1 and u_name.count("[0][0]") != 0:
            msg = "Multidimensional arrays are not currently supported."
            raise ShaderException(msg)

        loc = gl_ctx.getUniformLocation(program_id, u_name)
        if not loc or loc == -1:  # Skip uniforms that may be inside a Uniform Block
            continue

        # Strip [0] from array name for a more user-friendly name.
        if array_count != 0:
            u_name = u_name.strip('[0]')

        assert u_name not in uniforms, f"{u_name} exists twice in the shader. Possible name clash with an array."
        uniforms[u_name] = _Uniform(program_id, u_name, u_type, u_size, loc)

    if _debug_api_shaders:
        for uniform in uniforms.values():
            print(f" Found uniform: {uniform}")

    return uniforms


def _introspect_uniform_blocks(
    ctx: OpenGLSurfaceContext, program: ShaderProgram | ComputeShaderProgram,
) -> dict[str, UniformBlock]:
    uniform_blocks = {}
    gl_ctx: WebGL2RenderingContext = ctx.gl
    program_id: WebGLProgram = program.id

    for index in range(_get_number(gl_ctx, program_id, gl.GL_ACTIVE_UNIFORM_BLOCKS)):
        name = gl_ctx.getActiveUniformBlockName(program_id, index)
        if not name:
            msg = f"Unable to query UniformBlock name at index: {index}"
            raise ShaderException(msg)

        # num_active = gl.glGetActiveUniformBlockParameter(program_id, index, gl.GL_UNIFORM_BLOCK_ACTIVE_UNIFORMS)
        block_data_size = gl_ctx.getActiveUniformBlockParameter(program_id, index, gl.GL_UNIFORM_BLOCK_DATA_SIZE)
        binding = gl_ctx.getActiveUniformBlockParameter(program_id, index, gl.GL_UNIFORM_BLOCK_BINDING)
        indices = gl_ctx.getActiveUniformBlockParameter(program_id, index, gl.GL_UNIFORM_BLOCK_ACTIVE_UNIFORM_INDICES)

        uniforms: dict[int, tuple[str, GLDataType, int, int]] = {}

        if not hasattr(pyglet.graphics.api.core.current_context, "ubo_manager"):
            pyglet.graphics.api.core.current_context.ubo_manager = _UBOBindingManager()

        manager = pyglet.graphics.api.core.current_context.ubo_manager

        for block_uniform_index in indices:
            uniform_name, u_type, u_size = _query_uniform(gl_ctx, program_id, block_uniform_index)

            # Remove block name.
            if uniform_name.startswith(f"{name}."):
                uniform_name = uniform_name[len(name) + 1 :]  # Strip 'block_name.' part

            if uniform_name.count("[0][0]") > 0:
                msg = "Multidimensional arrays are not currently supported."
                raise ShaderException(msg)

            gl_type, _, length = ctx._uniform_setters[u_type]
            uniforms[block_uniform_index] = (uniform_name, gl_type, length, u_size)

        binding_index = binding
        if pyglet.options.shader_bind_management:
            # If no binding is specified in GLSL, then assign it internally.
            if binding == 0:
                binding_index = manager.get_binding(program, name)

                # This might cause an error if index > GL_MAX_UNIFORM_BUFFER_BINDINGS, but surely no
                # one would be crazy enough to use more than 36 uniform blocks, right?
                gl_ctx.uniformBlockBinding(program_id, index, binding_index)
            else:
                # If a binding was manually set in GLSL, just check if the values collide to warn the user.
                _block_name = manager.get_name(binding)
                if _block_name and _block_name != name:
                    msg = (
                        f"{program} explicitly set '{name}' to {binding} in the shader. '{_block_name}' has "
                        f"been overridden."
                    )
                    warnings.warn(msg)
                manager.add_explicit_binding(program, name, binding)

        uniform_blocks[name] = UniformBlock(
            program, name, index, block_data_size, binding_index, uniforms, len(indices),
        )

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

        self._lines[0] = "#version 300 es"
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
        self._gl = self._context.gl
        self._id = None
        self.type = shader_type

        shader_gl_type = _shader_types[shader_type]
        source_string = self.get_string_class()(source_string, shader_gl_type).validate()
        # shader_source_utf8 = source_string.encode("utf8")
        # source_buffer_pointer = cast(c_char_p(shader_source_utf8), POINTER(c_char))
        # source_length = c_int(len(shader_source_utf8))

        shader_id = self._gl.createShader(shader_gl_type)
        self._id = shader_id
        self._gl.shaderSource(shader_id, source_string)
        self._gl.compileShader(shader_id)

        status = self._gl.getShaderParameter(shader_id, gl.GL_COMPILE_STATUS)

        if status != GL_TRUE:
            source = source_string
            source_lines = "{0}".format(
                "\n".join(f"{str(i + 1).zfill(3)}: {line} " for i, line in enumerate(source.split("\n"))),
            )

            msg = (
                f"\n------------------------------------------------------------\n"
                f"{source_lines}"
                f"\n------------------------------------------------------------\n"
                f"Shader compilation failed. Please review the error on the specified line.\n"
                f"{self._get_shader_log(shader_id)}"
            )

            raise ShaderException(msg)

        if _debug_api_shaders:
            print(self._get_shader_log(shader_id))

    @staticmethod
    def get_string_class() -> type[GLShaderSource]:
        return GLShaderSource

    @classmethod
    def supported_shaders(cls) -> tuple[ShaderType, ...]:
        return 'vertex', 'fragment', 'compute', 'geometry', 'tesscontrol', 'tessevaluation'

    @property
    def id(self) -> int | WebGLProgram:
        return self._id

    def _get_shader_log(self, shader_id: int) -> str:
        info_log = self._gl.getShaderInfoLog(shader_id)
        if info_log:
            return f"OpenGL returned the following message when compiling the '{self.type}' shader: \n{info_log}"

        return f"{self.type.capitalize()} Shader '{shader_id}' compiled successfully."

    def delete(self) -> None:
        """Deletes the shader.

        This cannot be undone.
        """
        self._gl.deleteShader(self._id)
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

    _id: int | WebGLProgram | None
    _context: OpenGLSurfaceContext | None
    _uniforms: dict[str, _Uniform]
    _uniform_blocks: dict[str, UniformBlock]

    __slots__ = '_attributes', '_context', '_id', '_uniform_blocks', '_uniforms'

    def __init__(self, *shaders: Shader) -> None:
        """Initialize the ShaderProgram using at least two Shader instances."""
        super().__init__(*shaders)
        self._context = pyglet.graphics.api.core.current_context
        self._gl = self._context.gl
        self._id = _link_program(self._gl, *shaders)

        if _debug_api_shaders:
            """Query a ShaderProgram link logs."""
            result = self._gl.getProgramInfoLog(self._id)
            if result:
                print(f"OpenGL returned the following message when linking the program: \n{result}")
            else:
                js.console.log(f"Program '{self._id}' linked successfully.")

        # Query if Direct State Access is available:
        self.use()

        self._attributes = _introspect_attributes(self._id)
        self._uniforms = _introspect_uniforms(self._gl, self._id)
        self._uniform_blocks = self._get_uniform_blocks()
        self.stop()

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
        self._gl.useProgram(self._id)

    def stop(self) -> None:
        self._gl.useProgram(None)

    __enter__ = use
    bind = use
    unbind = stop

    def __exit__(self, *_) -> None:  # noqa: ANN002
        self._gl.useProgram(None)

    def delete(self) -> None:
        self._gl.deleteProgram(self._id)
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
            msg = (
                f"A Uniform with the name `{key}` was not found.\n"
                f"The spelling may be incorrect or, if not in use, it "
                f"may have been optimized out by the OpenGL driver."
            )
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
            current_attrib = self._attributes[name]
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

        if _debug_api_shaders:
            if missing_data := [key for key in attributes if key not in data]:
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


    def vertex_list(
        self, count: int, mode: GeometryMode, batch: Batch = None, group: Group = None, **data: Any,
    ) -> VertexList:
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

    def vertex_list_instanced(
        self,
        count: int,
        mode: GeometryMode,
        instance_attributes: Sequence[str],
        batch: Batch | None = None,
        group: Group | None = None,
        **data: Any,
    ) -> VertexList:
        assert len(instance_attributes) > 0, "You must provide at least one attribute name to be instanced."
        return self._vertex_list_create(count, mode, None, instance_attributes, batch=batch, group=group, **data)

    def vertex_list_indexed(
        self,
        count: int,
        mode: GeometryMode,
        indices: Sequence[int],
        batch: Batch | None = None,
        group: Group | None = None,
        **data: Any,
    ) -> IndexedVertexList:
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

    def vertex_list_instanced_indexed(
        self,
        count: int,
        mode: GeometryMode,
        indices: Sequence[int],
        instance_attributes: Sequence[str],
        batch: Batch | None = None,
        group: Group | None = None,
        **data: Any,
    ) -> IndexedVertexList:
        assert len(instance_attributes) > 0, "You must provide at least one attribute name to be instanced."
        return self._vertex_list_create(count, mode, indices, instance_attributes, batch=batch, group=group, **data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"


class ComputeShaderProgram:
    """OpenGL Compute Shader Program."""

    def __init__(self, source: str) -> None:
        """Create an OpenGL ComputeShaderProgram from source."""
        raise ShaderException("Compute Shaders are not supported in WebGL.")
