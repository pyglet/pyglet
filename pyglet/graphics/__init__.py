"""Low-level graphics rendering and abstractions.

This module provides efficient abstractions over OpenGL objects, such as
Shaders and Buffers. It also provides classes for highly performant batched
rendering and grouping.

See the :ref:`guide_graphics` for details on how to use this graphics API.
"""

import ctypes
import weakref

import pyglet
from pyglet.gl import *
from pyglet.graphics import shader, vertexdomain
from pyglet.graphics.vertexarray import VertexArray
from pyglet.graphics.vertexbuffer import BufferObject

_debug_graphics_batch = pyglet.options['debug_graphics_batch']


def draw(size, mode, **data):
    """Draw a primitive immediately.

    :warning: This function is deprecated as of 2.0.4, and will be removed
              in the next release.

    :Parameters:
        `size` : int
            Number of vertices given
        `mode` : gl primitive type 
            OpenGL drawing mode, e.g. ``GL_TRIANGLES``, 
            avoiding quotes.
        `**data` : keyword arguments for passing vertex attribute data.
            The keyword should be the vertex attribute name, and the
            argument should be a tuple of (format, data). For example:
            `position=('f', array)`

    """
    # Create and bind a throwaway VAO
    vao_id = GLuint()
    glGenVertexArrays(1, vao_id)
    glBindVertexArray(vao_id)
    # Activate shader program:
    program = get_default_shader()
    program.use()

    buffers = []
    for name, (fmt, array) in data.items():
        location = program.attributes[name]['location']
        count = program.attributes[name]['count']
        gl_type = vertexdomain._gl_types[fmt[0]]
        normalize = 'n' in fmt
        attribute = shader.Attribute(name, location, count, gl_type, normalize)
        assert size == len(array) // attribute.count, 'Data for %s is incorrect length' % fmt

        buffer = BufferObject(size * attribute.stride)
        attribute.set_region(buffer, 0, size, array)
        attribute.enable()
        attribute.set_pointer(buffer.ptr)

        buffers.append(buffer)      # Don't garbage collect it.

    glDrawArrays(mode, 0, size)

    # Deactivate shader program:
    program.stop()
    # Discard everything after drawing:
    del buffers
    glBindVertexArray(0)
    glDeleteVertexArrays(1, vao_id)


def draw_indexed(size, mode, indices, **data):
    """Draw a primitive with indexed vertices immediately.

    :warning: This function is deprecated as of 2.0.4, and will be removed
              in the next release.

    :Parameters:
        `size` : int
            Number of vertices given
        `mode` : int
            OpenGL drawing mode, e.g. ``GL_TRIANGLES``
        `indices` : sequence of int
            Sequence of integers giving indices into the vertex list.
        `**data` : keyword arguments for passing vertex attribute data.
            The keyword should be the vertex attribute name, and the
            argument should be a tuple of (format, data). For example:
            `position=('f', array)`

    """
    # Create and bind a throwaway VAO
    vao_id = GLuint()
    glGenVertexArrays(1, vao_id)
    glBindVertexArray(vao_id)
    # Activate shader program:
    program = get_default_shader()
    program.use()

    buffers = []
    for name, (fmt, array) in data.items():
        location = program.attributes[name]['location']
        count = program.attributes[name]['count']
        gl_type = vertexdomain._gl_types[fmt[0]]
        normalize = 'n' in fmt
        attribute = shader.Attribute(name, location, count, gl_type, normalize)
        assert size == len(array) // attribute.count, 'Data for %s is incorrect length' % fmt

        buffer = BufferObject(size * attribute.stride)
        attribute.set_region(buffer, 0, size, array)
        attribute.enable()
        attribute.set_pointer(buffer.ptr)
        buffers.append(buffer)

    if size <= 0xff:
        index_type = GL_UNSIGNED_BYTE
        index_c_type = ctypes.c_ubyte
    elif size <= 0xffff:
        index_type = GL_UNSIGNED_SHORT
        index_c_type = ctypes.c_ushort
    else:
        index_type = GL_UNSIGNED_INT
        index_c_type = ctypes.c_uint

    # With GL 3.3 vertex arrays indices needs to be in a buffer
    # bound to the ELEMENT_ARRAY slot
    index_array = (index_c_type * len(indices))(*indices)
    index_buffer = BufferObject(ctypes.sizeof(index_array))
    index_buffer.set_data(index_array)
    index_buffer.bind_to_index_buffer()

    glDrawElements(mode, len(indices), index_type, 0)
    glFlush()

    # Deactivate shader program:
    program.stop()
    # Discard everything after drawing:
    del buffers
    del index_buffer
    glBindVertexArray(0)
    glDeleteVertexArrays(1, vao_id)


# Default Shader source:

_vertex_source = """#version 330 core
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

_fragment_source = """#version 330 core
    in vec4 vertex_colors;
    in vec3 texture_coords;
    out vec4 final_colors;

    uniform sampler2D our_texture;

    void main()
    {
        final_colors = texture(our_texture, texture_coords.xy) + vertex_colors;
    }
"""


def get_default_batch():
    try:
        return pyglet.gl.current_context.pyglet_graphics_default_batch
    except AttributeError:
        pyglet.gl.current_context.pyglet_graphics_default_batch = Batch()
        return pyglet.gl.current_context.pyglet_graphics_default_batch


def get_default_group():
    try:
        return pyglet.gl.current_context.pyglet_graphics_default_group
    except AttributeError:
        pyglet.gl.current_context.pyglet_graphics_default_group = ShaderGroup(get_default_shader())
        return pyglet.gl.current_context.pyglet_graphics_default_group


def get_default_shader():
    try:
        return pyglet.gl.current_context.pyglet_graphics_default_shader
    except AttributeError:
        _default_vert_shader = pyglet.graphics.shader.Shader(_vertex_source, 'vertex')
        _default_frag_shader = pyglet.graphics.shader.Shader(_fragment_source, 'fragment')
        default_shader_program = pyglet.graphics.shader.ShaderProgram(_default_vert_shader, _default_frag_shader)
        pyglet.gl.current_context.pyglet_graphics_default_shader = default_shader_program
        return pyglet.gl.current_context.pyglet_graphics_default_shader


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

    def __init__(self):
        """Create a graphics batch."""
        # Mapping to find domain.  
        # group -> (attributes, mode, indexed) -> domain
        self.group_map = {}

        # Mapping of group to list of children.
        self.group_children = {}

        # List of top-level groups
        self.top_groups = []

        self._draw_list = []
        self._draw_list_dirty = False

        self._context = pyglet.gl.current_context

    def invalidate(self):
        """Force the batch to update the draw list.

        This method can be used to force the batch to re-compute the draw list
        when the ordering of groups has changed.

        .. versionadded:: 1.2
        """
        self._draw_list_dirty = True

    def migrate(self, vertex_list, mode, group, batch):
        """Migrate a vertex list to another batch and/or group.

        `vertex_list` and `mode` together identify the vertex list to migrate.
        `group` and `batch` are new owners of the vertex list after migration.  

        The results are undefined if `mode` is not correct or if `vertex_list`
        does not belong to this batch (they are not checked and will not
        necessarily throw an exception immediately).

        `batch` can remain unchanged if only a group change is desired.
        
        :Parameters:
            `vertex_list` : `~pyglet.graphics.vertexdomain.VertexList`
                A vertex list currently belonging to this batch.
            `mode` : int
                The current GL drawing mode of the vertex list.
            `group` : `~pyglet.graphics.Group`
                The new group to migrate to.
            `batch` : `~pyglet.graphics.Batch`
                The batch to migrate to (or the current batch).

        """
        program = vertex_list.domain.program
        attributes = vertex_list.domain.attribute_meta
        if isinstance(vertex_list, vertexdomain.IndexedVertexList):
            domain = batch.get_domain(True, mode, group, program, attributes)
        else:
            domain = batch.get_domain(False, mode, group, program, attributes)
        vertex_list.migrate(domain)

    def get_domain(self, indexed, mode, group, program, attributes):
        """Get, or create, the vertex domain corresponding to the given arguments."""
        if group is None:
            group = ShaderGroup(program=program)

        # Batch group
        if group not in self.group_map:
            self._add_group(group)

        # Find domain given formats, indices and mode
        domain_map = self.group_map[group]
        key = (indexed, mode, program, str(attributes))
        try:
            domain = domain_map[key]
        except KeyError:
            # Create domain
            if indexed:
                domain = vertexdomain.IndexedVertexDomain(program, attributes)
            else:
                domain = vertexdomain.VertexDomain(program, attributes)
            domain_map[key] = domain
            self._draw_list_dirty = True

        return domain

    def _add_group(self, group):
        self.group_map[group] = {}
        if group.parent is None:
            self.top_groups.append(group)
        else:
            if group.parent not in self.group_map:
                self._add_group(group.parent)
            if group.parent not in self.group_children:
                self.group_children[group.parent] = []
            self.group_children[group.parent].append(group)

        group._assigned_batches.add(self)
        self._draw_list_dirty = True

    def _update_draw_list(self):
        """Visit group tree in preorder and create a list of bound methods
        to call.
        """

        def visit(group):
            draw_list = []

            # Draw domains using this group
            domain_map = self.group_map[group]
            for (formats, mode, indexed, program_id), domain in list(domain_map.items()):
                # Remove unused domains from batch
                if domain.is_empty:
                    del domain_map[(formats, mode, indexed, program_id)]
                    continue
                draw_list.append((lambda d, m: lambda: d.draw(m))(domain, mode))

            # Sort and visit child groups of this group
            children = self.group_children.get(group)
            if children:
                children.sort()
                for child in list(children):
                    if child.visible:
                        draw_list.extend(visit(child))

            if children or domain_map:
                return [group.set_state] + draw_list + [group.unset_state]
            else:
                # Remove unused group from batch
                del self.group_map[group]
                group._assigned_batches.remove(self)
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
        for group in list(self.top_groups):
            if group.visible:
                self._draw_list.extend(visit(group))

        self._draw_list_dirty = False

        if _debug_graphics_batch:
            self._dump_draw_list()

    def _dump_draw_list(self):
        def dump(group, indent=''):
            print(indent, 'Begin group', group)
            domain_map = self.group_map[group]
            for _, domain in domain_map.items():
                print(indent, '  ', domain)
                for start, size in zip(*domain.allocator.get_allocated_regions()):
                    print(indent, '    ', 'Region %d size %d:' % (start, size))
                    for key, attribute in domain.attribute_names.items():
                        print(indent, '      ', end=' ')
                        try:
                            region = attribute.get_region(attribute.buffer, start, size)
                            print(key, region.array[:])
                        except:
                            print(key, '(unmappable)')
            for child in self.group_children.get(group, ()):
                dump(child, indent + '  ')
            print(indent, 'End group', group)

        print('Draw list for %r:' % self)
        for group in self.top_groups:
            dump(group)

    def draw(self):
        """Draw the batch."""

        if self._draw_list_dirty:
            self._update_draw_list()

        for func in self._draw_list:
            func()

    def draw_subset(self, vertex_lists):
        """Draw only some vertex lists in the batch.

        The use of this method is highly discouraged, as it is quite
        inefficient.  Usually an application can be redesigned so that batches
        can always be drawn in their entirety, using `draw`.

        The given vertex lists must belong to this batch; behaviour is
        undefined if this condition is not met.

        :Parameters:
            `vertex_lists` : sequence of `VertexList` or `IndexedVertexList`
                Vertex lists to draw.

        """

        # Horrendously inefficient.
        def visit(group):
            group.set_state()

            # Draw domains using this group
            domain_map = self.group_map[group]
            for (_, mode, _, _), domain in domain_map.items():
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
        for group in self.top_groups:
            if group.visible:
                visit(group)


class Group:
    """Group of common OpenGL state.

    `Group` provides extra control over how drawables are handled within a
    `Batch`. When a batch draws a drawable, it ensures its group's state is set;
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

    :Parameters:
        `order` : int
            Set the order to render above or below other Groups.
            Lower orders are drawn first.
        `parent` : `~pyglet.graphics.Group`
            Group to contain this Group; its state will be set before this
            Group's state.

    :Variables:
        `visible` : bool
            Determines whether this Group is visible in any of the Batches
            it is assigned to. If ``False``, objects in this Group will not
            be rendered.
        `batches` : list
            Read Only. A list of which Batches this Group is a part of.
    """
    def __init__(self, order=0, parent=None):

        self._order = order
        self.parent = parent
        self._visible = True
        self._assigned_batches = weakref.WeakSet()

    @property
    def order(self):
        return self._order

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, value):
        self._visible = value

        for batch in self._assigned_batches:
            batch.invalidate()

    @property
    def batches(self):
        return [batch for batch in self._assigned_batches]

    def __lt__(self, other):
        return self._order < other.order

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
                self._order == other.order and
                self.parent == other.parent)

    def __hash__(self):
        return hash((self._order, self.parent))

    def __repr__(self):
        return "{}(order={})".format(self.__class__.__name__, self._order)

    def set_state(self):
        """Apply the OpenGL state change.
        
        The default implementation does nothing."""
        pass

    def unset_state(self):
        """Repeal the OpenGL state change.
        
        The default implementation does nothing."""
        pass

    def set_state_recursive(self):
        """Set this group and its ancestry.

        Call this method if you are using a group in isolation: the
        parent groups will be called in top-down order, with this class's
        `set` being called last.
        """
        if self.parent:
            self.parent.set_state_recursive()
        self.set_state()

    def unset_state_recursive(self):
        """Unset this group and its ancestry.

        The inverse of `set_state_recursive`.
        """
        self.unset_state()
        if self.parent:
            self.parent.unset_state_recursive()


# Example Groups.

class ShaderGroup(Group):
    """A group that enables and binds a ShaderProgram.
    """

    def __init__(self, program, order=0, parent=None):
        super().__init__(order, parent)
        self.program = program

    def set_state(self):
        self.program.use()

    def unset_state(self):
        self.program.stop()

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
                self._order == other.order and
                self.program == other.program and
                self.parent == other.parent)

    def __hash__(self):
        return hash((self._order, self.parent, self.program))


class TextureGroup(Group):
    """A group that enables and binds a texture.

    TextureGroups are equal if their textures' targets and names are equal.
    """

    def __init__(self, texture, order=0, parent=None):
        """Create a texture group.

        :Parameters:
            `texture` : `~pyglet.image.Texture`
                Texture to bind.
            `order` : int
                Change the order to render above or below other Groups.
            `parent` : `~pyglet.graphics.Group`
                Parent group.
        """
        super().__init__(order, parent)
        self.texture = texture

    def set_state(self):
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(self.texture.target, self.texture.id)

    def __hash__(self):
        return hash((self.texture.target, self.texture.id, self.order, self.parent))

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
                self.texture.target == other.texture.target and
                self.texture.id == other.texture.id and
                self.order == other.order and
                self.parent == other.parent)

    def __repr__(self):
        return '%s(id=%d)' % (self.__class__.__name__, self.texture.id)
