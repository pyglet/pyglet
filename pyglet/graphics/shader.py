from __future__ import annotations

import abc
import ctypes
import re
import sys
import warnings
import weakref
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Literal, Sequence, Any, TYPE_CHECKING, Callable, Protocol, overload

import pyglet
from pyglet.enums import GraphicsAPI

if TYPE_CHECKING:
    from pyglet.graphics.buffer import UniformBufferObject
    from pyglet.customtypes import DataTypes, CType
    from pyglet.graphics.vertexdomain import IndexedVertexList, VertexList, InstanceIndexedVertexList, InstanceVertexList
    from pyglet.graphics import Batch, Group
    from pyglet.enums import GeometryMode
    from _weakref import CallableProxyType


class ShaderException(BaseException):
    pass

ShaderType = Literal['vertex', 'fragment', 'geometry', 'compute', 'tesscontrol', 'tessevaluation']

# NormalizedType = Literal[
#     '',  # no normalization.
#     'n',  # Signed normalization, (-1, 1)  # Not sure if OpenGL has this.
#     'N',  # Unsigned normalization. (0, 1)
# ]
GLSLDataTypes = Literal[
    'mat4',  # 4x4 matrix (16 floats)
    'vec4',  # vec4 (4 floats)
    'vec3',  # vec3 (3 floats)
    'vec2',  # vec2 (2 floats)
    'float',  # single float
    'int',  # single int
    'uint',  # single unsigned int
    'bool',  # seems to be c_uint in glsl.
]

UniformDataType = str
UniformName = str

class UniformBlockDesc(Protocol):
    stages: tuple[ShaderType]
    bind_num: int  # binding number in descriptor set
    set_num: int  # descriptor set number
    uniforms: tuple[tuple[UniformDataType, UniformName]]

@dataclass
class PushConstants:
    stages: tuple[ShaderType]
    constants: list[tuple[str, GLSLDataTypes]]  # Name, GLSL Type


@dataclass
class Sampler:
    name: str
    desc_set: int
    binding: int
    count: int = 1
    stages: Sequence[ShaderType] = ("fragment",)


class _AbstractShaderProgram(ABC):
    _id: int | None
    _attributes: dict[str, Attribute]
    _uniforms: dict[str, Any]
    _uniform_blocks: dict[str, UniformBlock]
    _samplers: dict[str, Sampler]

    def __init__(self, *shaders: Shader) -> None:
        self._id = None

        assert shaders, "At least one Shader object is required."

        # Attribute description
        self._attributes = {}

        # Uniform description
        self._uniforms = {}

        # Uniform Block description
        self._uniform_blocks = {}

        # Sampler descriptions
        self._samplers = {}

    @property
    def id(self) -> int | None:
        return self._id

    @property
    def is_defined(self) -> bool:
        """Determine if the ShaderProgram was defined and is ready for use."""
        # Just use the attributes are filled in to determine if it's ready.
        return bool(self._attributes)

    def set_attributes(self, *attributes: Attribute) -> None:
        """Define the attributes of the vertex shader.

        On some backends like OpenGL, this is unnecessary unless you want to redefine the buffers.
        """
        for attrib in attributes:
            self._attributes[attrib.fmt.name] = attrib

    def set_uniform_blocks(self, *uniform_blocks: UniformBlockDesc) -> None:
        for ub in uniform_blocks:
            self._uniform_blocks[ub.__class__.__name__] = self.get_uniform_block_cls()

    def set_samplers(self, *samplers: Sampler) -> None:
        for sampler in samplers:
            self._samplers[sampler.name] = sampler

    def get_uniform_block_cls(self) -> type[UniformBlock]:
        return UniformBlock

    @property
    def attributes(self) -> dict[str, Any]:
        """Attribute metadata dictionary.

        This property returns a dictionary containing metadata of all
        Attributes that were introspected in this ShaderProgram. Modifying
        this dictionary has no effect.
        """
        return self._attributes.copy()

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

    @property
    def samplers(self) -> dict[str, Sampler]:
        """A dictionary of introspected samplers.

        This property returns a dictionary of
        :py:class:`~pyglet.graphics.shader.Sampler` instances keyed by sampler name.
        """
        return self._samplers

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
        """Bind this shader program for rendering commands."""
        raise NotImplementedError

    def bind(self) -> None:
        """Alias for :meth:`use`."""
        self.use()

    def stop(self) -> None:
        """Unbind this shader program from rendering commands."""
        raise NotImplementedError

    def unbind(self) -> None:
        """Alias for :meth:`stop`."""
        self.stop()

    def delete(self) -> None:
        """Delete this shader program and release backend resources."""
        raise NotImplementedError

    def __enter__(self) -> None:
        self.use()

    def __exit__(self, *_) -> None:  # noqa: ANN002
        self.stop()

    @overload
    def _vertex_list_create(self, count: int, mode: GeometryMode, indices: None = None,
                            instances: None = None, batch: Batch | None = None, group: Group | None = None,
                            **data: Any) -> VertexList:
        ...

    @overload
    def _vertex_list_create(self, count: int, mode: GeometryMode, indices: Sequence[int] = ...,
                            instances: None = None, batch: Batch | None = None, group: Group | None = None,
                            **data: Any) -> IndexedVertexList:
        ...

    @overload
    def _vertex_list_create(self, count: int, mode: GeometryMode, indices: None = None,
                            instances: dict[str, int] = ..., batch: Batch | None = None, group: Group | None = None,
                            **data: Any) -> InstanceVertexList:
        ...

    @overload
    def _vertex_list_create(self, count: int, mode: GeometryMode, indices: Sequence[int] = ...,
                            instances: dict[str, int] = ..., batch: Batch | None = None, group: Group | None = None,
                            **data: Any) -> InstanceIndexedVertexList:
        ...

    def _vertex_list_create(self, count: int, mode: GeometryMode, indices: Sequence[int] | None = None,
                            instances: dict[str, int] | None = None, batch: Batch | None = None, group: Group | None = None,
                            **data: Any) -> VertexList | InstanceVertexList | IndexedVertexList | InstanceIndexedVertexList:
        raise NotImplementedError

    def vertex_list(self, count: int, mode: GeometryMode, batch: Batch | None = None, group: Group | None = None,
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

    def vertex_list_instanced(self, count: int, mode: GeometryMode, instance_attributes: dict[str, int],
                              batch: Batch | None = None, group: Group | None = None, **data: Any) -> InstanceVertexList:
        assert len(instance_attributes) > 0, "You must provide at least one attribute name to be instanced."
        return self._vertex_list_create(count, mode, None, instance_attributes, batch=batch, group=group, **data)

    def vertex_list_indexed(self, count: int, mode: GeometryMode, indices: Sequence[int], batch: Batch | None = None,
                            group: Group | None = None, **data: Any) -> IndexedVertexList:
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
                                      instance_attributes: dict[str, int], batch: Batch | None = None, group: Group | None = None,
                                      **data: Any) -> InstanceIndexedVertexList:
        assert len(instance_attributes) > 0, "You must provide at least one attribute name to be instanced."
        return self._vertex_list_create(count, mode, indices, instance_attributes, batch=batch, group=group, **data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"


class ShaderProgram(_AbstractShaderProgram):
    """Backend-agnostic shader program container.

    Concrete backends are responsible for compiling/linking shaders,
    introspecting attributes and uniforms, and providing API-specific
    program state management.
    """

    def __init__(self, *shaders: _AbstractShader) -> None:
        """Initialize a shader program from one or more Shader objects.

        Args:
            shaders:
                One or more :py:class:`~pyglet.graphics.shader.Shader`
                instances to be linked into a program by the active backend.
                At least one shader is required.
        """
        super().__init__(*shaders)


class ComputeShaderProgram:
    """Backend-agnostic compute shader program container."""

    def __init__(self, source: str) -> None:
        msg = f"{self.__class__.__name__} is backend-specific and must be provided by the active backend."
        raise NotImplementedError(msg)


class ShaderSource(abc.ABC):
    """String source of shader used during load of a Shader instance."""

    @abstractmethod
    def validate(self) -> str:
        """Return the validated shader source."""


class _AbstractShader(abc.ABC):
    """Graphics shader.

    Shader objects may be compiled on instantiation if OpenGL or already compiled in Vulkan.
    You can reuse a Shader object in multiple ShaderPrograms.
    """
    _src_str: str
    type: ShaderType

    def __init__(self, source_string: str, shader_type: ShaderType) -> None:
        """Initialize a shader type."""
        self._src_str = source_string
        self.type = shader_type

        available_shaders = self.supported_shaders()
        if shader_type not in available_shaders:
            msg = (
                f"Shader type '{shader_type}' is not supported by this shader class."
                f"Supported types are: {available_shaders}"
            )
            raise ShaderException(msg)

    @classmethod
    @abstractmethod
    def supported_shaders(cls: type[Shader]) -> tuple[ShaderType, ...]:
        """Return the supported shader types for this shader class."""

    @staticmethod
    @abstractmethod
    def get_string_class() -> type[ShaderSource]:
        """Return the proper ShaderSource class used to validate the shader."""

class Shader(_AbstractShader):
    """Graphics shader.

    Shader objects may be compiled on instantiation if OpenGL or already compiled in Vulkan.
    You can reuse a Shader object in multiple ShaderPrograms.
    """
    _src_str: str
    type: ShaderType

    def __init__(self, source_string: str, shader_type: ShaderType) -> None:
        """Initialize a shader type."""
        super().__init__(source_string, shader_type)

    @classmethod
    def supported_shaders(cls: type[_AbstractShader]) -> tuple[ShaderType, ...]:
        """Return the supported shader types for this shader class."""
        raise NotImplementedError

    @staticmethod
    def get_string_class() -> type[ShaderSource]:
        """Return the proper ShaderSource class used to validate the shader."""
        raise NotImplementedError

DataTypeTuple = ('?', 'f', 'i', 'I', 'h',  'H', 'b', 'B', 'q','Q')

_data_type_to_ctype = {
    '?': ctypes.c_bool,         # bool
    'b': ctypes.c_byte,         # signed byte
    'B': ctypes.c_ubyte,        # unsigned byte
    'h': ctypes.c_short,        # signed short
    'H': ctypes.c_ushort,       # unsigned short
    'i': ctypes.c_int,          # signed int
    'I': ctypes.c_uint,         # unsigned int
    'f': ctypes.c_float,        # float
    'd': ctypes.c_double,       # double
    'q': ctypes.c_longlong,     # signed long long
    'Q': ctypes.c_ulonglong,    # unsigned long long
}

@dataclass(frozen=True)
class AttributeFormat:
    """A format describing the properties of an Attribute."""
    name: str
    components: int  # for example: 4 for vec4
    data_type: DataTypes
    normalized: bool
    divisor: int            # 0 = per-vertex, 1> = per-instance

    @property
    def is_instanced(self) -> bool:
        return self.divisor != 0

@dataclass(frozen=True)
class AttributeView:
    """Describes a view of the attribute at its bound buffer."""
    offset: int  # Offset start of element to this attribute
    stride: int  # Size from one element to the next


class Attribute:
    """Describes an attribute in a shader."""
    fmt: AttributeFormat
    element_size: int
    c_type: CType
    location: int

    def __init__(self, name: str, location: int, components: int, data_type: DataTypes, normalize: bool = False,
                 divisor: int = 0) -> None:
        """Create the attribute accessor.

        Args:
            name:
                Name of the vertex attribute.
            location:
                Location (index) of the vertex attribute.
            components:
                Number of components in the attribute.
            data_type:
                Data type intended for use with the attribute.
            normalize:
                True if OpenGL should normalize the values
            divisor:
                The divisor value if this is an instanced attribute.

        """
        self.fmt = AttributeFormat(name, components, data_type, normalize, divisor)
        self.location = location

        self.c_type = _data_type_to_ctype[self.fmt.data_type]
        self.element_size = ctypes.sizeof(self.c_type)

    def set_data_type(self, data_type: DataTypes, normalize: bool) -> None:
        """Set datatype to a new format and normalization.

        Must be done before this attribute is used, or may cause unexpected behavior.
        """
        self.fmt = AttributeFormat(self.fmt.name, self.fmt.components, data_type, normalize, self.fmt.divisor)
        self.c_type = _data_type_to_ctype[self.fmt.data_type]
        self.element_size = ctypes.sizeof(self.c_type)

    def set_divisor(self, divisor: int) -> None:
        self.fmt = AttributeFormat(self.fmt.name, self.fmt.components, self.fmt.data_type, self.fmt.normalized, divisor)

    def __repr__(self) -> str:
        return f"Attribute(location={self.location}, fmt={self.fmt}')"


class GraphicsAttribute:
    """A combination of format and view to give the overall attribute information."""
    def __init__(self, attribute: Attribute, view: AttributeView) -> None:
        self.attribute = attribute
        self.view = view

    def enable(self) -> None:
        """Enable the attribute."""
        raise NotImplementedError

    def disable(self) -> None:
        """Disable the attribute."""
        raise NotImplementedError

    def set_pointer(self) -> None:
        """Setup this attribute to point to the currently bound buffer at the given offset."""
        raise NotImplementedError

    def set_divisor(self) -> None:
        raise NotImplementedError


def _ubo_view_repr(view: ctypes.Structure) -> str:
    names_fields = ", ".join((f"{k}={v.__name__}" for k, v in dict(view._fields_).items()))
    return f"UBOView({names_fields})"


def _build_ctypes_struct(
    name: str,
    struct_dict: dict[str, Any],
    array_sizes: dict[str, int] | None = None,
) -> type[ctypes.Structure]:
    """Build a nested ctypes Structure class from a dictionary of fields."""
    fields = []
    array_sizes = array_sizes or {}

    for field_name, field_type in struct_dict.items():
        if isinstance(field_type, dict):
            element_struct = _build_ctypes_struct(field_name, field_type, array_sizes)
            field_type = element_struct  # noqa: PLW2901
            if field_name in array_sizes and array_sizes[field_name] > 1:
                field_type = element_struct * array_sizes[field_name]  # noqa: PLW2901
        fields.append((field_name, field_type))

    return type(name.title(), (ctypes.Structure,), {"_fields_": fields, "__repr__": _ubo_view_repr})


_array_regex = re.compile(r"(\w+)\[(\d+)\]")


def _build_uniform_struct_from_uniforms(
    name: str,
    uniforms: Sequence[tuple[str, Any, int, int]],
    offsets: Sequence[int],
) -> type[ctypes.Structure]:
    """Build a UBO ctypes structure from ordered uniform tuples and offsets."""
    assert len(offsets) == len(uniforms) + 1, "Offsets must include one trailing end offset."

    array_sizes: dict[str, int] = {}
    dynamic_structs: dict[str, Any] = {}
    p_count = 0

    for i, (u_name, gl_type, length, u_size) in enumerate(uniforms):
        parts = u_name.split(".")

        current_structure = dynamic_structs
        for part_idx, part in enumerate(parts):
            part_name = part
            match = _array_regex.match(part_name)
            if match:  # It's an array.
                arr_name, array_index = match.groups()
                part_name = arr_name

                if part_idx != len(parts) - 1:
                    array_index = int(array_index)

                    # Track array sizes for the current array name.
                    array_sizes[arr_name] = max(array_sizes.get(arr_name, 0), array_index + 1)
                    if array_sizes[arr_name] > 1:
                        break

                    if arr_name not in current_structure:
                        current_structure[arr_name] = {}

                    current_structure = current_structure[arr_name]
                    continue

            if part_idx == len(parts) - 1:
                if u_size > 1:
                    current_structure[part_name] = (gl_type * length) * u_size if length > 1 else gl_type * u_size
                else:
                    current_structure[part_name] = gl_type * length if length > 1 else gl_type

                offset_size = offsets[i + 1] - offsets[i]
                c_type_size = ctypes.sizeof(current_structure[part_name])
                padding = offset_size - c_type_size
                if padding > 0:
                    current_structure[f"_padding{p_count}"] = ctypes.c_byte * padding
                    p_count += 1
            else:
                if part_name not in current_structure:
                    current_structure[part_name] = {}
                current_structure = current_structure[part_name]

    return _build_ctypes_struct(name, dynamic_structs, array_sizes)


class UniformArrayBase:
    """Backend-agnostic base for uniform array wrappers."""

    __slots__ = (
        "_c_array",
        "_gl_getter",
        "_gl_setter",
        "_gl_type",
        "_idx_to_loc",
        "_is_matrix",
        "_ptr",
        "_uniform",
    )

    def __init__(self, uniform: Any, gl_getter: Callable, gl_setter: Callable, gl_type: Any, is_matrix: bool) -> None:
        self._uniform = uniform
        self._gl_type = gl_type
        self._gl_getter = gl_getter
        self._gl_setter = gl_setter
        self._is_matrix = is_matrix
        self._idx_to_loc = {}  # Array index to uniform location mapping.

        if self._uniform.length > 1:
            self._c_array = (gl_type * self._uniform.length * self._uniform.size)()
        else:
            self._c_array = (gl_type * self._uniform.size)()

        self._ptr = ctypes.cast(self._c_array, ctypes.POINTER(gl_type))

    def _get_location_for_index(self, index: int) -> int:
        raise NotImplementedError

    def _apply_uniform_update(self, location: int, size: int, data: Sequence) -> None:
        raise NotImplementedError

    def _get_array_loc(self, index: int) -> int:
        try:
            return self._idx_to_loc[index]
        except KeyError:
            loc = self._idx_to_loc[index] = self._get_location_for_index(index)

        if loc == -1:
            msg = (
                f"{self._uniform.name}[{index}] not found.\n"
                "This may have been optimized out by the OpenGL driver if unused."
            )
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
            msg = (
                f"{self._uniform.name}[{key}] not found. "
                "This may have been optimized out by the OpenGL driver if unused."
            )
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

    def get(self) -> UniformArrayBase:
        self._gl_getter(self._uniform.program, self._uniform.location, self._ptr)
        return self

    def set(self, values: Sequence) -> None:
        assert len(self._c_array) == len(values), (
            f"Size of data ({len(values)}) does not match size of the uniform: {len(self._c_array)}."
        )

        self._c_array[:] = values
        self._update_uniform(self._ptr)

    def _update_uniform(self, data: Sequence, offset: int = 0) -> None:
        size = 1 if offset != 0 else self._uniform.size
        location = self._get_location_for_index(offset)
        self._apply_uniform_update(location, size, data)

    def __repr__(self) -> str:
        data = [tuple(data) if self._uniform.length > 1 else data for data in self._c_array]
        return f"UniformArray(uniform={self._uniform}, data={data})"


class UniformBase:
    """Backend-agnostic base for uniform wrappers."""

    __slots__ = "count", "get", "length", "location", "name", "program", "set", "size", "type"

    def __init__(
        self,
        *,
        name: str,
        uniform_type: int,
        size: int,
        location: Any,
        program: Any,
        matrix_types: tuple[int, ...],
        array_wrapper_factory: Callable[[Any, Callable, Callable, Any, bool], UniformArrayBase],
    ) -> None:
        self.name = name
        self.type = uniform_type
        self.size = size
        self.location = location
        self.program = program

        gl_type, gl_getter, gl_setter, length = self._get_uniform_accessors(uniform_type)
        self.length = length
        is_matrix = uniform_type in matrix_types

        if size > 1:
            array = array_wrapper_factory(self, gl_getter, gl_setter, gl_type, is_matrix)
            self.get = array.get
            self.set = array.set
            return

        self.get, self.set = self._create_scalar_get_set(
            program=program,
            location=location,
            gl_getter=gl_getter,
            gl_setter=gl_setter,
            gl_type=gl_type,
            length=length,
            is_matrix=is_matrix,
        )

    def _get_uniform_accessors(self, uniform_type: int) -> tuple[Any, Callable, Callable, int]:
        raise NotImplementedError

    def _create_scalar_get_set(
        self,
        *,
        program: Any,
        location: Any,
        gl_getter: Callable,
        gl_setter: Callable,
        gl_type: Any,
        length: int,
        is_matrix: bool,
    ) -> tuple[Callable, Callable]:
        raise NotImplementedError


class UBOBindingManager:
    """Manages global Uniform Block binding assignments."""

    _in_use: set[int]
    _pool: list[int]
    _max_binding_count: int
    _ubo_names: dict[str, int]
    _ubo_programs: defaultdict[Any, weakref.WeakSet[Any]]

    def __init__(self, max_binding_count: int) -> None:
        self._ubo_programs = defaultdict(weakref.WeakSet)
        # Reserve 'WindowBlock' for 0.
        self._ubo_names = {"WindowBlock": 0}
        self._max_binding_count = max_binding_count
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
        """Retrieve a global Uniform Block binding ID."""
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
            if ubo_name != "WindowBlock" and not self._ubo_programs[ubo_name]:
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


class UniformBlock:
    program: CallableProxyType[Callable[..., Any] | Any] | Any
    name: str
    index: int
    size: int
    binding: int
    uniforms: dict
    view_cls: type[ctypes.Structure]
    __slots__ = 'binding', 'index', 'name', 'program', 'size', 'uniform_count', 'uniforms', 'view_cls'

    def __init__(self, program: ShaderProgram, name: str, index: int, size: int, binding: int,
                 uniforms: dict, uniform_count: int) -> None:
        """Initialize a uniform block for a ShaderProgram."""
        self.program = weakref.proxy(program)
        self.name = name
        self.index = index
        self.size = size
        self.binding = binding
        self.uniforms = uniforms
        self.uniform_count = uniform_count
        self.view_cls = self._create_structure()

    def bind(self, ubo: UniformBufferObject) -> None:
        """Bind the Uniform Buffer Object to the binding point of this Uniform Block."""
        self._bind_buffer_base(self.binding, ubo.buffer.id)

    def create_ubo(self) -> UniformBufferObject:
        """Create a new UniformBufferObject from this uniform block."""
        return self._create_backend_ubo(self.view_cls, self.size, self.binding)

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

        import pyglet
        ctx = pyglet.graphics.api.core.current_context
        assert ctx is not None, "No context available."

        manager = ctx.ubo_manager
        if binding >= manager.max_value:
            msg = f"Binding value exceeds maximum allowed by hardware: {manager.max_value}"
            raise ShaderException(msg)

        existing_name = manager.get_name(binding)
        if existing_name and existing_name != self.name:
            msg = f"Binding: {binding} was in use by {existing_name}, and has been overridden."
            warnings.warn(msg)

        self.binding = binding
        self._set_block_binding()

    def _create_structure(self) -> type[ctypes.Structure]:
        return self._introspect_uniforms()

    @abstractmethod
    def _bind_buffer_base(self, binding: int, buffer_id: int) -> None:
        raise NotImplementedError

    @abstractmethod
    def _create_backend_ubo(
        self,
        view_class: type[ctypes.Structure],
        buffer_size: int,
        binding: int,
    ) -> UniformBufferObject:
        raise NotImplementedError

    @abstractmethod
    def _set_block_binding(self) -> None:
        raise NotImplementedError

    def _introspect_uniforms(self) -> type[ctypes.Structure]:
        """Introspect the block's structure and return a ctypes struct for manipulating the uniform block's members."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(program={self.program.id}, location={self.index}, size={self.size}, "
                f"binding={self.binding})")


def get_default_shader() -> ShaderProgram:
    """A default shader for rendering primitives."""
    raise NotImplementedError

_is_pyglet_doc_run = hasattr(sys, "is_pyglet_doc_run") and sys.is_pyglet_doc_run

if not _is_pyglet_doc_run:
    if pyglet.options.backend in (GraphicsAPI.OPENGL, GraphicsAPI.OPENGL_ES_3):
        from pyglet.graphics.api.gl.shader import (
            GLComputeShaderProgram as ComputeShaderProgram,
            GLShader as Shader,
            GLShaderProgram as ShaderProgram,
        )
        from pyglet.graphics.api.gl.shader import get_default_shader
    elif pyglet.options.backend in (GraphicsAPI.OPENGL_2, GraphicsAPI.OPENGL_ES_2):
        from pyglet.graphics.api.gl2.shader import ComputeShaderProgram, Shader, ShaderProgram
        from pyglet.graphics.api.gl2.shader import get_default_shader
    elif pyglet.options.backend == GraphicsAPI.WEBGL:
        from pyglet.graphics.api.webgl.shader import (
            WebGLComputeShaderProgram as ComputeShaderProgram,
            WebGLShader as Shader,
            WebGLShaderProgram as ShaderProgram,
        )
        from pyglet.graphics.api.webgl.shader import get_default_shader
    elif pyglet.options.backend == GraphicsAPI.VULKAN:
        from pyglet.graphics.api.vulkan.shader import ComputeShaderProgram, Shader, ShaderProgram
    else:
        msg = f"Unsupported backend: {pyglet.options.backend}"
        raise RuntimeError(msg)
