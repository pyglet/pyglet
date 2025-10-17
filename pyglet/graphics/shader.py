from __future__ import annotations

import abc
import ctypes
import weakref
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal, Sequence, Any, TYPE_CHECKING, Callable, Protocol

if TYPE_CHECKING:
    from pyglet.customtypes import DataTypes, CType
    from pyglet.graphics.vertexdomain import IndexedVertexList, VertexList, InstanceIndexedVertexList, InstanceVertexList
    from pyglet.graphics import GeometryMode, Batch, Group
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


class ShaderProgramBase(ABC):
    _attributes: dict[str, Attribute]
    _uniform_blocks: dict[str, UniformBlockBase]
    _samplers: dict[str, Sampler]

    def __init__(self, *shaders: ShaderBase) -> None:
        self._id = None

        assert shaders, "At least one Shader object is required."

        # Attribute description
        self._attributes = {}

        # Uniform Block description
        self._uniform_blocks = {}

    @property
    def id(self):
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
            self._attributes[attrib.name] = attrib

    def set_uniform_blocks(self, *uniform_blocks: UniformBlockDesc) -> None:
        for ub in uniform_blocks:
            self._uniform_blocks[ub.__class__.__name__] = self.get_uniform_block_cls()

    def set_samplers(self, *samplers: Sampler) -> None:
        for sampler in samplers:
            self._samplers[sampler.name] = sampler

    def get_uniform_block_cls(self) -> type[UniformBlockBase]:
        return UniformBlockBase

    @property
    def attributes(self) -> dict[str, Any]:
        """Attribute metadata dictionary.

        This property returns a dictionary containing metadata of all
        Attributes that were introspected in this ShaderProgram. Modifying
        this dictionary has no effect.
        """
        return self._attributes.copy()

    @property
    def uniform_blocks(self) -> dict[str, UniformBlockBase]:
        """A dictionary of introspected UniformBlocks.

        This property returns a dictionary of
        :py:class:`~pyglet.graphics.shader.UniformBlock` instances.
        They can be accessed by name. For example::

            block = my_shader_program.uniform_blocks['WindowBlock']
            ubo = block.create_ubo()

        """
        return self._uniform_blocks

    def _vertex_list_create(self, count: int, mode: GeometryMode, indices: Sequence[int] | None = None,
                            instances: Sequence[str] | None = None, batch: Batch = None, group: Group = None,
                            **data: Any) -> VertexList | InstanceVertexList | IndexedVertexList | InstanceIndexedVertexList:
        raise NotImplementedError

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

    def vertex_list_instanced(self, count: int, mode: GeometryMode, instance_attributes: dict[str, int], batch: Batch = None,
                              group: Group = None, **data: Any) -> InstanceVertexList:
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

    def vertex_list_instanced_indexed(self, count: int, *, mode: GeometryMode, indices: Sequence[int],
                                      instance_attributes: Sequence[str], batch: Batch = None, group: Group = None,
                                      **data: Any) -> InstanceIndexedVertexList:
        assert len(instance_attributes) > 0, "You must provide at least one attribute name to be instanced."
        return self._vertex_list_create(count, mode, indices, instance_attributes, batch=batch, group=group, **data)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id})"

class ShaderSource(abc.ABC):
    """String source of shader used during load of a Shader instance."""

    @abstractmethod
    def validate(self) -> str:
        """Return the validated shader source."""


class ShaderBase(abc.ABC):
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
    def supported_shaders(cls: type[ShaderBase]) -> tuple[ShaderType, ...]:
        """Return the supported shader types for this shader class."""

    @staticmethod
    @abstractmethod
    def get_string_class() -> type[ShaderSource]:
        """Return the proper ShaderSource class used to validate the shader."""

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


class UniformBufferObjectBase:
    @abstractmethod
    def read(self) -> bytes:
        raise NotImplementedError


class UniformBlockBase:
    program: CallableProxyType[Callable[..., Any] | Any] | Any
    name: str
    index: int
    size: int
    binding: int
    uniforms: dict
    view_cls: type[ctypes.Structure] | None
    __slots__ = 'binding', 'index', 'name', 'program', 'size', 'uniform_count', 'uniforms', 'view_cls'

    def __init__(self, program: ShaderProgramBase, name: str, index: int, size: int, binding: int,
                 uniforms: dict, uniform_count: int) -> None:
        """Initialize a uniform block for a ShaderProgram."""
        self.program = weakref.proxy(program)
        self.name = name
        self.index = index
        self.size = size
        self.binding = binding
        self.uniforms = uniforms
        self.uniform_count = uniform_count
        self.view_cls = None

    def bind(self, ubo: UniformBufferObjectBase) -> None:
        """Bind the Uniform Buffer Object to the binding point of this Uniform Block."""
        raise NotImplementedError

    def create_ubo(self) -> UniformBufferObjectBase:
        """Create a new UniformBufferObject from this uniform block."""
        raise NotImplementedError

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
        raise NotImplementedError

    def _introspect_uniforms(self) -> type[ctypes.Structure]:
        """Introspect the block's structure and return a ctypes struct for manipulating the uniform block's members."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(program={self.program.id}, location={self.index}, size={self.size}, "
                f"binding={self.binding})")
