from __future__ import annotations

import abc
import ctypes
import re
import warnings
import weakref
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Literal, Protocol, Sequence, overload

import pyglet
from pyglet.enums import GeometryMode, GraphicsAPI
from pyglet.graphics.attributes import (
    AttributeFormat,
    ShaderAttribute,
    VertexLayout,
)
from pyglet.graphics.buffer import UniformBufferRegion
from pyglet.graphics.resource import GraphicsResource, ShaderKey, ShaderProgramKey

# Backward-compatible public name for shader input metadata.
Attribute = ShaderAttribute

if TYPE_CHECKING:
    from _weakref import CallableProxyType

    from pyglet.graphics import Batch, Group, VertexStorage
    from pyglet.graphics.buffer import UniformBufferObject
    from pyglet.graphics.vertexdomain import (
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
    _attribute_formats: dict[str, AttributeFormat]
    _uniforms: dict[str, Any]
    _uniform_blocks: dict[str, UniformBlock]
    _samplers: dict[str, Sampler]
    _attribute_key: str
    _attribute_keys: tuple[tuple[Any, ...], ...]
    _domain_layout: VertexLayout
    _legacy_instance_layout: VertexLayout | None
    _vertex_layouts: dict[tuple[Any, ...], ShaderProgramView]
    _format_layouts: dict[str, ShaderProgramView]

    def __init__(self, *shaders: Shader, vertex_layout: VertexLayout | None = None) -> None:
        GraphicsResource.__init__(self)

        # Attribute description
        self._attributes = {}
        self._attribute_formats = {}
        self._attribute_key = str(())
        self._attribute_keys = ()
        self._legacy_instance_layout = None
        self._vertex_layouts = {}
        self._format_layouts = {}
        self._vertex_layout = vertex_layout

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
        for attrib in attributes:
            self._attributes[attrib.name] = attrib
            self._attribute_formats[attrib.name] = AttributeFormat(
                attrib.name, attrib.components, attrib.data_type, False, 0,
            )
        self._update_attribute_key()

    def apply_vertex_layout(self) -> None:
        """Apply the requested default buffer formats to introspected attributes."""
        if self._vertex_layout is not None:
            self._attribute_formats = self._copy_attribute_formats(
                self._attribute_formats, self._attributes, self._vertex_layout.attribute_formats,
            )
            self._update_attribute_key()

    def _update_attribute_key(self) -> None:
        """Cache the platform-independent key used to look up vertex domains."""
        ordered_formats = sorted(self._attribute_formats.values(), key=lambda attribute: attribute.name)
        self._attribute_keys = tuple(attribute.key for attribute in ordered_formats)
        self._domain_layout = VertexLayout(**self._attribute_formats)
        self._attribute_key = self._domain_layout.key
        self._vertex_layouts.clear()
        self._format_layouts.clear()

    @property
    def attribute_key(self) -> str:
        """Stable, cached key describing the geometry formats by name."""
        return self._attribute_key

    @property
    def geometry_layout(self) -> VertexLayout:
        """Geometry layout derived by this legacy shader convenience API."""
        return self._domain_layout

    @property
    def _vertex_layout_program(self) -> _AbstractShaderProgram:
        return self

    def set_instance_attributes(self, **attributes: int) -> _AbstractShaderProgram:
        """Deprecated adapter for creating a view with layout-owned divisors."""
        warnings.warn(
            "set_instance_attributes is deprecated; configure divisors in VertexLayout instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        for name, divisor in attributes.items():
            if name not in self._attributes:
                msg = f"Attribute {name} not found. Existing attributes: {list(self._attributes.keys())}"
                raise MissingAttributeException(msg)
            if divisor < 1:
                raise ValueError(f"Instance divisor for {name!r} must be greater than zero.")

        self._legacy_instance_layout = self.geometry_layout.with_divisors(**attributes)
        return self.get_vertex_view(self._legacy_instance_layout)

    def get_vertex_view(self, vertex_layout: VertexLayout | None = None) -> ShaderProgramView:
        """Return the interned shader-program view for the requested vertex formats.

        Pyglet's Sprite and Label helpers provide colors as four unsigned bytes.
        Prefer ``ShaderProgram(..., vertex_layout=VertexLayout(colors="4Bn"))``
        to set that program's default layout. Use this method only when an
        occasional alternate layout is needed for the same program.
        """
        if vertex_layout is not None and not isinstance(vertex_layout, VertexLayout):
            raise TypeError("vertex_layout must be an VertexLayout or None.")
        formats = {} if vertex_layout is None else vertex_layout.attribute_formats
        try:
            request_key = None if vertex_layout is None else vertex_layout.key
            if request_key is None:
                raise KeyError
            return self._format_layouts[request_key]
        except KeyError:
            pass

        program = self._vertex_layout_program
        attribute_formats = program._copy_attribute_formats(  # noqa: SLF001
            self._attribute_formats, self._attributes, formats,
        )
        attribute_keys = tuple(
            attribute.key for attribute in sorted(attribute_formats.values(), key=lambda attribute: attribute.name)
        )
        layout = program._get_vertex_layout(attribute_formats, attribute_keys)  # noqa: SLF001
        if request_key is not None:
            self._format_layouts[request_key] = layout
        return layout

    def _get_vertex_layout(self, attribute_formats: dict[str, AttributeFormat],
                           attribute_keys: tuple[tuple[Any, ...], ...] | None = None,
                           ) -> ShaderProgramView:
        if attribute_keys is None:
            attribute_keys = tuple(
                attribute.key
                for attribute in sorted(attribute_formats.values(), key=lambda attribute: attribute.name)
            )
        key = attribute_keys
        try:
            return self._vertex_layouts[key]
        except KeyError:
            layout = ShaderProgramView(self, attribute_formats, attribute_keys)
            self._vertex_layouts[key] = layout
            return layout

    @staticmethod
    def _copy_attribute_formats(
            attribute_formats: dict[str, AttributeFormat], shader_attributes: dict[str, Attribute],
            formats: dict[str, AttributeFormat],
    ) -> dict[str, AttributeFormat]:
        adjusted = attribute_formats
        for name, requested in formats.items():
            try:
                shader_attribute = shader_attributes[name]
                source = attribute_formats[name]
            except KeyError:
                msg = f"Attribute {name} not found. Existing attributes: {list(shader_attributes.keys())}"
                raise MissingAttributeException(msg) from None
            if shader_attribute.components != requested.components:
                raise ValueError(f"Geometry format for {name!r} is incompatible with the shader input.")
            if source == requested:
                continue
            if adjusted is attribute_formats:
                adjusted = attribute_formats.copy()
            adjusted[name] = requested
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
        """Shader input metadata dictionary.

        This property returns a dictionary containing metadata of all
        Attributes that were introspected in this ShaderProgram. Modifying
        this dictionary has no effect.
        """
        return self._attributes.copy()

    @property
    def attribute_formats(self) -> dict[str, AttributeFormat]:
        """Geometry formats used to store values for the shader inputs."""
        return self._attribute_formats.copy()

    @property
    def attribute_keys(self) -> tuple[tuple[Any, ...], ...]:
        """Stable tuple describing geometry formats independently of shader locations."""
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
                            storage: VertexStorage | None = None, vertex_layout: VertexLayout | None = None,
                            **data: Any) -> VertexList | InstanceVertexList | IndexedVertexList | InstanceIndexedVertexList:
        layout = layout or self
        batch = batch or pyglet.graphics.get_default_batch()
        storage = batch._resolve_storage(storage)  # noqa: SLF001
        vertex_layout = vertex_layout or (layout._legacy_instance_layout if instanced else None) or layout.geometry_layout
        if vertex_layout is layout.geometry_layout:
            geometry_layout = storage.resolve_layout(vertex_layout)
            assert geometry_layout is not None
        else:
            shader_layout = storage.get_vertex_layout(layout, vertex_layout)
            geometry_layout = shader_layout.geometry_layout
        return batch._create_vertex_list(  # noqa: SLF001
            geometry_layout, count, mode, group or pyglet.graphics.ShaderGroup(program=layout),
            indices=indices,
            instanced=instanced,
            data_error_type=MissingAttributeException,
            storage=storage, **data,
        )

    def vertex_list(self, count: int, mode: GeometryMode, batch: Batch | None = None, group: Group | None = None,
                    storage: VertexStorage | None = None, vertex_layout: VertexLayout | None = None,
                    **data: Any) -> VertexList:
        """Create a VertexList.

        Args:
            count:
                The number of vertices in the list.
            mode:
                A :class:`~pyglet.enums.GeometryMode` value, such as
                :attr:`~pyglet.enums.GeometryMode.POINTS`,
                :attr:`~pyglet.enums.GeometryMode.LINES`, or
                :attr:`~pyglet.enums.GeometryMode.TRIANGLES`.
                This determines how the list is drawn in the given batch.
            batch:
                Batch to add the VertexList to, or ``None`` if a Batch will not be used.
                Using a Batch is strongly recommended.
            group:
                Group to add the VertexList to, or ``None`` to create a default
                :class:`~pyglet.graphics.ShaderGroup` for this program.
            data:
                Initial data for each vertex attribute.

        """
        return self._vertex_list_create(count, mode, None, False, batch=batch, group=group, storage=storage,
                                        vertex_layout=vertex_layout, **data)

    def vertex_list_instanced(self, count: int, mode: GeometryMode, batch: Batch | None = None,
                              group: Group | None = None, **data: Any) -> InstanceVertexList:
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
                A :class:`~pyglet.enums.GeometryMode` value, such as
                :attr:`~pyglet.enums.GeometryMode.POINTS`,
                :attr:`~pyglet.enums.GeometryMode.LINES`, or
                :attr:`~pyglet.enums.GeometryMode.TRIANGLES`.
                This determines how the list is drawn in the given batch.
            indices:
                Sequence of integers giving indices into the vertex list.
            batch:
                Batch to add the VertexList to, or ``None`` if a Batch will not be used.
                Using a Batch is strongly recommended.
            group:
                Group to add the VertexList to, or ``None`` to create a default
                :class:`~pyglet.graphics.ShaderGroup` for this program.
            data:
                Initial data for each vertex attribute.
        """
        return self._vertex_list_create(count, mode, indices, False, batch=batch, group=group, **data)

    def vertex_list_instanced_indexed(self, count: int, *, mode: GeometryMode, indices: Sequence[int],
                                      batch: Batch | None = None, group: Group | None = None,
                                      **data: Any) -> InstanceIndexedVertexList:
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

    def __init__(self, *shaders: _AbstractShader, vertex_layout: VertexLayout | None) -> None:
        """Initialize a shader program with an optional default attribute layout.

        ``vertex_layout=None`` keeps the introspected attribute formats. An
        :class:`VertexLayout` changes only the buffer interpretation of the
        named attributes; their component counts remain defined by the shader.
        """
        assert shaders, "At least one Shader object is required."
        super().__init__(*shaders, vertex_layout=vertex_layout)


class ShaderProgramView(ShaderProgram):
    """An interned ShaderProgram view with a specific vertex layout.

    A view shares its owning program's linked shader and uniforms, but caches
    its own vertex formats, instance divisors, and vertex-domain metadata.
    """

    def __init__(self, program: _AbstractShaderProgram, attribute_formats: dict[str, AttributeFormat],
                 attribute_keys: tuple[tuple[Any, ...], ...]) -> None:
        GraphicsResource.__init__(self, key=program.key)
        self._program = program
        self._attributes = program._attributes
        self._attribute_formats = attribute_formats
        self._legacy_instance_layout = None
        self._attribute_keys = attribute_keys
        self._format_layouts = {}
        self._domain_layout = VertexLayout(**attribute_formats)
        self._attribute_key = self._domain_layout.key

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
    def attribute_formats(self) -> dict[str, AttributeFormat]:
        return self._attribute_formats.copy()

    @property
    def attribute_keys(self) -> tuple[tuple[Any, ...], ...]:
        return self._attribute_keys

    @property
    def attribute_key(self) -> str:
        return self._attribute_key

    @property
    def geometry_layout(self) -> VertexLayout:
        return self._domain_layout

    def set_instance_attributes(self, **attributes: int) -> ShaderProgramView:
        warnings.warn(
            "set_instance_attributes is deprecated; configure divisors in VertexLayout instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        for name, divisor in attributes.items():
            if name not in self._attributes:
                msg = f"Attribute {name} not found. Existing attributes: {list(self._attributes.keys())}"
                raise MissingAttributeException(msg)
            if divisor < 1:
                raise ValueError(f"Instance divisor for {name!r} must be greater than zero.")
        return self._program.get_vertex_view(self.geometry_layout.with_divisors(**attributes))

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
        return self._program._vertex_list_create(
            count, mode, None, True, batch=batch, group=group, layout=self, **data
        )

    def vertex_list_instanced_indexed(self, count: int, *, mode: GeometryMode, indices: Sequence[int],
                                      batch: Batch | None = None, group: Group | None = None,
                                      **data: Any) -> InstanceIndexedVertexList:
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
        vertex_layout: VertexLayout | None,
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
        super().__init__(*shaders, vertex_layout=vertex_layout)
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

    def delete(self) -> None:
        """Delete the shader program's backend resource."""

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

if not pyglet.IS_DOC_BUILD and not TYPE_CHECKING:
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
