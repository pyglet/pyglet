from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Sequence

import pyglet
from pyglet.graphics.api.webgl import vertexdomain
from pyglet.graphics.api.webgl.enums import geometry_map
from pyglet.graphics.draw import BatchBase, _DomainKey, Group

_debug_graphics_batch = pyglet.options.debug_graphics_batch

if TYPE_CHECKING:
    from pyglet.graphics import GeometryMode
    from pyglet.graphics.api.webgl.vertexdomain import IndexedVertexList, VertexList
    from pyglet.graphics.api.webgl.shader import ShaderProgram
    from pyglet.graphics.api.webgl.context import OpenGLSurfaceContext
    from pyglet.graphics.state import State


# Default Shader source:

_vertex_source: str = """#version 330 core
    in vec3 position;
    in vec4 colors;

    out vec4 vertex_colors;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    void main()
    {
        gl_Position = window.projection * window.view * vec4(position, 1.0);

        vertex_colors = colors;
    }
"""

_fragment_source: str = """#version 330 core
    in vec4 vertex_colors;
    out vec4 final_colors;

    void main()
    {
        final_colors = vertex_colors;
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


_domain_class_map: dict[tuple[bool, bool], type[vertexdomain.VertexDomain]] = {
    # Indexed, Instanced : Domain
    (False, False): vertexdomain.VertexDomain,
    (True, False): vertexdomain.IndexedVertexDomain,
    (False, True): vertexdomain.InstancedVertexDomain,
    (True, True): vertexdomain.InstancedIndexedVertexDomain,
}


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
                The initial element count of the buffers created by the domains in the batch.

                Increase this value if you plan to load large amounts of vertices, as it will reduce the need for
                resizing buffers, which can be slow.
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
                   attributes: dict[str, Any]) -> vertexdomain.VertexDomain | vertexdomain.IndexedVertexDomain | vertexdomain.InstancedVertexDomain | vertexdomain.InstancedIndexedVertexDomain:
        """Get, or create, the vertex domain corresponding to the given arguments.

        mode is the render mode such as GL_LINES or GL_TRIANGLES
        """
        # Group map just used for group lookup now, not domains.
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
        # Remove bucket from all domains.
        for domain in self._domain_registry.values():
            if domain.has_bucket(group):
                del domain._vertex_buckets[group]  # noqa: SLF001

    def _create_draw_list(self) -> list[Callable]:
        """Rebuild draw list by walking the group tree and minimizing state transitions."""
        def visit(group: Group) -> list[Callable]:
            draw_list = []
            if not group.visible:
                return draw_list

            # Determine if any vertices are drawable.
            is_drawable = False
            for dkey, domain in self._domain_registry.items():
                if domain.is_empty or not domain.get_drawable_bucket(group):
                    self._empty_domains.add(dkey)
                    continue
                is_drawable = True
                break

            # State has nothing drawable and no children to affect.
            # Even if it has states, nothing to apply it to. Clean them and return early.
            if not is_drawable and not self.group_children.get(group):
                self._cleanup_groups(group)
                return []

            # If drawable, then find the domains to draw.
            if is_drawable:
                for dkey, domain in self._domain_registry.items():
                    bucket = domain.get_drawable_bucket(group)
                    if not bucket:
                        continue

                    draw_list.append((domain, dkey.mode, group))

            # Recurse into visible children
            children = self.group_children.get(group, [])
            for child in sorted(children):
                if child.visible:
                    draw_list.extend(visit(child))

            if children or is_drawable:
                return [(None, 'set', group), *draw_list, (None, 'unset', group)]

            return draw_list

        _draw_list = []

        self.top_groups.sort()

        for top in list(self.top_groups):
            if top.visible:
                _draw_list.extend(visit(top))

        return _draw_list

    @staticmethod
    def _vao_bind_fn(domain):    # noqa: ANN001, ANN205
        def _bind_vao(_ctx) -> None:  # noqa: ANN001
            domain.bind_vao()

        return _bind_vao

    @staticmethod
    def _draw_bucket_fn(domain, buckets, mode_func):  # noqa: ANN001, ANN205
        def _draw(_ctx) -> None:  # noqa: ANN001
            domain.draw_buckets(mode_func, buckets)

        return _draw

    def _optimize_draw_list(self, draw_list: list[tuple]) -> list[Callable]:
        """Turn a flattened (domain/mode/group) list into optimized callables.

        States that are equal (by __eq__) are treated as the same logical GPU state.
        Intermediate unset/set pairs for identical states are removed, preserving
        dependency ordering and teardown safety.
        """
        calls: list[Callable] = []
        active_states: dict[type, State] = {}  # (type, key) -> instance

        def _next_same_type_set(idx: int, state_type: type) -> None | State:
            for j in range(idx + 1, len(draw_list)):
                dom2, mode2, group2 = draw_list[j]
                if dom2 is None and mode2 == "set":
                    for s2 in group2._expanded_states:  # noqa: SLF001
                        if type(s2) is state_type:
                            return s2  # first same-type set we see in the future
            return None

        def flush_buckets() -> None:
            nonlocal current_buckets, last_mode, last_domain
            if not current_buckets:
                return

            calls.append(self._draw_bucket_fn(last_domain, list(current_buckets), geometry_map[last_mode]))
            current_buckets.clear()

        def _emit_set(_state: State) -> None:
            stype = type(_state)
            current = active_states.get(stype)

            # state is same
            if current == _state:
                return

            # state changed
            if current_buckets:
                flush_buckets()

            # unset previous
            if current and current.unsets_state:
                calls.append(current.unset_state)

            # set new state
            if _state.sets_state:
                calls.append(_state.set_state)

            active_states[stype] = _state

        def _emit_unset(_state: State, idx: int) -> None:
            stype = type(_state)
            current = active_states.get(stype)
            if current is None:
                return

            next_set = _next_same_type_set(idx, stype)
            if next_set == current:
                return  # will remain active

            # state is about to end
            flush_buckets()

            if current.unsets_state:
                calls.append(current.unset_state)
            active_states.pop(stype, None)

        last_domain = None
        last_mode = None
        current_buckets = []

        for i, (domain, mode, group) in enumerate(draw_list):
            if domain is None:
                # This is a state boundary. See if it *actually* changes state; if so, flush first.
                if mode == "set":
                    for s in group._expanded_states:
                        _emit_set(s)

                elif mode == "unset":
                    for s in reversed(group._expanded_states):
                        _emit_unset(s, i)

                continue

            # Drawable
            bucket = domain.get_drawable_bucket(group)
            if not bucket or bucket.is_empty:
                continue

            if last_domain is None:
                calls.append(self._vao_bind_fn(domain))
            elif domain != last_domain:
                # New VAO: flush previous batch, bind new VAO
                flush_buckets()
                calls.append(self._vao_bind_fn(domain))
            elif mode != last_mode:
                # Same VAO but different primitive mode: flush
                flush_buckets()

            current_buckets.append(bucket)
            last_domain = domain
            last_mode = mode

        # Final flush
        flush_buckets()

        return calls

    def _dump_draw_list_call_order(self, draw_list: list[Callable], include_dc: bool=True) -> None:
        import inspect

        print("=== DRAW ORDER ===")

        def fn_label(_fn: Callable) -> str:
            r = repr(_fn)
            if "unset_state" in r:
                return "UNSET"
            if "set_state" in r:
                return "SET"
            if "_vao_call_fn" in r:
                return "VAO"
            if "make_draw_buckets_fn" in r:
                return "DRAW"
            return "CALL"

        def fn_name(_fn: Callable) -> str:
            if inspect.ismethod(_fn):
                dc_info = f" ({_fn.__self__})" if include_dc else ""
                return f"{_fn.__self__.__class__.__name__}.{_fn.__name__}{dc_info}"
            if inspect.isfunction(_fn):
                return _fn.__name__
            return _fn.__class__.__name__

        for i, fn in enumerate(draw_list):
            label = fn_label(fn)
            name = fn_name(fn)
            print(f"{i:03d} ({label}): {name}")
        print("==================")

    def _set_draw_functions(self, draw_list: list) -> list[Callable]:
        """Takes a draw list and turns them into function calls.

        Does not optimize any states. All states are called.
        """
        calls: list[Callable] = []
        last_domain = None

        for i, (domain, mode, group) in enumerate(draw_list):
            if domain is None:
                # This is a state boundary. See if it *actually* changes state; if so, flush first.
                if mode == "set":
                    calls.extend([s.set_state for s in group._expanded_states if s.sets_state])

                elif mode == "unset":
                    calls.extend(reversed([s.unset_state for s in group._expanded_states if s.unsets_state]))

                continue

            # Drawable
            bucket = domain.get_drawable_bucket(group)
            if not bucket or bucket.is_empty:
                continue

            if last_domain is None or domain != last_domain:
                calls.append(self._vao_bind_fn(domain))

            calls.append(self._draw_bucket_fn(domain, [bucket], geometry_map[mode]))
            last_domain = domain

        return calls

    def _dump_draw_list(self) -> None:
        def dump(group: Group, indent: str = '') -> None:
            print(indent, 'Begin group', group)
            for domain in self._domain_registry.values():
                if domain.has_bucket(group):
                    # Domain header
                    domain_info = repr(domain).split('@')[-1].replace('>', '')
                    print(f"{indent}  > Domain: {domain.__class__.__name__}@{domain_info}")

                    # Regions
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

    def _update_draw_list(self) -> None:
        if self._draw_list_dirty:
            draw_list = self._create_draw_list()
            if pyglet.options.optimize_states:
                self._draw_list = self._optimize_draw_list(draw_list)
            else:
                self._draw_list = self._set_draw_functions(draw_list)
            self._draw_list_dirty = False

    def draw(self) -> None:
        """Draw the batch."""
        self._update_draw_list()

        for func in self._draw_list:
            func(self._context)

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
