#!/usr/bin/python
# $Id:$

import ctypes

import pyglet
from pyglet.gl import *
from pyglet.graphics import vertexbuffer, vertexattribute, vertexdomain

_debug_graphics_batch = pyglet.options['debug_graphics_batch']

def draw(size, mode, *data):
    '''Draw a primitive immediately.

    :Parameters:
        `size` : int
            Number of vertices given
        `mode` : int
            OpenGL drawing mode, e.g. ``GL_TRIANGLES``
        `data` : (str, sequence)
            Tuple of format string and array data.  Any number of
            data items can be given, each providing data for a different
            vertex attribute.

    '''
    glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)

    for format, array in data:
        attribute = vertexattribute.create_attribute(format)
        assert size == len(array) // attribute.count, \
            'Data for %s is incorrect length' % format
        buffer = vertexbuffer.create_mappable_buffer(
            size * attribute.stride, vbo=False)

        attribute.set_region(buffer, 0, size, array)
        attribute.enable()
        attribute.set_pointer(buffer.ptr)

    glDrawArrays(mode, 0, size)
        
    glPopClientAttrib()

def draw_indexed(size, mode, indices, *data):
    '''Draw a primitive with indexed vertices immediately.

    :Parameters:
        `size` : int
            Number of vertices given
        `mode` : int
            OpenGL drawing mode, e.g. ``GL_TRIANGLES``
        `indices` : sequence of int
            Sequence of integers giving indices into the vertex arrays.
            If unspecified, the arrays are drawn in sequence.
        `data` : (str, sequence)
            Tuple of format string and array data.  Any number of
            data items can be given, each providing data for a different
            vertex attribute.

    '''
    glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)

    for format, array in data:
        attribute = vertexattribute.create_attribute(format)
        assert size == len(array) // attribute.count, \
            'Data for %s is incorrect length' % format
        buffer = vertexbuffer.create_mappable_buffer(
            size * attribute.stride, vbo=False)

        attribute.set_region(buffer, 0, size, data)
        attribute.enable()
        attribute.set_pointer(buffer.ptr)

    if size <= 0xff:
        index_type = GL_UNSIGNED_BYTE
        index_c_type = ctypes.c_ubyte
    elif size <= 0xffff:
        index_type = GL_UNSIGNED_SHORT
        index_c_type = ctypes.c_ushort
    else:
        index_type = GL_UNSIGNED_INT
        index_c_type = ctypes.c_uint

    index_array = (index_c_type * len(indices))(*indices)
    glDrawElements(mode, len(indices), index_type, index_array)
    
    glPopClientAttrib()

def _parse_data(data):
    '''Given a list of data items, returns (formats, initial_arrays).'''
    assert data, 'No attribute formats given'

    # Return tuple (formats, initial_arrays).
    formats = []
    initial_arrays = []
    for i, format in enumerate(data):
        if isinstance(format, tuple):
            format, array = format
            initial_arrays.append((i, array))
        formats.append(format)
    formats = tuple(formats)
    return formats, initial_arrays

def _get_default_batch():
    shared_object_space = get_current_context().object_space
    try:
        return shared_object_space.pyglet_graphics_default_batch
    except AttributeError:
        shared_object_space.pyglet_graphics_default_batch = Batch()
        return shared_object_space.pyglet_graphics_default_batch

def vertex_list(count, *data):
    # Note that mode=0 because the default batch is never drawn: vertex lists
    # returned from this function are drawn directly by the app.
    return _get_default_batch().add(count, 0, None, *data)

def vertex_list_indexed(count, indices, *data):
    # Note that mode=0 because the default batch is never drawn: vertex lists
    # returned from this function are drawn directly by the app.
    return _get_default_batch().add_indexed(count, 0, None, indices, *data)

class Batch(object):
    def __init__(self):
        # Mapping to find domain.  
        # group -> (attributes, mode, indexed) -> domain
        self.group_map = {}

        # Mapping of group to list of children.
        self.group_children = {}

        # List of top-level groups
        self.top_groups = []

        self._draw_list = []
        self._draw_list_dirty = False

    def add(self, count, mode, group, *data):
        formats, initial_arrays = _parse_data(data)
        domain = self._get_domain(False, mode, group, formats)
        domain.__formats = formats
            
        # Create vertex list and initialize
        vlist = domain.create(count)
        for i, array in initial_arrays:
            vlist.set_attribute_data(i, array)

        return vlist

    def add_indexed(self, count, mode, group, indices, *data):
        formats, initial_arrays = _parse_data(data)
        domain = self._get_domain(True, mode, group, formats)
            
        # Create vertex list and initialize
        vlist = domain.create(count, len(indices))
        start = vlist.start
        vlist.set_index_data(map(lambda i: i + start, indices))
        for i, array in initial_arrays:
            vlist.set_attribute_data(i, array)

        return vlist 

    def migrate(self, vertex_list, mode, group, batch):
        '''Migrate a vertex list to another batch and/or group.

        `vertex_list` and `mode` together identify the vertex list to migrate.
        `group` and `batch` are new owners of the vertex list after migration.  

        The results are undefined if `mode` is not correct or if `vertex_list`
        does not belong to this batch (they are not checked and will not
        necessarily throw an exception immediately).

        `batch` can remain unchanged if only a group change is desired.
        
        :Parameters:
            `vertex_list` : `VertexList`
                A vertex list currently belonging to this batch.
            `mode` : int
                The current GL drawing mode of the vertex list.
            `group` : `Group`
                The new group to migrate to.
            `batch` : `Batch`
                The batch to migrate to (or the current batch).

        '''
        formats = vertex_list.domain.__formats
        domain = batch._get_domain(False, mode, group, formats)
        vertex_list.migrate(domain)

    def _get_domain(self, indexed, mode, group, formats):
        if group is None:
            group = null_group
        
        # Batch group
        if group not in self.group_map:
            self._add_group(group)

        domain_map = self.group_map[group]

        # Find domain given formats, indices and mode
        key = (formats, mode, indexed)
        try:
            domain = domain_map[key]
        except KeyError:
            # Create domain
            if indexed:
                domain = vertexdomain.create_indexed_domain(*formats)
            else:
                domain = vertexdomain.create_domain(*formats)
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
        self._draw_list_dirty = True

    def _update_draw_list(self):
        # Visit group tree in preorder and create a list of bound methods
        # to call.
        draw_list = []

        def visit(group):
            draw_list.append(group.set_state)

            # Draw domains using this group
            domain_map = self.group_map[group]
            for (_, mode, _), domain in domain_map.items():
                draw_list.append(
                    (lambda d, m: lambda: d.draw(m))(domain, mode))

            # Sort and visit child groups of this group
            children = self.group_children.get(group)
            if children:
                children.sort()
                for child in children:
                    visit(child)

            draw_list.append(group.unset_state)

        self.top_groups.sort()
        for group in self.top_groups:
            visit(group)

        self._draw_list = draw_list
        self._draw_list_dirty = False

        if _debug_graphics_batch:
            self._dump_draw_list()

    def _dump_draw_list(self):
        def dump(group, indent=''):
            print indent, 'Begin group', group
            domain_map = self.group_map[group]
            for _, domain in domain_map.items():
                print indent, '  ', domain
            for child in self.group_children.get(group, ()):
                dump(child, indent + '  ')
            print indent, 'End group', group

        print 'Draw list for %r:' % self
        for group in self.top_groups:
            dump(group)
        
    def draw(self):
        if self._draw_list_dirty:
            self._update_draw_list()

        for func in self._draw_list:
            func()

    # TODO: remove?
    def draw_subset(self, vertex_lists):
        # Horrendously inefficient.
        def visit(group):
            group.set_state()

            # Draw domains using this group
            domain_map = self.group_map[group]
            for (_, mode, _), domain in domain_map.items():
                for list in vertex_lists:
                    if list.domain is domain:
                        list.draw(mode)

            # Sort and visit child groups of this group
            children = self.group_children.get(group)
            if children:
                children.sort()
                for child in children:
                    visit(child)

            group.unset_state()

        self.top_groups.sort()
        for group in self.top_groups:
            visit(group)

class AbstractGroup(object):
    def __init__(self, parent=None):
        self.parent = parent
        
    def set_state(self):
        pass

    def unset_state(self):
        pass

    def set_state_recursive(self):
        '''Set this group and its ancestry.

        Call this method if you are using a group in isolation: the
        parent groups will be called in top-down order, with this class's
        `set` being called last.
        '''
        if self.parent:
            self.parent.set_state_recursive()
        self.set_state()

    def unset_state_recursive(self):
        '''Unset this group and its ancestry.

        The inverse of `set_recursive`.
        '''
        group = self
        while group:
            group.unset_state_recursive()
            group = group.parent

class NullGroup(AbstractGroup):
    pass

null_group = NullGroup()

class TextureGroup(AbstractGroup):
    # Don't use this, create your own group classes that are more specific.
    # This is just an example.
    def __init__(self, texture, parent=None):
        super(TextureGroup, self).__init__(parent)
        self.texture = texture

    def set_state(self):
        glEnable(self.texture.target)
        glBindTexture(self.texture.target, self.texture.id)

    def unset_state(self):
        glDisable(self.texture.target)

    def __hash__(self):
        return hash((self.texture.target, self.texture.id, self.parent))

    def __eq__(self, other):
        return (self.texture.target == other.texture.target and
            self.texture.id == other.texture.id and
            self.parent == self.parent)

    def __repr__(self):
        return '%s(id=%d)' % (self.__class__.__name__, self.texture.id)

class OrderedGroup(AbstractGroup):
    # This can be useful as a top-level group, or as a superclass for other
    # groups that need to be ordered.
    #
    # As a top-level group it's useful because graphics can be composited in a
    # known order even if they don't know about each other or share any known
    # group.
    def __init__(self, order, parent=None):
        super(OrderedGroup, self).__init__(parent)
        self.order = order

    def __cmp__(self, other):
        if isinstance(other, OrderedGroup):
            return cmp(self.order, other.order)
        return -1

    def __eq__(self, other):
        return (self.__class__ is other.__class__ and
            self.order == other.order and
            self.parent == other.parent)

    def __hash__(self):
        return hash((self.order, self.parent))

    def __repr__(self):
        return '%s(%d)' % (self.__class__.__name__, self.order)
