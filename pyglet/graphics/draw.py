from __future__ import annotations

import contextlib
import sys
import warnings
import weakref
from copy import copy
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generic, Sequence, TypeVar, Generator

import pyglet
from pyglet.enums import BlendFactor, BlendOp, CompareOp, GeometryMode, GraphicsAPI
from pyglet.graphics.api.base import BackendRenderer, SurfaceContext
from pyglet.graphics.state import (
    BlendState,
    CameraScissorProviderProtocol,
    CameraScopeProtocol,
    CameraScopeState,
    DepthBufferComparison,
    MultiTextureSamplerState,
    ScissorState,
    ShaderProgramState,
    ShaderUniformState,
    State,
    TextureState,
    UniformBufferState,
    ViewportState,
    _expand_states_in_order,
)
if TYPE_CHECKING:
    from pyglet.graphics.buffer import UniformBufferRegion
    from pyglet.window.camera.base import BaseCamera, CameraScissor
    from pyglet.customtypes import ScissorProtocol
    from pyglet.graphics.shader import ShaderProgram
    from pyglet.graphics.texture import Texture
    from pyglet.graphics.vertexdomain import IndexedVertexList, VertexDomain, VertexList



class Group:
    """Group of common state.

    ``Group`` provides extra control over how drawables are handled within a
    ``Batch``. When a batch draws a drawable, it ensures its group's state is set;
    this can include binding textures, shaders, or setting any other parameters.
    It also sorts the groups before drawing.

    In the following example, the background sprite is guaranteed to be drawn
    before the car and the boat::

        batch = pyglet.graphics.Batch()
        background = pyglet.graphics.Group(order=0)
        foreground = pyglet.graphics.Group(order=1)

        background = pyglet.sprite.Sprite(background_image, batch=batch, group=background)
        car = pyglet.sprite.Sprite(car_image, batch=batch, group=foreground)
        boat = pyglet.sprite.Sprite(boat_image, batch=batch, group=foreground)

        def on_draw():
            batch.draw()
    """
    states: list[State]
    _hash: int
    _hashable_states: tuple

    def __init__(self, order: int = 0, parent: Group | None = None) -> None:
        """Initialize a rendering group.

        Args:
            order:
                Set the order to render above or below other Groups.
                Lower orders are drawn first.
            parent:
                Group to contain this Group; its state will be set before this Group's state.
        """
        self._order = order
        self.parent = parent
        self._visible = True
        self._assigned_batches = weakref.WeakSet()

        self._enforced_states = []
        self._state_names = {}
        self._expanded_states = []
        self._comparisons = []

        # Default hash
        self._hashable_states = ()
        self._hash = hash((self._order, self.parent))

        if parent and parent.has_enforced_states:
            for p_state in parent._enforced_states:  # noqa: SLF001
                self.set_state(p_state)

    @property
    def has_enforced_states(self) -> bool:
        """If this group has states that automatically apply to children."""
        return bool(self._enforced_states)

    def set_state(self, state: State) -> None:
        """Sets a state to be applied to the group.

        If the state is an enforced state, setting a new state will not update any children.
        """
        assert not self.batches, "New states cannot be set once a group is in a batch."
        state_type = type(state)
        self._state_names[state_type.__name__] = state
        group_states = self._state_names.values()
        self._expanded_states = _expand_states_in_order(group_states)
        if state.enforced_state:
            self._enforced_states.append(state)

        self._hashable_states = tuple({state for state in group_states if state.group_hash is True})
        self._hash = hash((self._order, self.parent, self._hashable_states))

    @property
    def states(self) -> tuple[State, ...]:
        """The states that will apply to members of this group."""
        return tuple(self._state_names.values())

    def add_comparison(self, value):
        self._comparisons.append(value)

    def set_scissor(self, scissor_object: ScissorProtocol) -> None:
        self.set_state(ScissorState(scissor_object))

    def set_camera(self, camera: CameraScopeProtocol) -> None:
        """Set a camera scope for this group.

        The camera object is applied during batch draw inside a draw context.
        If the camera/view provides an effective scissor area, a matching
        camera scissor state is attached automatically.
        """
        self.set_state(CameraScopeState(camera))
        if isinstance(camera, CameraScissorProviderProtocol):
            scissor = camera.get_group_scissor_area()
            if scissor is not None:
                self.set_state(ScissorState(scissor, owned_by_camera=True))

    def set_blend(self, blend_src: BlendFactor, blend_dst: BlendFactor, blend_op: BlendOp = BlendOp.ADD):
        self.set_state(BlendState(blend_src, blend_dst, blend_op))

    def set_depth_test(self, func: CompareOp) -> None:
        self.set_state(DepthBufferComparison(func))

    def set_viewport(self, x, y, width, height):
        self.set_state(ViewportState(x, y, width, height))

    def set_shader_program(self, program: ShaderProgram):
        self.set_state(ShaderProgramState(program))

    def set_shader_uniforms(self, program: ShaderProgram, uniforms: dict[str, Any]) -> None:
        self.set_state(ShaderUniformState(program, uniforms))

    def set_uniform_buffer(self, region: UniformBufferRegion, binding_index: int | None = None) -> None:
        """Set a Uniform Buffer Object region state.

        Args:
            region:
                A region created by ``UniformBlock.create_ubo_region``.
            binding_index:
                Optional binding point override. By default, the region uses
                the binding point assigned to its source uniform block.
        """
        self.set_state(UniformBufferState(region, binding_index))

    def set_texture(self, texture: Texture, texture_unit: int=0, set_id: int=0) -> None:
        """Set the texture state.

        Args:
            texture:
                The Texture instance that this draw call uses.
            texture_unit:
                The binding unit this Texture/Sampler is bound to.
                In OpenGL this is the Active Texture (glActiveTexture).
                In Vulkan this is the Sampler binding number in the descriptor.
            set_id:
                The set that the sampler belongs to. Only applicable in Vulkan.
        """
        self._state_names.pop(MultiTextureSamplerState.__name__, None)
        self.set_state(TextureState.from_texture(texture, texture_unit, set_id))

    def set_textures(
            self,
            textures: dict[str, Texture],
            program: ShaderProgram,
            first_texture_unit: int = 0,
            set_id: int = 0) -> None:
        """Set multiple texture states and matching sampler uniforms.

        Args:
            textures:
                Mapping of shader sampler uniform names to Texture instances.
            program:
                The shader program that owns the sampler uniforms.
            first_texture_unit:
                The first binding unit to use. Each texture uses the next unit.
            set_id:
                The set that the sampler belongs to. Only applicable in Vulkan.
        """
        self._state_names.pop(TextureState.__name__, None)
        self.set_state(MultiTextureSamplerState.from_textures(program, textures, first_texture_unit, set_id))

    @property
    def order(self) -> int:
        """Rendering order of this group compared to others.

        Lower numbers are drawn first.
        """
        return self._order

    @property
    def visible(self) -> bool:
        """Visibility of the group in the rendering pipeline.

        Determines whether this Group is visible in any of the Batches
        it is assigned to. If ``False``, objects in this Group will not
        be rendered.
        """
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = value

        for batch in self._assigned_batches:
            batch.invalidate()

    @property
    def batches(self) -> tuple[Batch, ...]:
        """Which graphics Batches this Group is a part of.

        Read Only.
        """
        return tuple(self._assigned_batches)

    def __lt__(self, other: Group) -> bool:
        return self._order < other.order

    def __eq__(self, other: Group) -> bool:
        """Comparison function used to determine if another Group is providing the same state.

        When the same state is determined, those groups will be consolidated into one draw call.

        If subclassing, then care must be taken to ensure this function can compare to another of the same group.

        :see: ``__hash__`` function, both must be implemented.
        """
        return (self.__class__ is other.__class__ and
                self._order == other.order and
                self.parent == other.parent and
                self._hashable_states == other._hashable_states and
                self._comparisons == other._comparisons)

    def __hash__(self) -> int:
        """This is an immutable return to establish the permanent identity of the object.

        This is used by Python with ``__eq__`` to determine if something is unique.

        For simplicity, the hash should be a tuple containing your unique identifiers of your Group.

        By default, this is (``order``, ``parent``).

        :see: ``__eq__`` function, both must be implemented.
        """
        return self._hash

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(order={self._order})"

    def set_state_all(self, ctx: DrawContext) -> None:
        """Calls all set states of the underlying Group."""
        for state in self._expanded_states:
            if state.sets_state:
                state.set_state(ctx)

    def unset_state_all(self, ctx: DrawContext) -> None:
        """Calls all unset states of the underlying Group."""
        for state in self._expanded_states:
            if state.unsets_state:
                state.unset_state(ctx)

    def set_state_recursive(self, ctx: DrawContext) -> None:
        """Set this group and its ancestry.

        Call this method if you are using a group in isolation: the
        parent groups will be called in top-down order, with this class's
        ``set`` being called last.
        """
        if self.parent:
            self.parent.set_state_recursive(ctx)
        self.set_state_all(ctx)

    def unset_state_recursive(self, ctx: DrawContext) -> None:
        """Unset this group and its ancestry.

        The inverse of ``set_state_recursive``.
        """
        self.unset_state_all(ctx)
        if self.parent:
            self.parent.unset_state_recursive(ctx)


_debug_graphics_batch = pyglet.options.debug_graphics_batch
_domain_class_map: dict[tuple[bool, bool], type[VertexDomain]] = {
    # Indexed, Instanced : Domain
   #  (False, False): vertexdomain.VertexDomain,
   # (True, False): vertexdomain.IndexedVertexDomain,
   # (False, True): vertexdomain.InstancedVertexDomain,
   #  (True, True): vertexdomain.InstancedIndexedVertexDomain,
}

@dataclass(frozen=True)
class _DomainKey:
    indexed: bool
    instanced: bool
    mode: GeometryMode
    attributes: str

@dataclass
class BatchDrawOptions:
    """A draw pass encompasses the starting data of a batched draw.

    A user may fill some or none of the arguments.
    """

    #: The framebuffer render target. If not specified, the window framebuffer.
    framebuffer: object | None = None

    #: The camera to use at the start. Some passes may require drawing the same scene with a different camera.
    camera: BaseCamera | None = None
    viewport: tuple | None = None
    scissor: tuple | CameraScissor | None = None

    clear_color: tuple[float, float, float, float] | None = None

    def resolve(self, ctx: SurfaceContext) -> DrawPass:
        """Resolves the draw options to give a final DrawPass."""
        camera = self.camera or ctx.window.default_camera
        return DrawPass(
            #framebuffer=self.framebuffer or ctx.default_framebuffer,
            framebuffer=self.framebuffer,
            camera=camera,
            viewport=self.viewport or camera.viewport,
            scissor=self.scissor or camera.view.scissor,
            clear_color=self.clear_color or ctx.clear_color,
        )

@dataclass
class DrawPass:
    """This is the resolved state of the DrawPass.

    This class is guaranteed to have all the arguments filled after the backend resolves it.
    """
    framebuffer: object | None
    camera: BaseCamera
    viewport: tuple
    scissor: CameraScissor
    clear_color: tuple[float, float, float, float]

SurfaceContextT = TypeVar("SurfaceContextT", bound=SurfaceContext)
BackendContextT = TypeVar("BackendContextT")

@dataclass
class DrawContext(Generic[SurfaceContextT, BackendContextT]):
    """This temporary context is passed to Group states during batch draw.

    The data in this object is only valid during the batch draw call.
    """
    # The active backend surface during draw.
    surface_ctx: SurfaceContextT
    backend_ctx: BackendContextT

    # The draw pass used in this.
    draw_pass: DrawPass
    renderer: BackendRenderer

    camera_stack: list[CameraScopeProtocol] = field(default_factory=list)
    viewport_stack: list = field(default_factory=list)
    scissor_stack: list = field(default_factory=list)

    active_shader_program: ShaderProgram | None = None

    # Keep track of current camera to prevent double applies.
    _applied_camera: CameraScopeProtocol | None = None

    def __post_init__(self) -> None:
        if not self.camera_stack and self.draw_pass.camera is not None:
            self.camera_stack.append(self.draw_pass.camera)

    @property
    def active_camera(self) -> CameraScopeProtocol:
        return self.camera_stack[-1]

    @property
    def active_viewport(self) -> tuple | None:
        if self.viewport_stack:
            return self.viewport_stack[-1]
        return None

    @property
    def active_scissor(self) -> tuple | None:
        if self.scissor_stack:
            return self.scissor_stack[-1]
        return None

    def apply_camera_scope(self, *, commit: bool = True) -> None:
        if not self.camera_stack:
            return
        camera = self.active_camera
        if camera is self._applied_camera:
            return
        camera.begin(draw_context=self, commit=commit)
        self._applied_camera = camera
        self.apply_viewport()
        self.apply_scissor()

    def apply_viewport(self) -> None:
        viewport_state = self.active_viewport
        if viewport_state is not None:
            viewport = (viewport_state.x, viewport_state.y, viewport_state.width, viewport_state.height)
        else:
            viewport = self.active_camera.viewport or self.draw_pass.viewport

        if viewport is None:
            return

        x, y, width, height = viewport
        self.renderer.set_viewport(int(x), int(y), int(width), int(height))

    def apply_scissor(self) -> None:
        scissor_state = self.active_scissor
        if scissor_state is not None:
            scissor = scissor_state.scissor
        else:
            scissor = self.active_camera.get_group_scissor_area()
            if scissor is None:
                scissor = self.draw_pass.scissor

        self.renderer.set_scissor(scissor)

    def apply_clear_color(self, r: float, g: float, b: float, a: float) -> None:
        self.renderer.set_clear_color(r, g, b, a)

    def begin(self) -> None:
        self.apply_clear_color(*self.draw_pass.clear_color)
        self.apply_camera_scope()


class Batch:
    """Manage a collection of drawables for batched rendering.

    Many drawable pyglet objects accept an optional `Batch` argument in their
    constructors. By giving a `Batch` to multiple objects, you can tell pyglet
    that you expect to draw all of these objects at once, so it can optimise its
    use of OpenGL. Hence, drawing a `Batch` is often much faster than drawing
    each contained drawable separately.

    The following example creates a batch, adds two sprites to the batch, and
    then draws the entire batch::

        batch = pyglet.graphics.Batch()
        car = pyglet.sprite.Sprite(car_image, batch=batch)
        boat = pyglet.sprite.Sprite(boat_image, batch=batch)

        def on_draw():
            batch.draw()

    While any drawables can be added to a `Batch`, only those with the same
    draw mode, shader program, and group can be optimised together.

    Internally, a `Batch` manages a set of VertexDomains along with
    information about how the domains are to be drawn. To implement batching on
    a custom drawable, get your vertex domains from the given batch instead of
    setting them up yourself.
    """
    _empty_domains: set[_DomainKey]
    _domain_registry: dict[_DomainKey, Any]
    _draw_list: list[Callable]
    top_groups: list[Group]
    group_children: dict[Group, list[Group]]
    group_map: dict[Group, dict[_DomainKey, VertexDomain]]
    initial_count: int
    _domain_class_map: dict[tuple[bool, bool], type[VertexDomain]] = _domain_class_map

    def __init__(self, context: SurfaceContext | None = None, initial_count: int = 32) -> None:
        """Initialize a graphics batch.

        Args:
            context:
                The SurfaceContext this batch will create resources against.
            initial_count:
                The initial vertex count of the buffers created by this batch.
        """
        self._context = context or pyglet.graphics.api.core.current_context
        assert self._context is not None, "A context needs to exist before you create this."

        # Mapping to find domain.
        # group -> (attributes, mode, indexed) -> domain
        self.group_map = {}

        # Mapping of group to list of children.
        self.group_children = {}

        # List of top-level groups
        self.top_groups = []

        self._draw_list = []
        self._draw_list_dirty = False

        # Mapping of DomainKey to a VertexDomain
        self._domain_registry = {}

        # Keep empty domains around for a little to prevent possible.
        self._empty_domains = set()

        self.initial_count = initial_count

    def invalidate(self) -> None:
        """Force the batch to update the draw list.

        This method can be used to force the batch to re-compute the draw list
        when the ordering of groups has changed.

        .. versionadded:: 1.2
        """
        self._draw_list_dirty = True

    def delete_empty_domains(self) -> None:
        """Deletes all empty domains and all of their buffers.

        Should not need to be called through normal usage, as this will occur periodically.
        """
        for domain_key in self._empty_domains:
            domain = self._domain_registry.get(domain_key)
            if domain is None:
                continue
            # It's possible this domain was re-used before being deleted, check one last time before removal.
            if domain.is_empty:
                del self._domain_registry[domain_key]
        self._empty_domains.clear()

    @staticmethod
    def _attributes_key(attributes: dict[str, Any]) -> str:
        """Sort by the location, since introspection order can change depending on platform."""
        return str(tuple(
            attribute.key for attribute in sorted(attributes.values(), key=lambda attribute: attribute.location)
        ))

    @staticmethod
    def _normalized_shader_attributes(program: ShaderProgram, initial_attribs: dict[str, Any]) -> dict[str, Any]:
        """Return shader attributes adjusted to the vertex-list's original buffer formats."""
        attributes = program.attributes

        # Preserve the vertex-list's concrete storage formats for lookup/compatibility.
        for a_name, *_ in program.attribute_keys:
            initial_attribute = initial_attribs.get(a_name)
            if initial_attribute is None:
                continue
            attribute = attributes[a_name]

            needs_data_type = (
                initial_attribute.fmt.data_type != attribute.fmt.data_type or
                initial_attribute.fmt.normalized != attribute.fmt.normalized
            )
            needs_divisor = initial_attribute.fmt.divisor != attribute.fmt.divisor

            if not needs_data_type and not needs_divisor:
                continue

            adjusted_attribute = copy(attribute)
            if needs_data_type:
                adjusted_attribute.set_data_type(initial_attribute.fmt.data_type, initial_attribute.fmt.normalized)
            if needs_divisor:
                adjusted_attribute.set_divisor(initial_attribute.fmt.divisor)
            attributes[a_name] = adjusted_attribute

        return attributes

    def update_shader(self, vertex_list: VertexList | IndexedVertexList, mode: GeometryMode, group: Group,
                      program: ShaderProgram) -> bool:
        """Migrate a vertex list to another domain that has the specified shader attributes.

        The results are undefined if `mode` is not correct or if `vertex_list`
        does not belong to this batch (they are not checked and will not
        necessarily throw an exception immediately).

        Args:
            vertex_list:
                A vertex list currently belonging to this batch.
            mode:
                The current GL drawing mode of the vertex list.
            group:
                The new group to migrate to.
            program:
                The new shader program to migrate to.

        Returns:
            False if the domain's no longer match. The caller should handle this scenario.
        """
        attributes = self._normalized_shader_attributes(program, vertex_list.initial_attribs)

        # Changing shaders for existing drawables are limited by the attributes
        # the drawable originally allocated buffers for.
        if missing := [name for name in vertex_list.initial_attribs if name not in attributes]:
            if _debug_graphics_batch:
                warnings.warn(f"Missing required shader attributes for update: {missing}")
            return False

        drawable_attributes = {name: attributes[name] for name in vertex_list.initial_attribs}
        domain = self.get_domain(vertex_list.indexed, vertex_list.instanced, mode, group, drawable_attributes)

        # TODO: Allow migration if we can restore original vertices somehow. Much faster.
        # If the domain's don't match, we need to re-create the vertex list. Tell caller no match.
        if domain != vertex_list.domain:
            return False

        # Same domain, but state can still differ (for example, a different program).
        if vertex_list.group != group:
            vertex_list.update_group(group)
            self._draw_list_dirty = True

        return True

    def migrate(
            self,
            vertex_list: VertexList | IndexedVertexList,
            mode: GeometryMode,
            group: Group,
            batch: Batch) -> None:
        """Migrate a vertex list to another batch and/or group.

        `vertex_list` and `mode` together identify the vertex list to migrate.
        `group` and `batch` are new owners of the vertex list after migration.

        The results are undefined if `mode` is not correct or if `vertex_list`
        does not belong to this batch (they are not checked and will not
        necessarily throw an exception immediately).

        ``batch`` can remain unchanged if only a group change is desired.

        Args:
            vertex_list:
                A vertex list currently belonging to this batch.
            mode:
                The current GL drawing mode of the vertex list.
            group:
                The new group to migrate to.
            batch:
                The batch to migrate to (or the current batch).

        """
        attributes = vertex_list.domain.attribute_meta
        domain = batch.get_domain(vertex_list.indexed, vertex_list.instanced, mode, group, attributes)

        if domain != vertex_list.domain:
            vertex_list.migrate(domain, group)
        else:
            # If the same domain, no need to move vertices, just update the group.
            vertex_list.update_group(group)

            # Updating group can potentially change draw order though.
            self._draw_list_dirty = True


    def get_domain(self, indexed: bool, instanced: bool, mode: GeometryMode, group: Group,
                   attributes: dict[str, Any]) -> VertexDomain:
        """Get, or create, the vertex domain corresponding to the given arguments.

        mode is the render mode such as GL_LINES or GL_TRIANGLES
        """
        # Group map just used for group lookup now, not domains.
        if group not in self.group_map:
            self._add_group(group)

        # If instanced, ensure a separate domain, as multiple instance sources can match the key.
        # Find domain given formats, indices and mode
        key = _DomainKey(indexed, instanced, mode, self._attributes_key(attributes))

        try:
            domain = self._domain_registry[key]
        except KeyError:
            # Create domain
            domain = self._domain_class_map[(indexed, instanced)](self._context, self.initial_count, attributes)
            self._domain_registry[key] = domain
            self._draw_list_dirty = True
        return domain

    def _add_group(self, group: Group) -> None:
        self.group_map[group] = {}
        if group.parent is None:
            self.top_groups.append(group)
        else:
            if group.parent not in self.group_map:
                self._add_group(group.parent)
            if group.parent not in self.group_children:
                self.group_children[group.parent] = []
            self.group_children[group.parent].append(group)

        group._assigned_batches.add(self)  # noqa: SLF001
        self._draw_list_dirty = True

    def _create_draw_list(self) -> list:
        """Create the backend-specific draw list representation."""
        msg = f"{self.__class__.__name__} must implement _create_draw_list."
        raise NotImplementedError(msg)

    def _compile_draw_list(self, draw_list: list) -> list[Callable]:
        """Compile the backend draw list representation into draw callables."""
        return draw_list

    def _update_draw_list(self) -> None:
        if self._draw_list_dirty:
            draw_list = self._create_draw_list()
            self._draw_list = self._compile_draw_list(draw_list)
            self._draw_list_dirty = False

            if _debug_graphics_batch:
                self._dump_draw_list()

    def _dump_draw_list(self) -> None:
        def dump(group: Group, indent: str = '') -> None:
            print(indent, 'Begin group', group)
            domain_map = self.group_map[group]
            for domain in domain_map.values():
                print(indent, '  ', domain)
                for start, size in zip(*domain.allocator.get_allocated_regions()):
                    print(indent, '    ', 'Region %d size %d:' % (start, size))
                    for key, buffer in domain.attrib_name_buffers.items():
                        print(indent, '      ', end=' ')
                        try:
                            region = buffer.get_region(start, size)
                            print(key, region.array[:])
                        except:  # noqa: E722
                            print(key, '(unmappable)')
            for child in self.group_children.get(group, ()):
                dump(child, indent + '  ')
            print(indent, 'End group', group)

        print(f'Draw list for {self!r}:')
        for group in self.top_groups:
            dump(group)

    def _create_backend_draw_context(self) -> Any:
        """Create temporary backend-specific data for one draw."""
        return None

    def _create_draw_context(self, draw_pass: BatchDrawOptions) -> DrawContext:
        return DrawContext(
            surface_ctx=self._context,
            backend_ctx=self._create_backend_draw_context(),
            draw_pass=draw_pass.resolve(self._context),
            renderer=self._context.renderer,
        )

    def draw(self) -> None:
        """Draw the batch.

        If the draw list is dirty, a new one will be created and applied.
        """
        self._update_draw_list()
        draw_options = BatchDrawOptions()
        draw_ctx = self._create_draw_context(draw_options)
        draw_ctx.begin()

        for func in self._draw_list:
            func(draw_ctx)

        self.delete_empty_domains()

    @contextlib.contextmanager
    def draw_with_options(self) -> Generator[BatchDrawOptions, Any, None]:
        """A context manager for specifying draw options before drawing.

        Can be used as a context manager::

            with batch.draw_with_options() as options:
                options.camera = new_camera

        Upon exit of the context, the draw list functions will be called.

        .. versionadded:: 3.0
        """
        draw_options = BatchDrawOptions()
        try:
            yield draw_options
        finally:
            self._update_draw_list()
            draw_ctx = self._create_draw_context(draw_options)
            draw_ctx.begin()

            for func in self._draw_list:
                func(draw_ctx)

            self.delete_empty_domains()

    def draw_subset(self, vertex_lists: Sequence[VertexList | IndexedVertexList]) -> None:
        """Draw only some vertex lists in the batch.

        The use of this method is highly discouraged, as it is quite
        inefficient.  Usually an application can be redesigned so that batches
        can always be drawn in their entirety, using `draw`.

        The given vertex lists must belong to this batch; behaviour is
        undefined if this condition is not met.

        Args:
            vertex_lists:
                Vertex lists to draw.

        """
        draw_ctx = self._create_draw_context(BatchDrawOptions())
        draw_ctx.begin()

        def visit(group: Group) -> None:
            group.set_state_all(draw_ctx)

            for domain_key, domain in self._domain_registry.items():
                for alist in vertex_lists:
                    if alist.domain is domain and alist.group is group:
                        domain.draw_subset(domain_key.mode, alist)

            # Sort and visit child groups of this group
            children = self.group_children.get(group)
            if children:
                children.sort()
                for child in children:
                    if child.visible:
                        visit(child)

            group.unset_state_all(draw_ctx)

        self.top_groups.sort()
        for top_group in self.top_groups:
            if top_group.visible:
                visit(top_group)


class _BucketBatch(Batch):
    """Shared implementation for GL backends that draw grouped domain buckets."""

    _geometry_map: ClassVar[dict[Any, Any]] = {}

    def _cleanup_groups(self, group: Group) -> None:
        """Safely remove empty groups from all tracking structures."""
        del self.group_map[group]
        group._assigned_batches.remove(self)  # noqa: SLF001
        if group.parent:
            self.group_children[group.parent].remove(group)
        try:  # noqa: SIM105
            del self.group_children[group]
        except KeyError:
            pass
        try:  # noqa: SIM105
            self.top_groups.remove(group)
        except ValueError:
            pass

        for domain in self._domain_registry.values():
            if domain.has_bucket(group):
                del domain._vertex_buckets[group]  # noqa: SLF001

    def _create_draw_list(self) -> list[tuple[Any, Any, Group]]:
        """Rebuild draw list by walking the group tree.

        Backends with different draw submission models should override this
        instead of adapting themselves to the bucket representation.
        """

        def visit(group: Group) -> list[tuple[Any, Any, Group]]:
            draw_list = []
            if not group.visible:
                return draw_list

            is_drawable = False
            for domain_key, domain in self._domain_registry.items():
                if domain.is_empty or not domain.get_drawable_bucket(group):
                    self._empty_domains.add(domain_key)
                    continue
                is_drawable = True
                break

            if not is_drawable and not self.group_children.get(group):
                self._cleanup_groups(group)
                return []

            if is_drawable:
                for domain_key, domain in self._domain_registry.items():
                    bucket = domain.get_drawable_bucket(group)
                    if not bucket:
                        continue

                    draw_list.append((domain, domain_key.mode, group))

            children = self.group_children.get(group, [])
            for child in sorted(children):
                if child.visible:
                    draw_list.extend(visit(child))

            if children or is_drawable:
                return [(None, "set", group), *draw_list, (None, "unset", group)]

            return draw_list

        draw_list = []
        self.top_groups.sort()

        for top_group in list(self.top_groups):
            if top_group.visible:
                draw_list.extend(visit(top_group))

        return draw_list

    @staticmethod
    def _vao_bind_fn(domain):  # noqa: ANN001, ANN205
        def _bind_vao(_ctx) -> None:  # noqa: ANN001
            domain.bind_vao()

        return _bind_vao

    @staticmethod
    def _draw_bucket_fn(domain, buckets, mode_func):  # noqa: ANN001, ANN205
        def _draw(_ctx) -> None:  # noqa: ANN001
            domain.draw_buckets(mode_func, buckets)

        return _draw

    def _optimize_draw_list(self, draw_list: list[tuple]) -> list[Callable]:
        """Turn a flattened ``(domain, mode, group)`` list into optimized callables."""
        calls: list[Callable] = []
        active_states: dict[type, State] = {}

        def _next_same_type_set(idx: int, state_type: type) -> None | State:
            for dom2, mode2, group2 in draw_list[idx + 1:]:
                if dom2 is None and mode2 == "set":
                    for state in group2._expanded_states:  # noqa: SLF001
                        if type(state) is state_type:
                            return state
            return None

        def flush_buckets() -> None:
            nonlocal current_buckets
            if not current_buckets:
                return

            calls.append(self._draw_bucket_fn(last_domain, list(current_buckets), self._geometry_map[last_mode]))
            current_buckets.clear()

        def _emit_set(state: State) -> None:
            state_type = type(state)
            current = active_states.get(state_type)
            if current == state:
                return

            if current_buckets:
                flush_buckets()

            if current and current.unsets_state:
                calls.append(current.unset_state)

            if state.sets_state:
                calls.append(state.set_state)

            active_states[state_type] = state

        def _emit_unset(state: State, idx: int) -> None:
            state_type = type(state)
            current = active_states.get(state_type)
            if current is None:
                return

            next_set = _next_same_type_set(idx, state_type)
            if next_set == current:
                return

            flush_buckets()

            if current.unsets_state:
                calls.append(current.unset_state)
            active_states.pop(state_type, None)

        last_domain = None
        last_mode = None
        current_buckets = []

        for i, (domain, mode, group) in enumerate(draw_list):
            if domain is None:
                if mode == "set":
                    for state in group._expanded_states:  # noqa: SLF001
                        _emit_set(state)
                elif mode == "unset":
                    for state in reversed(group._expanded_states):  # noqa: SLF001
                        _emit_unset(state, i)
                continue

            bucket = domain.get_drawable_bucket(group)
            if not bucket or bucket.is_empty:
                continue

            if last_domain is None:
                calls.append(self._vao_bind_fn(domain))
            elif domain != last_domain:
                flush_buckets()
                calls.append(self._vao_bind_fn(domain))
            elif mode != last_mode:
                flush_buckets()

            current_buckets.append(bucket)
            last_domain = domain
            last_mode = mode

        flush_buckets()

        return calls

    def _dump_draw_list_call_order(self, draw_list: list[Callable], include_dc: bool = True) -> None:
        import inspect

        print("=== DRAW ORDER ===")

        def fn_label(fn: Callable) -> str:
            text = repr(fn)
            if "unset_state" in text:
                return "UNSET"
            if "set_state" in text:
                return "SET"
            if "_bind_vao" in text:
                return "VAO"
            if "_draw" in text:
                return "DRAW"
            return "CALL"

        def fn_name(fn: Callable) -> str:
            if inspect.ismethod(fn):
                dc_info = f" ({fn.__self__})" if include_dc else ""
                return f"{fn.__self__.__class__.__name__}.{fn.__name__}{dc_info}"
            if inspect.isfunction(fn):
                return fn.__name__
            return fn.__class__.__name__

        for i, fn in enumerate(draw_list):
            print(f"{i:03d} ({fn_label(fn)}): {fn_name(fn)}")
        print("==================")

    def _set_draw_functions(self, draw_list: list[tuple]) -> list[Callable]:
        """Compile a draw list without optimizing state transitions."""
        calls: list[Callable] = []
        last_domain = None

        for domain, mode, group in draw_list:
            if domain is None:
                if mode == "set":
                    calls.extend([state.set_state for state in group._expanded_states if state.sets_state])  # noqa: SLF001
                elif mode == "unset":
                    calls.extend(reversed([
                        state.unset_state for state in group._expanded_states if state.unsets_state  # noqa: SLF001
                    ]))
                continue

            bucket = domain.get_drawable_bucket(group)
            if not bucket or bucket.is_empty:
                continue

            if last_domain is None or domain != last_domain:
                calls.append(self._vao_bind_fn(domain))

            calls.append(self._draw_bucket_fn(domain, [bucket], self._geometry_map[mode]))
            last_domain = domain

        return calls

    def _compile_draw_list(self, draw_list: list[tuple]) -> list[Callable]:
        if pyglet.options.optimize_states:
            return self._optimize_draw_list(draw_list)
        return self._set_draw_functions(draw_list)

    def _dump_draw_list(self) -> None:
        def dump(group: Group, indent: str = '') -> None:
            print(indent, 'Begin group', group)
            for domain in self._domain_registry.values():
                if domain.has_bucket(group):
                    domain_info = repr(domain).split('@')[-1].replace('>', '')
                    print(f"{indent}  > Domain: {domain.__class__.__name__}@{domain_info}")

                    starts, sizes = domain.vertex_buffers.allocator.get_allocated_regions()
                    for start, size in zip(starts, sizes):
                        print(f"{indent}     - Region start={start:<4} size={size:<4}")
                        attribs = ', '.join(domain.attrib_name_buffers.keys())
                        print(f"{indent}       (Attributes: {attribs})")
            for child in self.group_children.get(group, ()):
                dump(child, indent + '  ')
            print(indent, 'End group', group)

        print(f'Draw list for {self!r}:')
        for group in self.top_groups:
            dump(group)


class ShaderGroup(Group):
    """A group that enables and binds a ShaderProgram."""

    def __init__(self, program: ShaderProgram, order: int = 0, parent: Group | None = None) -> None:
        super().__init__(order, parent)
        self.set_shader_program(program)


def get_default_batch() -> Batch:
    """The built in batch object used for objects that have no specified batch."""
    msg = "Default batch is not available for this backend."
    raise RuntimeError(msg)


try:
    _is_pyglet_doc_run = sys.is_pyglet_doc_run
except AttributeError:
    _is_pyglet_doc_run = False

if not _is_pyglet_doc_run:
    if pyglet.options.backend in (GraphicsAPI.OPENGL, GraphicsAPI.OPENGL_ES_3):
        from pyglet.graphics.api.gl.draw import (
            GLBatch as Batch,
        )
        from pyglet.graphics.api.gl.draw import (
            get_default_batch as _backend_get_default_batch,
        )
        get_default_batch = _backend_get_default_batch

    elif pyglet.options.backend in (GraphicsAPI.OPENGL_2, GraphicsAPI.OPENGL_ES_2):
        from pyglet.graphics.api.gl2.draw import (
            GL2Batch as Batch,
        )
        from pyglet.graphics.api.gl2.draw import (
            get_default_batch as _backend_get_default_batch,
        )

        get_default_batch = _backend_get_default_batch

    elif pyglet.options.backend == GraphicsAPI.WEBGL:
        from pyglet.graphics.api.webgl.draw import (
            WebGLBatch as Batch,
        )
        from pyglet.graphics.api.webgl.draw import (
            get_default_batch as _backend_get_default_batch,
        )
        get_default_batch = _backend_get_default_batch
    else:
        msg = f"Unsupported backend: {pyglet.options.backend!r}"
        raise Exception(msg)
