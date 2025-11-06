from __future__ import annotations

from typing import Callable, Sequence, Any, TYPE_CHECKING

import pyglet
from pyglet.graphics.api.gl.enums import geometry_map


from pyglet.graphics.draw import _DomainKey, BatchBase, Group
from pyglet.graphics.api.gl import (
    vertexdomain, OpenGLSurfaceContext,
)
from pyglet.graphics.state import State

_debug_graphics_batch = pyglet.options.debug_graphics_batch

if TYPE_CHECKING:
    from pyglet.graphics import GeometryMode
    from pyglet.graphics.api.gl2.shader import ShaderProgram
    from pyglet.graphics.api.gl.vertexdomain import VertexList, IndexedVertexList


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
    active_states: dict[type, State]

    def __init__(self) -> None:
        self.active_states = {}

    @staticmethod
    def expand_states_to_dict(states: list[State]) -> dict[type, State]:
        """Flatten a groups list of states (including dependents) into a dict."""
        out: dict[type, State] = {}
        all_states: list[State] = []
        for s in states:
            if s.dependents:
                all_states.extend(s.generate_dependent_states())
            all_states.append(s)
        for s in all_states:
            out[type(s)] = s
        return out

    def transition_to(self, target: dict[type, State]) -> tuple[list[Callable], list[Callable]]:
        """Transition from the current active states to the target state set.

        Emits only changes for states that differ or are missing.
        Returns (set_functions, unset_functions).
        """
        set_funcs: list[Callable] = []
        unset_funcs: list[Callable] = []

        current = self.active_states

        # Unset anything that no longer exists in target
        for t, cur in list(current.items()):
            if t not in target:
                if cur.unsets_state:
                    unset_funcs.append(cur.unset_state)
                del current[t]

        # Anything new or changed
        for t, new in target.items():
            old = current.get(t)
            if old is None or old != new:
                if new.sets_state:
                    set_funcs.append(new.set_state)
                current[t] = new
            # else equals no-op

        return set_funcs, unset_funcs

    def get_cleanup_states(self) -> list[Callable]:
        """Return a list of functions to unset all active states.

        Clears the active states in the process. This is done at the end of the batch draw.
        """
        funcs = [s.unset_state for s in self.active_states.values() if s.unsets_state]
        self.active_states.clear()
        return funcs

# Singleton instance for all batches. (How to cleanup state between all batches?)
_state_manager: StateManager = StateManager()


class _DrawConsolidator:
    def __init__(self):
        self.set_states = []
        self.unset_states = []
        self.buckets = []
        self.draw_list = []
        self.last_domain = None
        self.last_mode = None

    def store_states(self, set_states, unset_states):
        self.set_states.extend(set_states)
        self.unset_states.extend(unset_states)

    def commit_states(self):
        self.draw_list.extend(self.set_states)
        self.draw_list.extend(self.unset_states)
        self.set_states.clear()
        self.unset_states.clear()

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
    group_map: dict[Group, dict[_DomainKey, vertexdomain.VertexDomain]]

    def __init__(self, context: OpenGLSurfaceContext | None = None, initial_count: int = 32) -> None:
        """Initialize the batch for use.

        Args:
            context:
                The OpenGL Surface context this batch will be a part of.
            initial_count:
                The initial element_count of the buffers created by the domains in the batch.
        """
        # Mapping to find domain.
        # group -> (attributes, mode, indexed) -> domain
        super().__init__(initial_count)
        self._context = context or pyglet.graphics.api.core.current_context
        assert self._context is not None, "A context needs to exist before you create this."

    def invalidate(self) -> None:
        """Force the batch to update the draw list.

        This method can be used to force the batch to re-compute the draw list
        when the ordering of groups has changed.

        .. versionadded:: 1.2
        """
        self._draw_list_dirty = True

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

    def migrate(self, vertex_list: VertexList | IndexedVertexList, mode: GeometryMode, group: Group,
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
        print("MIGRATING VERTEX LIST?", mode, group)
        attributes = vertex_list.domain.attribute_meta
        domain = batch.get_domain(vertex_list.indexed, vertex_list.instanced, mode, group, attributes)

        # If the same domain, no need to move vertices, just update the group.
        if domain != vertex_list.domain:
            print("THIS DOMAIN", vertex_list.domain, "NEW DOMAIN?", domain)
            vertex_list.migrate(domain)
            bucket = domain.get_group_bucket(group)
            bucket.add_vertex_list(vertex_list)

            print("DRAW LIST IS DIRTY, MIGRATE")
        else:
            vertex_list.update_group(group)

            # Updating group can potentially change draw order though.
            print("DRAW LIST IS DIRTY")
            self._draw_list_dirty = True

    def get_domain(self, indexed: bool, instanced: bool, mode: GeometryMode, group: Group,
                   attributes: dict[str, Any]) -> vertexdomain.VertexDomain | vertexdomain.IndexedVertexDomain | vertexdomain.InstancedVertexDomain | vertexdomain.InstancedIndexedVertexDomain:
        """Get, or create, the vertex domain corresponding to the given arguments.

        mode is the render mode such as GL_LINES or GL_TRIANGLES
        """
        # Batch group
        if group not in self.group_map:
            self._add_group(group)

        # If instanced, ensure a separate domain, as multiple instance sources can match the key.
        # Find domain given formats, indices and mode
        key = _DomainKey(indexed, instanced, mode, str(attributes))

        try:
            domain = self._domain_registry[key]
        except KeyError:
            # Create domain
            domain = _domain_class_map[(indexed, instanced)](self._context, self.initial_count, attributes)
            self._domain_registry[key] = domain
            self._all_domains_in_draw_order.append(domain)   # keep stable append
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

    def _cleanup_groups(self, group: Group) -> None:
        """Safely remove empty groups from all tracking structures."""
        print("CLEAN GROUP?", group)
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

    def _create_draw_list(self) -> list[Callable]:
        """Rebuild draw list by walking the group tree and minimizing state transitions."""
        print("CREATE DRAW LIST")

        def _vao_call_fn(domain):
            def _draw(_context):
                domain.bind_vao()

            return _draw

        def make_draw_buckets_fn(domain, buckets, mode_func):
            def _draw(_context):
                domain.draw_buckets(mode_func, buckets)

            return _draw

        def _flush_buckets(draw_list, last_domain, last_mode):
            nonlocal dc
            draw_list.append(make_draw_buckets_fn(last_domain, list(dc.buckets), last_mode))
            dc.buckets.clear()

        def visit(group: Group, inherited_state: dict[type, State]) -> list[Callable]:
            nonlocal dc

            draw_list: list[Callable] = []
            if not group.visible:
                return draw_list

            dc.draw_list = draw_list

            group_states = _state_manager.expand_states_to_dict(group.states)

            has_states = bool(group_states)

            # Determine if any vertices are drawable.
            is_drawable = False
            for domain in self._domain_registry.values():
                if domain.is_empty or not domain.get_drawable_bucket(group):
                    continue
                is_drawable = True
                break

            # State has nothing drawable and no children to affect.
            # Even if it has states, nothing to apply it to. Return early.
            if not is_drawable and not self.group_children.get(group):
                self._cleanup_groups(group)
                return []

            # Group is not drawable, and has no states, go through visible children.
            if not has_states and not is_drawable:
                for child in sorted(self.group_children.get(group, [])):
                    if child.visible:
                        draw_list.extend(visit(child, inherited_state))
                if not self.group_children.get(group):
                    self._cleanup_groups(group)
                return draw_list
            # Compute this node's effective target state
            target_state = {**inherited_state, **group_states}

            # Apply state transitions
            set_calls, unset_calls = _state_manager.transition_to(target_state)

            state_changed = bool(set_calls or unset_calls)

            dc.store_states(set_calls, unset_calls)

            # If drawable, then find the domains to draw.
            if is_drawable:
                for dkey, domain in self._domain_registry.items():
                    bucket = domain.get_drawable_bucket(group)
                    if not bucket:
                        continue

                    mode_func = geometry_map[dkey.mode]
                    domain_changed = dc.last_domain != domain
                    # If not the last VAO, then assign a VAO.
                    if domain_changed:
                        if dc.buckets:
                            _flush_buckets(draw_list, dc.last_domain, dc.last_mode)

                        dc.commit_states()

                        draw_list.append(_vao_call_fn(domain))

                    # If the state changed, and the domain didn't, states need to still be comitted
                    if state_changed:
                        # Domain change would have flushed already.
                        if not domain_changed:
                            # If the last state has changed, then we can't draw them together. Commit the buckets.
                            if dc.buckets:
                                _flush_buckets(draw_list, dc.last_domain, dc.last_mode)
                            dc.commit_states()

                    dc.buckets.append(bucket)

                    dc.last_domain = domain
                    dc.last_mode = mode_func

            # Recurse into visible children
            for child in sorted(self.group_children.get(group, [])):
                if child.visible:
                    draw_list.extend(visit(child, target_state))

            if not is_drawable:
                dc.commit_states()

            return draw_list

        # Build the final list
        _draw_list = []

        dc = _DrawConsolidator()

        self.top_groups.sort()
        baseline_state: dict[type, State] = {}

        for top in list(self.top_groups):
            if top.visible:
                _draw_list.extend(visit(top, baseline_state))

        # End-of-frame cleanup for anything still active:
        if dc.buckets:
            print(f"We have current buckets, and the state count is being finalized.: {len(dc.buckets)}")
            _draw_list.append(make_draw_buckets_fn(dc.last_domain, list(dc.buckets), dc.last_mode))
        _draw_list.extend(_state_manager.get_cleanup_states())

        #self._draw_list_dirty = False

        #self._debug_dump_group_tree()
        self._dump_draw_order(_draw_list)

        return _draw_list

    def _dump_draw_order(self, draw_list):
        print("=== FINAL DRAW LIST ===")
        for i, fn in enumerate(draw_list):
            print(f"{i:03d}: {fn}")

    def _debug_dump_group_tree(self):
        print("TREE")
        def walk(g, depth=0):
            print("  " * depth + f"- {g!r}")
            for c in sorted(self.group_children.get(g, [])):
                walk(c, depth+1)
        for root in sorted(self.top_groups):
            walk(root)

    def _dump_draw_list(self) -> None:
        def dump(group: Group, indent: str = '') -> None:
            print(indent, 'Begin group', group)
            domain_map = self.group_map[group]
            for domain in domain_map.values():
                print(indent, '  ', domain)
                # for start, size in zip(*domain.allocator.get_allocated_regions()):
                #     print(indent, '    ', 'Region %d size %d:' % (start, size))
                #     for key, buffer in domain.attrib_name_buffers.items():
                #         print(indent, '      ', end=' ')
                #         try:
                #             region = buffer.get_region(start, size)
                #             print(key, region.array[:])
                #         except:
                #             print(key, '(unmappable)')
            for child in self.group_children.get(group, ()):
                dump(child, indent + '  ')
            print(indent, 'End group', group)

        print(f'Draw list for {self!r}:')
        for group in self.top_groups:
            dump(group)

    def _update_draw_list(self) -> None:
        if self._draw_list_dirty:
            self._draw_list = self._create_draw_list()
            self._draw_list_dirty = False

    def draw(self) -> None:
        """Draw the batch."""
        self._update_draw_list()

        for func in self._draw_list:
            func(self._context)

    # def draw_groups(self, *groups: Group) -> None:
    #     """Draw specific groups within the batch.
    #
    #     .. note: This only applies to a top level group; groups within groups not supported and will produce
    #              a KeyError.
    #
    #     .. note: Draw calls are not optimized like the Batch is.
    #     """
    #     #assert self._allow_group_draw, "Enable the draw_group parameter on initialization to use this."
    #
    #     if self._draw_list_dirty:
    #         self._update_draw_list()
    #
    #     for group in groups:
    #         print("GROUP", group)
    #         for dkey, domain in self._domain_registry.items():
    #             domain.bind_vao()
    #             print("BIND", group in domain._buckets, group, domain._buckets)
    #             if group in domain._buckets:
    #                 group.set_state_all(self._context)
    #                 bucket = domain._buckets[group]
    #
    #                 print("BUCKET DRAW?", bucket, bucket.is_empty)
    #                 bucket.draw(dkey.mode)
    #                 group.unset_state_all(self._context)
    #
    #         #for func in self._draw_list_groups[group]:
    #         #    func()

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
            group.set_state_all(self._context)

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

            group.unset_state_all(self._context)

        self.top_groups.sort()
        for top_group in self.top_groups:
            if top_group.visible:
                visit(top_group)
