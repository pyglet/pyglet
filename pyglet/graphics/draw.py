from __future__ import annotations

import weakref
from dataclasses import dataclass
from typing import Any, Callable, Sequence, TYPE_CHECKING

import pyglet
from pyglet.enums import BlendFactor, BlendOp, CompareOp

from pyglet.graphics.state import (
    State,
    TextureState,
    ShaderProgramState,
    BlendState,
    ShaderUniformState,
    UniformBufferState,
    DepthBufferComparison,
    ScissorState,
    ViewportState,
    _expand_states_in_order,
)

if TYPE_CHECKING:
    from pyglet.customtypes import ScissorProtocol
    from pyglet.graphics import GeometryMode
    from pyglet.graphics.api.base import SurfaceContext
    from pyglet.graphics.texture import TextureBase
    from pyglet.graphics.vertexdomain import VertexDomain, VertexList, IndexedVertexList
    from pyglet.graphics.shader import ShaderProgramBase



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

        self._state_names = {}
        self._states = []
        self._expanded_states = []
        self._comparisons = []

        # Default hash
        self._hashable_states = ()
        self._hash = hash((self._order, self.parent))

    def add_state(self, state: State) -> None:
        self._states.append(state)
        self._state_names[state.__class__.__name__] = state
        self._expanded_states = _expand_states_in_order(self._states)

        self._hashable_states = tuple({state for state in self._states if state.group_hash is True})
        self._hash = hash((self._order, self.parent, self._hashable_states))

    def add_comparison(self, value):
        self._comparisons.append(value)

    def set_scissor(self, scissor_object: ScissorProtocol) -> None:
        self.add_state(ScissorState(scissor_object))

    def set_blend(self, blend_src: BlendFactor, blend_dst: BlendFactor, blend_op: BlendOp = BlendOp.ADD):
        self.add_state(BlendState(blend_src, blend_dst, blend_op))

    def set_depth_test(self, func: CompareOp) -> None:
        self.add_state(DepthBufferComparison(func))

    def set_viewport(self, x, y, width, height):
         self.add_state(ViewportState(x, y, width, height))

    def set_shader_program(self, program: ShaderProgramBase):
        self.add_state(ShaderProgramState(program))

    def set_shader_uniforms(self, program: ShaderProgramBase, uniforms: dict[str, Any]):
        self.add_state(ShaderUniformState(program, uniforms))

    def set_uniform_buffer(self, ubo: str, binding: int):
        self.add_state(UniformBufferState(ubo, binding))

    def set_texture(self, texture: TextureBase, texture_unit: int=0, set_id: int=0) -> None:
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
        self.add_state(TextureState.from_texture(texture, texture_unit, set_id))

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
    def batches(self) -> tuple[BatchBase, ...]:
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

    def set_state_all(self, ctx: SurfaceContext) -> None:
        """Calls all set states of the underlying Group."""
        for state in self._expanded_states:
            if state.sets_state:
                state.set_state(ctx)

    def unset_state_all(self, ctx: SurfaceContext) -> None:
        """Calls all unset states of the underlying Group."""
        for state in self._expanded_states:
            if state.unsets_state:
                state.unset_state(ctx)

    def set_state_recursive(self, ctx: SurfaceContext) -> None:
        """Set this group and its ancestry.

        Call this method if you are using a group in isolation: the
        parent groups will be called in top-down order, with this class's
        ``set`` being called last.
        """
        if self.parent:
            self.parent.set_state_recursive(ctx)
        self.set_state_all(ctx)

    def unset_state_recursive(self, ctx: SurfaceContext) -> None:
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

class BatchBase:
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

    def __init__(self, initial_count: int = 32) -> None:
        """Initialize a graphics batch.

        Args:
            initial_count:
                The initial vertex count of the buffers created by this batch.
        """
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
            domain = self._domain_registry[domain_key]
            # It's possible this domain was re-used before being deleted, check one last time before removal.
            if domain.is_empty:
                del self._domain_registry[domain_key]
        self._empty_domains.clear()

    def update_shader(self, vertex_list: VertexList | IndexedVertexList, mode: GeometryMode, group: Group,
                      program: ShaderProgramBase) -> bool:
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
        # No new attributes.
        attributes = program.attributes.copy()

        # Formats may differ (normalization) than what is declared in the shader.
        # Make those adjustments and attempt to get a domain.
        for a_name in attributes:
            if (a_name in vertex_list.initial_attribs and
                    vertex_list.initial_attribs[a_name]['format'] != attributes[a_name]['format']):
                attributes[a_name]['format'] = vertex_list.initial_attribs[a_name]['format']

        domain = self.get_domain(vertex_list.indexed, vertex_list.instanced, mode, group, attributes)

        # TODO: Allow migration if we can restore original vertices somehow. Much faster.
        # If the domain's don't match, we need to re-create the vertex list. Tell caller no match.
        if domain != vertex_list.domain:
            return False

        return True

    def migrate(self, vertex_list: VertexList | IndexedVertexList, mode: GeometryMode, group: Group, batch: BatchBase) -> None:
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
        vertex_list.migrate(domain)

    def get_domain(self, indexed: bool, instanced: bool, mode: GeometryMode, group: Group,
                   attributes: dict[str, Any]) -> VertexDomain:
        """Get, or create, the vertex domain corresponding to the given arguments.

        mode is the render mode such as GL_LINES or GL_TRIANGLES
        """
        # Batch group
        if group not in self.group_map:
            self._add_group(group)

        domain_map = self.group_map[group]

        # If instanced, ensure a separate domain, as multiple instance sources can match the key.
        if instanced:
            self._instance_count += 1
            key = (indexed, self._instance_count, mode, str(attributes))
        else:
            # Find domain given formats, indices and mode
            key = (indexed, 0, mode, str(attributes))

        try:
            domain = domain_map[key]
        except KeyError:
            # Create domain
            domain = _domain_class_map[(indexed, instanced)](attributes)
            domain_map[key] = domain
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

    def _update_draw_list(self) -> None:
        """Visit group tree in preorder and create a list of bound methods to call."""

        def visit(group: Group) -> list:
            draw_list = []

            # Draw domains using this group
            domain_map = self.group_map[group]

            # indexed, instanced, mode, program, str(attributes))
            for (indexed, instanced, mode, formats), domain in list(domain_map.items()):
                # Remove unused domains from batch
                if domain.is_empty:
                    del domain_map[(indexed, instanced, mode, formats)]
                    continue
                draw_list.append((lambda d, m: lambda: d.draw(m))(domain, mode))  # noqa: PLC3002

            # Sort and visit child groups of this group
            children = self.group_children.get(group)
            if children:
                children.sort()
                for child in list(children):
                    if child.visible:
                        draw_list.extend(visit(child))

            if children or domain_map:
                return [group.set_state, *draw_list, group.unset_state]

            # Remove unused group from batch
            del self.group_map[group]
            group._assigned_batches.remove(self)  # noqa: SLF001
            if group.parent:
                self.group_children[group.parent].remove(group)
            try:
                del self.group_children[group]
            except KeyError:
                pass
            try:
                self.top_groups.remove(group)
            except ValueError:
                pass

            return []

        self._draw_list = []

        self.top_groups.sort()
        for top_group in list(self.top_groups):
            if top_group.visible:
                self._draw_list.extend(visit(top_group))

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

    def draw(self) -> None:
        """Draw the batch."""
        if self._draw_list_dirty:
            self._update_draw_list()

        for func in self._draw_list:
            func()

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

        # Horrendously inefficient.
        def visit(group: Group) -> None:
            group.set_state()

            # Draw domains using this group
            domain_map = self.group_map[group]
            for (_, _, mode, _, _), domain in domain_map.items():
                for alist in vertex_lists:
                    if alist.domain is domain:
                        alist.draw(mode)

            # Sort and visit child groups of this group
            children = self.group_children.get(group)
            if children:
                children.sort()
                for child in children:
                    if child.visible:
                        visit(child)

            group.unset_state()

        self.top_groups.sort()
        for top_group in self.top_groups:
            if top_group.visible:
                visit(top_group)


class ShaderGroup(Group):
    """A group that enables and binds a ShaderProgram."""

    def __init__(self, program: ShaderProgramBase, order: int = 0, parent: Group | None = None) -> None:
        super().__init__(order, parent)
        self.set_shader_program(program)

