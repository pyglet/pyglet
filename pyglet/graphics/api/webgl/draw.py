from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Sequence

import pyglet
from pyglet.graphics.api.webgl import (
    vertexdomain,
)
from pyglet.graphics.api.webgl.enums import geometry_map
from pyglet.graphics.draw import BatchBase, DomainKey, Group

_debug_graphics_batch = pyglet.options.debug_graphics_batch

if TYPE_CHECKING:
    from pyglet.graphics import GeometryMode
    from pyglet.graphics.api.gl.vertexdomain import IndexedVertexList, VertexList
    from pyglet.graphics.api.gl2.shader import ShaderProgram
    from pyglet.graphics.state import State


# Default Shader source:

_vertex_source: str = """#version 330 core
    in vec3 position;
    in vec4 colors;
    in vec3 tex_coords;
    out vec4 vertex_colors;
    out vec3 texture_coords;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    void main()
    {
        gl_Position = window.projection * window.view * vec4(position, 1.0);

        vertex_colors = colors;
        texture_coords = tex_coords;
    }
"""

_fragment_source: str = """#version 330 core
    in vec4 vertex_colors;
    in vec3 texture_coords;
    out vec4 final_colors;

    uniform sampler2D our_texture;

    void main()
    {
        final_colors = texture(our_texture, texture_coords.xy) + vertex_colors;
    }
"""

# Default blit source
_blit_vertex_source: str = """#version 330 core
    in vec3 position;
    in vec3 tex_coords;
    out vec3 texture_coords;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    void main()
    {
        gl_Position = window.projection * window.view * vec4(position, 1.0);

        texture_coords = tex_coords;
    }
"""

_blit_fragment_source: str = """#version 330 core
    in vec3 texture_coords;
    out vec4 final_colors;

    uniform sampler2D our_texture;

    void main()
    {
        final_colors = texture(our_texture, texture_coords.xy);
    }
"""


def get_default_batch() -> Batch:
    """Batch used globally for objects that have no Batch specified."""
    return pyglet.graphics.api.core.get_default_batch()
    # try:
    #     return pyglet.graphics.api.core.current_context.pyglet_graphics_default_batch
    # except AttributeError:
    #     pyglet.graphics.api.core.current_context.pyglet_graphics_default_batch = Batch()
    #     return pyglet.graphics.api.core.current_context.pyglet_graphics_default_batch


def get_default_shader() -> ShaderProgram:
    """A default basic shader for default batches."""
    return pyglet.graphics.api.core.get_cached_shader(
        "default_graphics",
        (_vertex_source, 'vertex'),
        (_fragment_source, 'fragment'),
    )


def get_default_blit_shader() -> ShaderProgram:
    """A default basic shader for blitting, provides no blending."""
    return pyglet.graphics.api.core.get_cached_shader(
        "default_blit",
        (_blit_vertex_source, 'vertex'),
        (_blit_fragment_source, 'fragment'),
    )


_domain_class_map: dict[tuple[bool, bool], type[vertexdomain.VertexDomain]] = {
    # Indexed, Instanced : Domain
    (False, False): vertexdomain.VertexDomain,
    (True, False): vertexdomain.IndexedVertexDomain,
    (False, True): vertexdomain.InstancedVertexDomain,
    (True, True): vertexdomain.InstancedIndexedVertexDomain,
}


class StateManager:
    def __init__(self):
        self.active_states = {}

    def get_state_funcs(self, states: list[State]) -> tuple[list[callable], list[callable]]:
        set_functions = []
        unset_functions = []
        new_states = {}

        # Collect all states and their dependencies
        all_states = []
        for state in states:
            if state.dependents:
                all_states.extend(state.generate_dependent_states())
            all_states.append(state)

        # Process states in dependency order
        for state in all_states:
            state_type = type(state)

            # Handle replacement logic
            if state_type in self.active_states:
                current_state = self.active_states[state_type]
                if state != current_state:
                    # Call unset only if the flag is enabled
                    # if current_state.unsets_state and current_state.call_unset_on_replace:
                    #    unset_functions.append(current_state.unset_state)
                    if state.sets_state:
                        set_functions.append(state.set_state)
            else:
                # New state, add its set function if applicable
                if state.sets_state:
                    set_functions.append(state.set_state)

            # Update new states
            new_states[state_type] = state

        # Determine which states were removed
        removed_states = {
            state_type: self.active_states[state_type]
            for state_type in self.active_states
            if state_type not in new_states
        }

        for state in removed_states.values():
            if state.unsets_state:
                unset_functions.append(state.unset_state)

        # Update active states
        self.active_states = new_states

        return set_functions, unset_functions

    def get_cleanup_states(self) -> list[callable]:
        """Return a list of functions to unset all active states.

        Clears the active states in the process. This is done at the end of the batch draw.
        """
        unset_functions = [state.unset_state for state in self.active_states.values() if state.unsets_state]
        self.active_states.clear()
        return unset_functions


# Singleton instance for all batches. (How to cleanup state between all batches?)
_state_manager: StateManager = StateManager()


class Batch(BatchBase):
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

    _draw_list: list[Callable]
    top_groups: list[Group]
    group_children: dict[Group, list[Group]]
    group_map: dict[Group, dict[DomainKey, vertexdomain.VertexDomain]]

    def __init__(self) -> None:
        """Create a graphics batch."""
        # Mapping to find domain.
        # group -> (attributes, mode, indexed) -> domain
        super().__init__()
        self._context = pyglet.graphics.api.core.current_context

    def invalidate(self) -> None:
        """Force the batch to update the draw list.

        This method can be used to force the batch to re-compute the draw list
        when the ordering of groups has changed.

        .. versionadded:: 1.2
        """
        self._draw_list_dirty = True

    def update_shader(
        self, vertex_list: VertexList | IndexedVertexList, mode: GeometryMode, group: Group, program: ShaderProgram
    ) -> bool:
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
            if (
                a_name in vertex_list.initial_attribs
                and vertex_list.initial_attribs[a_name]['format'] != attributes[a_name]['format']
            ):
                attributes[a_name]['format'] = vertex_list.initial_attribs[a_name]['format']

        domain = self.get_domain(vertex_list.indexed, vertex_list.instanced, mode, group, attributes)

        # TODO: Allow migration if we can restore original vertices somehow. Much faster.
        # If the domain's don't match, we need to re-create the vertex list. Tell caller no match.
        if domain != vertex_list.domain:
            return False

        return True

    def migrate(
        self, vertex_list: VertexList | IndexedVertexList, mode: GeometryMode, group: Group, batch: Batch
    ) -> None:
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

    def _convert_to_instanced(
        self, domain: vertexdomain.VertexDomain | vertexdomain.IndexedVertexDomain, instance_attributes: Sequence[str]
    ) -> vertexdomain.InstancedVertexDomain | vertexdomain.InstancedIndexedVertexDomain:
        """Takes a domain from inside the Batch and creates a new instanced version."""
        # Search for the existing domain.
        for group, domain_map in self.group_map.items():
            for key, mapped_domain in domain_map.items():
                if domain == mapped_domain:
                    # Set instance attributes.
                    new_attributes = mapped_domain.attribute_meta.copy()
                    for name, attribute_dict in new_attributes.items():
                        if name in instance_attributes:
                            attribute_dict['instance'] = True
                    dindexed, dinstanced, dmode, _ = key

                    assert dinstanced == 0, "Cannot convert an instanced domain."
                    return self.get_domain(dindexed, True, dmode, group, new_attributes)

        msg = "Domain was not found and could not be converted."
        raise Exception(msg)

    def get_domain(
        self, indexed: bool, instanced: bool, mode: GeometryMode, group: Group, attributes: dict[str, Any]
    ) -> (
        vertexdomain.VertexDomain
        | vertexdomain.IndexedVertexDomain
        | vertexdomain.InstancedVertexDomain
        | vertexdomain.InstancedIndexedVertexDomain
    ):
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
                draw_list.append((lambda d, m: lambda: d.draw(m))(domain, geometry_map[mode]))  # noqa: PLC3002

            # Sort and visit child groups of this group
            children = self.group_children.get(group)
            if children:
                children.sort()
                for child in list(children):
                    if child.visible:
                        draw_list.extend(visit(child))

            if children or domain_map:
                set_funcs, unset_funcs = _state_manager.get_state_funcs(group.states)
                return [*set_funcs, *draw_list, *unset_funcs]

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

        self._draw_list.extend(_state_manager.get_cleanup_states())

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
