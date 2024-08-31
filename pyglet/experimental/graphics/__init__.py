"""Low-level graphics rendering and abstractions.

This module provides efficient abstractions over OpenGL objects, such as
Shaders and Buffers. It also provides classes for highly performant batched
rendering and grouping.

See the :ref:`guide_graphics` for details on how to use this graphics API.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Sequence, Tuple

import pyglet
from pyglet.experimental.graphics import vertexdomain
from pyglet.graphics.vertexarray import VertexArray  # noqa: F401

if TYPE_CHECKING:
    from pyglet.graphics import Group
    from pyglet.graphics.shader import ShaderProgram
    from pyglet.graphics.vertexdomain import IndexedVertexList, VertexList

_debug_graphics_batch = pyglet.options['debug_graphics_batch']

_domain_class_map: dict[tuple[bool, bool], type[vertexdomain.VertexDomain]] = {
    # Indexed, Instanced : Domain
    (False, False): vertexdomain.VertexDomain,
    (True, False): vertexdomain.IndexedVertexDomain,
}

DomainKey = Tuple[bool, int, int, str]


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
    _draw_list: list[Callable]
    top_groups: list[Group]
    group_children: dict[Group, list[Group]]
    group_map: dict[Group, dict[DomainKey, vertexdomain.VertexDomain]]
    domain_map: dict[DomainKey: vertexdomain.VertexDomain | vertexdomain.IndexedVertexDomain]

    def __init__(self) -> None:
        """Create a graphics batch."""
        # Mapping to find domain.
        # group -> (attributes, mode, indexed) -> domain
        self.group_map = {}

        # Mapping of group to list of children.
        self.group_children = {}

        # All domains associated with the batch..
        self.domain_map = {}

        # List of top-level groups
        self.top_groups = []

        self._draw_list = []
        self._draw_list_dirty = False

        self._context = pyglet.gl.current_context

        self.current_states = []

    def invalidate(self) -> None:
        """Force the batch to update the draw list.

        This method can be used to force the batch to re-compute the draw list
        when the ordering of groups has changed.

        .. versionadded:: 1.2
        """
        self._draw_list_dirty = True

    def update_shader(self, vertex_list: VertexList | IndexedVertexList, mode: int, group: Group,
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

    def migrate(self, vertex_list: vertexdomain.VertexList | vertexdomain.IndexedVertexList, mode: int, group: Group, batch: Batch) -> None:
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

        # If it's the same domain, no need to dealloc it...
        if domain != vertex_list.domain:
            vertex_list.migrate(domain)
        else:
            # Update the group.
            vertex_list.update_group(group)

            # Updating group can potentially change draw order.
            self._draw_list_dirty = True

    def get_domain(self, indexed: bool, instanced: bool, mode: int, group: Group,
                   attributes: dict[str, Any]) -> (
            vertexdomain.VertexDomain | vertexdomain.IndexedVertexDomain):
        """Get, or create, the vertex domain corresponding to the given arguments."""
        key = (indexed, instanced, mode, str(attributes))

        # Check for existing domain
        if key in self.domain_map:
            domain = self.domain_map[key]
        else:
            # Create a new domain if none exists
            domain = _domain_class_map[(indexed, instanced)](attributes)
            self.domain_map[key] = domain
            self._draw_list_dirty = True

        # Ensure the group association is kept.
        if group not in self.group_map:
            self._add_group(group)

        domain_map = self.group_map[group]
        domain_map[key] = domain

        return domain

    def _add_group(self, group: Group) -> None:
        if group not in self.group_map:
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

    def _check_gl_state(self, group: Group) -> bool:
        """Return if the group state needs updating."""
        return any(gl_state not in self.current_states for gl_state in group.set_states)

    def pop_states(self, group: Group) -> None:
        for state in group.set_states:
            if state in self.current_states:
                self.current_states.remove(state)

    def add_states(self, group: Group) -> bool:
        requires_change = False
        for state in group.set_states:
            if state not in self.current_states:
                self.current_states.append(state)
                requires_change = True

        return requires_change

    def _create_draw_list(self) -> list:
        # print("-----------")

        def visit(current_group: Group) -> list:
            draw_list = []

            # Draw domains using this group
            domain_map = self.group_map.get(current_group, {})

            # Iterate over the domains associated with the current group
            for (indexed, instanced, mode, formats), current_domain in list(domain_map.items()):
                # Remove unused domains from batch
                if current_domain.is_empty:
                    del domain_map[(indexed, instanced, mode, formats)]
                    continue

                # If this group exists, has no vertices in the domain, skip it.
                if current_group in current_domain.group_vertex_ranges:
                    if not current_domain.group_vertex_ranges[current_group]:
                        continue
                else:
                    continue

                # If group exists, and has vertices, add a draw call.
                draw_list.append((current_domain, mode, current_group))

            # Sort and visit child groups of this group
            children = self.group_children.get(current_group)
            if children:
                children.sort()
                for child in list(children):
                    if child.visible:
                        draw_list.extend(visit(child))

            if children or domain_map:
                # if not domain_map:
                #     return [(None, 'set', current_group), *draw_list, (None, 'unset', current_group)]
                #
                # return draw_list
                return [(None, 'set', current_group), *draw_list, (None, 'unset', current_group)]

            # Clean up if the group is empty and has no children
            # Remove unused group from batch
            del self.group_map[current_group]
            current_group._assigned_batches.remove(self)  # noqa: SLF001
            if current_group.parent:
                self.group_children[current_group.parent].remove(current_group)
            try:
                del self.group_children[current_group]
            except KeyError:
                pass
            try:
                self.top_groups.remove(current_group)
            except ValueError:
                pass

            return []

        full_draw_list = []

        self.top_groups.sort()

        for top_group in list(self.top_groups):
            if top_group.visible:
                full_draw_list.extend(visit(top_group))

        return full_draw_list

    def _optimize_draw_list(self, draw_list: list) -> list[Callable]:
        draw_call_list = []
        contiguous_groups = []
        last_mode = None
        last_domain = None
        # print("draw list to optimize:", draw_list)
        # print("======")

        set_states = []
        set_groups = []
        # test_draw_stuff = []

        # Iterate through all calls to condense group calls.

        # Draw calls should be: bind vao -> state -> draw -> unset_state
        new_list = []
        was_added = []

        # Used to determine if a group is allowed to be unset. 'unset' is a marker for this.
        ready_to_unset = set()

        for domain, mode, group in draw_list:
            # print("----START", domain, mode, group)
            # Data: Group if no domain. If domain, mode.
            if not domain:
                # Mode is set/unset literal when domain is None
                if mode == 'set':
                    # If the state is already set or doesn't have states. Continue.
                    if not group.set_states or group in set_groups:
                        continue

                    state_added = False

                    # Check if any states in this group need to be added.
                    for gl_state in group.set_states:
                        if gl_state not in set_states:
                            state_added = True

                    # A new state needs to be added.
                    if state_added:
                        # Add all the new states.
                        set_states.extend(group.set_states)
                        # print("group set state:", group)
                        # print("group states", group.set_states)
                        # print("current states", set_states)
                        # print("old states", old_states)
                        groups_to_unset = []
                        # If the state gets added, check if the previous set group states needs to be unset.
                        for set_group in set_groups:
                            # print("CHECK GROUP", set_group)
                            for gl_state in set_group.set_states:
                                # If a previously set group state is not in any of the new ones, unset those.
                                if gl_state not in group.set_states:
                                    # print(gl_state, group.set_states)
                                    if set_group not in groups_to_unset and set_group in ready_to_unset:
                                        groups_to_unset.append(set_group)

                        for remove_group in reversed(groups_to_unset):
                            # print("-removing group", remove_group)
                            set_groups.remove(remove_group)
                            ready_to_unset.remove(remove_group)
                            new_list.append((None, 'unset', remove_group))
                            for gl_state in remove_group.set_states:
                                # print("Removing state", gl_state)
                                set_states.remove(gl_state)

                        # print("Groups removed", groups_to_unset)

                        # print("States after", set_states)
                        # print("State count after", len(set_states), len(group.set_states), len(set_states) == len(group.set_states))

                        set_groups.append(group)
                        was_added.append(group)
                        new_list.append((None, 'set', group))
                        # print("set groups total:", set_groups)

                elif mode == 'unset':
                    ready_to_unset.add(group)

                    if not group.set_states or group not in was_added:
                        continue

                    # Group was added, but no longer in there.
                    if group not in set_groups:
                        raise Exception("Not sure if this should even be a thing", group, set_groups)
                        new_list.append((None, 'unset', group))

            else:
                new_list.append((domain, mode, group))

        # Unset any remaining groups:
        for group in reversed(set_groups):
            new_list.append((None, 'unset', group))
            for state in group.set_states:
                set_states.remove(state)

        # At this point all the set_states should be empty if correct.
        # We don't need to clean up since it's local, but doing it for a sanity check. TODO: Move to test?
        assert len(set_states) == 0, f"Leftover states were found. Optimization failed. States: {set_states}"

        # print("---------", "States!", set_states)
        # print("Test list groups", new_list)

        draw_list = new_list

        # Collapse draw calls into contiguous render calls.
        for draw_domain, mode, group in draw_list:
            # print("<<<<<<<<< start consolidation", group, draw_domain, mode)
            # If the mode, domain are None, it's a group/parent with no draws.
            # However, it still may have a state that needs setting.
            if draw_domain is None:
                if mode == 'set':
                    draw_call_list.append(group.set_state)
                    # test_draw_stuff.append([f"set state of {group}"])
                elif mode == 'unset':
                    if contiguous_groups:
                        draw_call_list.append(
                            (lambda d, m, gs: lambda: d.draw_groups(m, gs))(last_domain, last_mode, contiguous_groups))

                        # test_draw_stuff.extend([f"DRAW: {contiguous_groups}"])
                        contiguous_groups = []

                    draw_call_list.append(group.unset_state)
                    # test_draw_stuff.extend([f"UNset state of {group}"])
                continue

            # If the domain or draw mode has changed, we need to break up the draw.
            if last_domain is None or (draw_domain == last_domain and mode == last_mode):
                # Check if the state of this group requires changing.
                if last_domain is None:
                    draw_call_list.append(draw_domain.bind)
                contiguous_groups.append(group)
            else:
                # Previous domain/mode is not compatible with current.
                draw_call_list.append(draw_domain.bind)
                if contiguous_groups:
                    # If we have contiguous groups, we need to now combine those
                    draw_call_list.append(
                        (lambda d, m, gs: lambda: d.draw_groups(m, gs))(last_domain, last_mode, contiguous_groups))

                    # test_draw_stuff.extend(["draw", contiguous_groups])

                # Reset contiguous groups for share state checks.
                contiguous_groups = [group]

            last_mode = mode
            last_domain = draw_domain

        # Draw the remaining contiguous groups
        if contiguous_groups:
            # test_draw_stuff.extend(["draw", contiguous_groups])
            draw_call_list.append(
                (lambda d, m, gs: lambda: d.draw_groups(m, gs))(last_domain, last_mode, contiguous_groups))

        # print("**** Optimized list:\n", test_draw_stuff)

        return draw_call_list

    def _update_draw_list(self) -> None:
        self._draw_list_dirty = False

        draw_list = self._create_draw_list()

        self._draw_list = self._optimize_draw_list(draw_list)

        if _debug_graphics_batch:
            self._dump_draw_list()

        # print("FINAL", [f"{func!s}" for func in self._draw_list])

        # print("GROUPS", draw_list)

    def _dump_draw_list(self, regions: bool = False) -> None:
        total_domains = 0

        def dump(current_group: Group, indent: str = '') -> None:
            nonlocal total_domains
            print(indent, 'Begin group', current_group, f"(order: {current_group.order})")
            current_domain_map = self.group_map[current_group]
            total_domains += len(current_domain_map)
            for current_domain in current_domain_map.values():
                print(indent, '  ', current_domain)
                for start, size in zip(*current_domain.allocator.get_allocated_regions()):
                    print(indent, '    ',
                          f'Region [start: {start}, size: {size}, groups: {len(current_domain.group_vertex_ranges)}]:')
                    for key, buffer in current_domain.attrib_name_buffers.items():
                        print(indent, '      ', end=' ')
                        try:
                            region = buffer.get_region(start, size)
                            print(key, region.array[:])
                        except Exception:
                            print(key, '(unmappable)')
                # for group, ranges in current_domain.group_vertex_ranges.items():
                #     parent_info = f" (parent: {group.parent})" if group.parent else ""
                #     print(indent, f'  Group {group}-{hex(id(group))}:{parent_info}')
                #     if regions:
                #         for range_start, range_size in ranges:
                #             print(indent, f'    Start: {range_start}, Size: {range_size}')
            for child in self.group_children.get(current_group, ()):
                dump(child, indent + '  ')
            print(indent, 'End group', current_group)

        print(f'Draw list for {self!r}:')
        for top_group in self.top_groups:
            dump(top_group)
        print(f'Total domains used: {total_domains}')
        print(f'Total draw list: {len(self._draw_list)}')

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


class SortedGroup(pyglet.graphics.Group):
    """Allows maintaining draw order of sprite list."""
    _domain: vertexdomain.VertexDomain | vertexdomain.IndexedVertexDomain | None

    def __init__(self, order: int = 0, parent: pyglet.graphics.Group | None = None) -> None:  # noqa: D107
        super().__init__(order, parent)
        self._dirty = False
        self._object_map = []
        self._domain = None

    def initialize(self) -> None:
        self.set_states = [pyglet.graphics.GLState(self)]

    def set_state(self) -> None:
        if self._dirty:
            for obj in self._object_map:
                vlist: vertexdomain.VertexList | vertexdomain.IndexedVertexList = obj._vertex_list
                self._domain.group_index_ranges[obj._group].remove((vlist.index_start, vlist.index_count))
                self._domain.group_index_ranges[obj._group].append((vlist.index_start, vlist.index_count))
                self._domain.group_vertex_ranges[obj._group].remove((vlist.start, vlist.count))
                self._domain.group_vertex_ranges[obj._group].append((vlist.start, vlist.count))

            self._dirty = False

    def sort_objects(self, key: Callable) -> None:
        sorted_objects = sorted(self._object_map, key=key)
        if sorted_objects != self._object_map:
            self._object_map = sorted_objects
            self._dirty = True

    def link_objects(self, pyglet_objects: list[Any]) -> None:
        assert pyglet_objects, "No objects provided."
        first_group = pyglet_objects[0]._group
        self._domain = pyglet_objects[0]._vertex_list.domain
        if not all(obj._group == first_group for obj in pyglet_objects):
            raise Exception("All objects do not belong to the same group")

        for pyglet_object in pyglet_objects:
            assert pyglet_object.group == self, "The pyglet object does not belong in this group."

            self._object_map.append(pyglet_object)

        self._dirty = True

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
                self._order == other.order and
                self.parent == other.parent)

    def __hash__(self) -> int:
        """This is an immutable return to establish the permanent identity of the object.

        This is used by Python with ``__eq__`` to determine if something is unique.

        For simplicity, the hash should be a tuple containing your unique identifiers of your Group.

        By default, this is (``order``, ``parent``).

        :see: ``__eq__`` function, both must be implemented.
        """
        return hash((self._order, self.parent))
