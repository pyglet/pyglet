from __future__ import annotations

import abc
import ctypes
import re
import sys
import warnings
import weakref
from abc import ABC, abstractmethod
from collections import defaultdict
from copy import copy
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Literal, Protocol, Sequence, overload

import pyglet
from pyglet.enums import GeometryMode, GraphicsAPI
from pyglet.graphics.buffer import UniformBufferRegion
from pyglet.graphics.resource import GraphicsResource, ShaderKey, ShaderProgramKey

if TYPE_CHECKING:
    from _weakref import CallableProxyType

    from pyglet.customtypes import CType, DataTypes
    from pyglet.enums import GeometryMode
    from pyglet.graphics import Batch, Group
    from pyglet.graphics.buffer import UniformBufferObject
    from pyglet.graphics.vertexdomain import (
        DomainAttributes,
        IndexedVertexList,
        InstanceIndexedVertexList,
        InstanceVertexList,
        VertexList,
    )


class ShaderException(BaseException):
    pass

class MissingUniformException(ShaderException):
    """Exception for when a Shader uniform is missing due to optimization or mispelling."""

class UnsupportedShaderType(ShaderException):
    """Exception for trying to create an unsupported shader."""

class MissingAttributeException(ShaderException):
    """Exception for when a Shader has a missing attribute name."""

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


class _AbstractShaderProgram(GraphicsResource[Any, ShaderProgramKey], ABC):
    key_type = ShaderProgramKey
    _attributes: dict[str, Attribute]
    _uniforms: dict[str, Any]
    _uniform_blocks: dict[str, UniformBlock]
    _samplers: dict[str, Sampler]
    _attribute_key: str
    _attribute_keys: tuple[tuple[Any, ...], ...]
    _domain_attributes: DomainAttributes
    _instanced_domain_attributes: DomainAttributes | None
    _instance_attributes: dict[str, int]
    _vertex_layouts: dict[tuple[Any, ...], ShaderProgramView]
    _format_layouts: dict[frozenset[tuple[str, str]], ShaderProgramView]

    def __init__(self, *shaders: Shader) -> None:
        GraphicsResource.__init__(self)

        # Attribute description
        self._attributes = {}
        self._attribute_key = str(())
        self._attribute_keys = ()
        self._instanced_domain_attributes = None
        self._instance_attributes = {}
        self._vertex_layouts = {}
        self._format_layouts = {}

        # Uniform description
        self._uniforms = {}

        # Uniform Block description
        self._uniform_blocks = {}

        # Sampler descriptions
        self._samplers = {}

    @property
    def is_defined(self) -> bool:
        """Determine if the ShaderProgram was defined and is ready for use."""
        # Just use the attributes are filled in to determine if it's ready.
        return bool(self._attributes)

    def set_attributes(self, *attributes: Attribute) -> None:
        """Define the attributes of the vertex shader.

        On some backends like OpenGL, this is unnecessary unless you want to redefine the buffers.
        """
        if self._vertex_layouts:
            # Layouts may share the base mapping when a format request was a no-op.
            self._attributes = self._attributes.copy()
        for attrib in attributes:
            self._attributes[attrib.fmt.name] = attrib
        self._update_attribute_key()

    def _update_attribute_key(self) -> None:
        """Cache the platform-independent key used to look up vertex domains."""
        self._attribute_keys = tuple(
            attribute.key for attribute in sorted(self._attributes.values(), key=lambda attribute: attribute.location)
        )
        self._attribute_key = str(self._attribute_keys)
        self._domain_attributes = self.derive_domain_attributes(self._attributes, self._attribute_key)
        self._vertex_layouts.clear()
        self._format_layouts.clear()
        self._instanced_domain_attributes = (
            self._derive_instanced_domain_attributes(
                self._attributes, self._instance_attributes, self._attribute_keys,
            )
            if self._instance_attributes else None
        )

    @staticmethod
    def derive_domain_attributes(attributes: dict[str, Attribute], key: str | None = None) -> DomainAttributes:
        """Create domain metadata for an attribute layout."""
        from pyglet.graphics.vertexdomain import DomainAttributes

        if key is None:
            return DomainAttributes.from_attributes(attributes)
        return DomainAttributes(attributes, key)

    @property
    def attribute_key(self) -> str:
        """Stable, cached key describing all attributes, sorted by location."""
        return self._attribute_key

    @property
    def domain_attributes(self) -> DomainAttributes:
        """Cached attributes and lookup key used for vertex domains."""
        return self._domain_attributes

    @property
    def instanced_domain_attributes(self) -> DomainAttributes:
        """Cached attributes and lookup key used for instanced vertex domains."""
        assert self._instanced_domain_attributes is not None, (
            "Configure instance attributes with set_instance_attributes first."
        )
        return self._instanced_domain_attributes

    @property
    def _vertex_layout_program(self) -> _AbstractShaderProgram:
        return self

    def _derive_instanced_domain_attributes(self, attributes: dict[str, Attribute],
                                             instances: dict[str, int],
                                             attribute_keys: tuple[tuple[Any, ...], ...] | None = None,
                                             ) -> DomainAttributes:
        adjusted = attributes.copy()
        for name, divisor in instances.items():
            attribute = copy(attributes[name])
            attribute.set_divisor(divisor)
            adjusted[name] = attribute
        if attribute_keys is None:
            return self.derive_domain_attributes(adjusted)
        adjusted_keys = tuple(adjusted[key[0]].key for key in attribute_keys)
        return self.derive_domain_attributes(adjusted, str(adjusted_keys))

    def set_instance_attributes(self, **attributes: int) -> _AbstractShaderProgram:
        """Configure the attributes and divisors used by instanced vertex lists."""
        for name, divisor in attributes.items():
            if name not in self._attributes:
                msg = f"Attribute {name} not found. Existing attributes: {list(self._attributes.keys())}"
                raise MissingAttributeException(msg)
            if divisor < 1:
                raise ValueError(f"Instance divisor for {name!r} must be greater than zero.")

        if attributes != self._instance_attributes:
            self._instance_attributes = attributes.copy()
            self._format_layouts.clear()
            self._instanced_domain_attributes = (
                self._derive_instanced_domain_attributes(self._attributes, attributes, self._attribute_keys)
                if attributes else None
            )
        return self

    def get_attribute_view(self, **formats: str) -> ShaderProgramView:
        """Return the interned shader-program view for the requested vertex formats.

        Pyglet's Sprite and Label helpers provide colors as four unsigned bytes.
        A custom shader used with those helpers should therefore use
        ``program.get_attribute_view(colors="Bn")`` so the values are normalized
        before reaching a GLSL ``vec4`` color input.
        """
        try:
            request_key = frozenset(formats.items())
            return self._format_layouts[request_key]
        except TypeError:
            request_key = None
        except KeyError:
            pass

        program = self._vertex_layout_program
        attributes = program._copy_attributes_with_formats(self._attributes, formats)  # noqa: SLF001
        attribute_keys = tuple(attributes[key[0]].key for key in self._attribute_keys)
        layout = program._get_vertex_layout(attributes, self._instance_attributes, attribute_keys)  # noqa: SLF001
        if request_key is not None:
            self._format_layouts[request_key] = layout
        return layout

    def _get_vertex_layout(self, attributes: dict[str, Attribute],
                           instances: dict[str, int],
                           attribute_keys: tuple[tuple[Any, ...], ...] | None = None,
                           ) -> ShaderProgramView:
        if attribute_keys is None:
            attribute_keys = tuple(
                attribute.key for attribute in sorted(attributes.values(), key=lambda attribute: attribute.location)
            )
        key = attribute_keys, frozenset(instances.items())
        try:
            return self._vertex_layouts[key]
        except KeyError:
            layout = ShaderProgramView(self, attributes, instances, attribute_keys)
            self._vertex_layouts[key] = layout
            return layout

    @staticmethod
    def _copy_attributes_with_formats(attributes: dict[str, Attribute], formats: dict[str, str]) -> dict[str, Attribute]:
        adjusted = attributes
        for name, fmt in formats.items():
            valid = (
                isinstance(fmt, str)
                and len(fmt) in (1, 2)
                and fmt[0] in DataTypeTuple
                and (len(fmt) == 1 or fmt[1] == 'n')
            )
            if not valid:
                raise ValueError(f"Invalid vertex format {fmt!r} for attribute {name!r}.")
            try:
                source = attributes[name]
            except KeyError:
                msg = f"Attribute {name} not found. Existing attributes: {list(attributes.keys())}"
                raise MissingAttributeException(msg) from None
            normalized = len(fmt) == 2
            if source.fmt.data_type == fmt[0] and source.fmt.normalized == normalized:
                continue
            if adjusted is attributes:
                adjusted = attributes.copy()
            attribute = copy(source)
            attribute.set_data_type(fmt[0], normalized)
            adjusted[name] = attribute
        return adjusted

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
    def attribute_keys(self) -> tuple[tuple[Any, ...], ...]:
        """Stable tuple describing all attributes, sorted by attribute location."""
        return self._attribute_keys

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

    @staticmethod
    def _missing_uniform_message(uniform_name: str) -> str:
        return (
            f"A Uniform with the name `{uniform_name}` was not found.\n"
            f"The spelling may be incorrect or, if not in use, it "
            f"may have been optimized out by the OpenGL driver."
        )

    def _raise_uniform_operation_exception(self, err: Exception) -> None:
        raise ShaderException from err

    def __setitem__(self, key: str, value: Any) -> None:
        try:
            uniform = self._uniforms[key]
        except KeyError as err:
            msg = self._missing_uniform_message(key)
            if pyglet.options.debug_api_shaders:
                warnings.warn(msg)
                return
            raise MissingUniformException(msg) from err
        try:
            uniform.set(value)
        except Exception as err:  # noqa: BLE001
            self._raise_uniform_operation_exception(err)

    def __getitem__(self, item: str) -> Any:
        try:
            uniform = self._uniforms[item]
        except KeyError as err:
            msg = self._missing_uniform_message(item)
            if pyglet.options.debug_api_shaders:
                warnings.warn(msg)
                return None
            raise MissingUniformException(msg) from err
        try:
            return uniform.get()
        except Exception as err:  # noqa: BLE001
            self._raise_uniform_operation_exception(err)

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
                            instanced: Literal[False] = False, batch: Batch | None = None, group: Group | None = None,
                            **data: Any) -> VertexList:
        ...

    @overload
    def _vertex_list_create(self, count: int, mode: GeometryMode, indices: Sequence[int] = ...,
                            instanced: Literal[False] = False, batch: Batch | None = None, group: Group | None = None,
                            **data: Any) -> IndexedVertexList:
        ...

    @overload
    def _vertex_list_create(self, count: int, mode: GeometryMode, indices: None = None,
                            instanced: Literal[True] = True, batch: Batch | None = None, group: Group | None = None,
                            **data: Any) -> InstanceVertexList:
        ...

    @overload
    def _vertex_list_create(self, count: int, mode: GeometryMode, indices: Sequence[int] = ...,
                            instanced: Literal[True] = True, batch: Batch | None = None, group: Group | None = None,
                            **data: Any) -> InstanceIndexedVertexList:
        ...

    def _vertex_list_create(self, count: int, mode: GeometryMode, indices: Sequence[int] | None = None,
                            instanced: bool = False, batch: Batch | None = None, group: Group | None = None,
                            layout: _AbstractShaderProgram | ShaderProgramView | None = None,
                            **data: Any) -> VertexList | InstanceVertexList | IndexedVertexList | InstanceIndexedVertexList:
        assert isinstance(mode, GeometryMode), f"Mode {mode} is not geometry mode."
        layout = layout or self

        initial_arrays = []
        for name, array in data.items():
            if name not in layout._attributes:
                msg = f"Attribute {name} not found. Existing attributes: {list(layout._attributes.keys())}"
                raise MissingAttributeException(msg) from None
            initial_arrays.append((name, array))

        domain_attributes = layout.instanced_domain_attributes if instanced else layout.domain_attributes
        if pyglet.options.debug_api_shaders:
            if missing_data := [name for name in domain_attributes.attributes if name not in data]:
                warnings.warn(f"No data was supplied for the following found attributes: `{missing_data}`.\n")

        batch = batch or pyglet.graphics.get_default_batch()
        group = group or pyglet.graphics.ShaderGroup(program=layout)
        domain = batch.get_domain(indices is not None, instanced, mode, group, domain_attributes)
        vertex_list = domain.create(group, count, indices)

        for name, array in initial_arrays:
            vertex_list.set_attribute_data(name, array)

        return vertex_list

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
                Initial data for each vertex attribute.

        """
        return self._vertex_list_create(count, mode, None, False, batch=batch, group=group, **data)

    def vertex_list_instanced(self, count: int, mode: GeometryMode, batch: Batch | None = None,
                              group: Group | None = None, **data: Any) -> InstanceVertexList:
        assert self._instance_attributes, "Configure instance attributes with set_instance_attributes first."
        return self._vertex_list_create(
            count, mode, None, True, batch=batch, group=group, **data
        )

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
                Initial data for each vertex attribute.
        """
        return self._vertex_list_create(count, mode, indices, False, batch=batch, group=group, **data)

    def vertex_list_instanced_indexed(self, count: int, *, mode: GeometryMode, indices: Sequence[int],
                                      batch: Batch | None = None, group: Group | None = None,
                                      **data: Any) -> InstanceIndexedVertexList:
        assert self._instance_attributes, "Configure instance attributes with set_instance_attributes first."
        return self._vertex_list_create(
            count, mode, indices, True, batch=batch, group=group, **data
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(handle={self._handle})"


class ShaderProgram(_AbstractShaderProgram):
    """Backend-agnostic shader program container.

    Concrete backends are responsible for compiling/linking shaders,
    introspecting attributes and uniforms, and providing API-specific
    program state management.
    """

    def __init__(self, *shaders: _AbstractShader) -> None:
        """Initialize a shader program from one or more Shader objects."""
        assert shaders, "At least one Shader object is required."
        super().__init__(*shaders)


class ShaderProgramView(ShaderProgram):
    """An interned ShaderProgram view with a specific vertex layout.

    A view shares its owning program's linked shader and uniforms, but caches
    its own vertex formats, instance divisors, and vertex-domain metadata.
    """

    def __init__(self, program: _AbstractShaderProgram, attributes: dict[str, Attribute],
                 instances: dict[str, int], attribute_keys: tuple[tuple[Any, ...], ...]) -> None:
        GraphicsResource.__init__(self, key=program.key)
        self._program = program
        self._attributes = attributes
        self._instance_attributes = instances.copy()
        self._attribute_keys = attribute_keys
        self._attribute_key = str(self._attribute_keys)
        self._format_layouts = {}
        self._domain_attributes = program.derive_domain_attributes(attributes, self._attribute_key)
        self._instanced_domain_attributes = (
            program._derive_instanced_domain_attributes(attributes, instances, attribute_keys) if instances else None
        )

    @property
    def program(self) -> _AbstractShaderProgram:
        """The ShaderProgram that owns this layout."""
        return self._program

    @property
    def _vertex_layout_program(self) -> _AbstractShaderProgram:
        return self._program

    @property
    def handle(self) -> Any:
        """Backend handle of the program this view represents."""
        return self._program.handle

    def delete(self) -> None:
        """Release this view without affecting its owning shader program."""

    @property
    def attributes(self) -> dict[str, Attribute]:
        return self._attributes.copy()

    @property
    def attribute_keys(self) -> tuple[tuple[Any, ...], ...]:
        return self._attribute_keys

    @property
    def attribute_key(self) -> str:
        return self._attribute_key

    @property
    def domain_attributes(self) -> DomainAttributes:
        return self._domain_attributes

    @property
    def instanced_domain_attributes(self) -> DomainAttributes:
        assert self._instanced_domain_attributes is not None, (
            "Configure instance attributes with set_instance_attributes first."
        )
        return self._instanced_domain_attributes

    def set_instance_attributes(self, **attributes: int) -> ShaderProgramView:
        for name, divisor in attributes.items():
            if name not in self._attributes:
                msg = f"Attribute {name} not found. Existing attributes: {list(self._attributes.keys())}"
                raise MissingAttributeException(msg)
            if divisor < 1:
                raise ValueError(f"Instance divisor for {name!r} must be greater than zero.")
        return self._program._get_vertex_layout(self._attributes, attributes, self._attribute_keys)

    def vertex_list(self, count: int, mode: GeometryMode, batch: Batch | None = None,
                    group: Group | None = None, **data: Any) -> VertexList:
        return self._program._vertex_list_create(
            count, mode, batch=batch, group=group, layout=self, **data
        )

    def vertex_list_indexed(self, count: int, mode: GeometryMode, indices: Sequence[int],
                            batch: Batch | None = None, group: Group | None = None,
                            **data: Any) -> IndexedVertexList:
        return self._program._vertex_list_create(
            count, mode, indices, batch=batch, group=group, layout=self, **data
        )

    def vertex_list_instanced(self, count: int, mode: GeometryMode, batch: Batch | None = None,
                              group: Group | None = None, **data: Any) -> InstanceVertexList:
        assert self._instance_attributes, "Configure instance attributes with set_instance_attributes first."
        return self._program._vertex_list_create(
            count, mode, None, True, batch=batch, group=group, layout=self, **data
        )

    def vertex_list_instanced_indexed(self, count: int, *, mode: GeometryMode, indices: Sequence[int],
                                      batch: Batch | None = None, group: Group | None = None,
                                      **data: Any) -> InstanceIndexedVertexList:
        assert self._instance_attributes, "Configure instance attributes with set_instance_attributes first."
        return self._program._vertex_list_create(
            count, mode, indices, True, batch=batch, group=group, layout=self, **data
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self._program, name)

    def __setitem__(self, key: str, value: Any) -> None:
        self._program[key] = value

    def __getitem__(self, key: str) -> Any:
        return self._program[key]

    def __enter__(self) -> None:
        self._program.__enter__()

    def __exit__(self, *args: Any) -> None:
        self._program.__exit__(*args)

    def use(self) -> None:
        self._program.use()

    def stop(self) -> None:
        self._program.stop()

    def delete(self) -> None:
        self._program.delete()

    def __repr__(self) -> str:
        return f"ShaderProgramView(program={self._program!r}, attributes={self._attribute_key})"


class ComputeShaderProgram(_AbstractShaderProgram):
    """Backend-agnostic compute shader program container."""

    def __init__(self, source: str) -> None:
        super().__init__()
        msg = f"{self.__class__.__name__} is backend-specific and must be provided by the active backend."
        raise NotImplementedError(msg)


class TransformFeedbackShaderProgram(ShaderProgram):
    """Backend-agnostic transform feedback shader program container."""
    _id: int

    def __init__(
        self,
        *shaders: _AbstractShader,
        varyings: Sequence[str],
        varying_buffer_type: Literal["interleaved", "separate"] = "separate",
    ) -> None:
        """Initialize a transform feedback shader program.

        Args:
            shaders:
                One or more :py:class:`~pyglet.graphics.shader.Shader` instances.
            varyings:
                Names of vertex/geometry shader output variables to capture with
                transform feedback.
            varying_buffer_type:
                Buffer packing mode for captured outputs:
                ``"separate"`` (one buffer per varying) or ``"interleaved"``
                (single interleaved buffer).

        Notes:
            This class is replaced by a backend-specific implementation at
            import time when a supported backend is active.
        """
        super().__init__(*shaders)
        _ = varyings, varying_buffer_type
        msg = f"{self.__class__.__name__} is backend-specific and must be provided by the active backend."
        raise NotImplementedError(msg)

class ShaderSource(abc.ABC):
    """String source of shader used during load of a Shader instance."""

    @abstractmethod
    def validate(self) -> str:
        """Return the validated shader source."""


class _AbstractShader(GraphicsResource[Any, ShaderKey], abc.ABC):
    """Graphics shader.

    Shader objects may be compiled on instantiation if OpenGL or already compiled in Vulkan.
    You can reuse a Shader object in multiple ShaderPrograms.
    """
    _src_str: str
    type: ShaderType
    key_type = ShaderKey

    def __init__(self, source_string: str, shader_type: ShaderType) -> None:
        """Initialize a shader type."""
        GraphicsResource.__init__(self)
        self._src_str = source_string
        self.type = shader_type

        available_shaders = self.supported_shaders()
        if shader_type not in available_shaders:
            msg = (
                f"Shader type '{shader_type}' is not supported by this shader class."
                f"Supported types are: {available_shaders}"
            )
            raise UnsupportedShaderType(msg)

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

    @property
    def key(self) -> tuple[str, int, int, DataTypes, bool, int]:
        """Stable tuple that describes this attribute's domain-relevant format."""
        return (
            self.fmt.name,
            self.location,
            self.fmt.components,
            self.fmt.data_type,
            self.fmt.normalized,
            self.fmt.divisor,
        )


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
            raise MissingUniformException(msg)

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
            raise MissingUniformException(msg)

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
        """Bind a UBO to the binding point of this uniform block."""
        self._bind_buffer_base(self.binding, ubo.buffer.handle)

    def create_ubo(
        self,
        *,
        copies_per_resource: int = 3,
        alignment: int | None = None,
        strict: bool = False,
    ) -> UniformBufferObject:
        """Create a new UniformBufferObject from this uniform block."""
        return self._create_backend_ubo(
            self.view_cls,
            self.size,
            self.binding,
            alignment,
            copies_per_resource,
            strict,
        )

    def create_ubo_region(
        self,
        *,
        copies_per_resource: int = 3,
        alignment: int | None = None,
        strict: bool = False,
    ) -> UniformBufferRegion:
        """Create a ring-buffered region for updating and binding this uniform block."""

        ubo = self.create_ubo(
            copies_per_resource=copies_per_resource,
            alignment=alignment,
            strict=strict,
        )
        return UniformBufferRegion(ubo, copies_per_resource=copies_per_resource)

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
        alignment: int | None,
        copies_per_resource: int,
        strict: bool,
    ) -> UniformBufferObject:
        raise NotImplementedError

    @abstractmethod
    def _set_block_binding(self) -> None:
        raise NotImplementedError

    def _introspect_uniforms(self) -> type[ctypes.Structure]:
        """Introspect the block's structure and return a ctypes struct for manipulating the uniform block's members."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return (f"{self.__class__.__name__}(program={self.program.handle}, location={self.index}, size={self.size}, "
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
            GLTransformFeedbackShaderProgram as TransformFeedbackShaderProgram,
        )
        from pyglet.graphics.api.gl.shader import get_default_shader
    elif pyglet.options.backend in (GraphicsAPI.OPENGL_2, GraphicsAPI.OPENGL_ES_2):
        from pyglet.graphics.api.gl2.shader import (
            ComputeShaderProgram,
            Shader,
            ShaderProgram,
            TransformFeedbackShaderProgram,
        )
        from pyglet.graphics.api.gl2.shader import get_default_shader
    elif pyglet.options.backend == GraphicsAPI.WEBGL:
        from pyglet.graphics.api.webgl.shader import (
            WebGLComputeShaderProgram as ComputeShaderProgram,
            WebGLShader as Shader,
            WebGLShaderProgram as ShaderProgram,
            WebGLTransformFeedbackShaderProgram as TransformFeedbackShaderProgram,
        )
        from pyglet.graphics.api.webgl.shader import get_default_shader
    elif pyglet.options.backend == GraphicsAPI.VULKAN:
        from pyglet.graphics.api.vulkan.shader import ComputeShaderProgram, Shader, ShaderProgram
    else:
        msg = f"Unsupported backend: {pyglet.options.backend}"
        raise RuntimeError(msg)

    # A view forwards all program operations to its owner, so it is also a
    # valid program for the active backend at runtime.
    ShaderProgram.register(ShaderProgramView)
