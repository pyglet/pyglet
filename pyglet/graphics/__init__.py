#!/usr/bin/python
# $Id:$

import ctypes

import pyglet
from pyglet.gl import *
from pyglet.graphics import vertexbuffer, vertexattribute, vertexdomain

_debug_graphics_batch = pyglet.options['debug_graphics_batch']

# TODO: separate out draw_indexed
def draw(size, mode, *data, **kwargs):
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
        `indices` : sequence of int
            Optional array integers giving indices into the arrays.
            If unspecified, the arrays are drawn in sequence.

    '''
    indices = kwargs.get('indices')

    glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)

    for format, array in data:
        attribute = vertexattribute.create_attribute(format)
        assert size == len(array) // attribute.count, \
            'Data for %s is incorrect length' % format
        buffer = vertexbuffer.create_mappable_buffer(
            size * attribute.stride, vbo=False)

        # TODO set without creating region
        region = attribute.get_region(buffer, 0, size)
        region.array[:] = array

        attribute.enable()
        attribute.set_pointer(buffer.ptr)

    if indices is None:
        glDrawArrays(mode, 0, size)
    else:
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

def vertex_list(count, *data):
    formats, initial_arrays = _parse_data(data)
    domain = vertexdomain.create_domain(*formats)
    vlist = domain.create(count)
    for i, array in initial_arrays:
        vlist.set_attribute_data(i, array)
    return vlist

# TODO indexed_vertex_list

class Batch(object):
    def __init__(self):
        # Mapping to find domain.  
        # state -> (attributes, mode, indexed) -> domain
        self.state_map = {}

        # Mapping of state to list of children.
        self.state_children = {}

        # List of top-level states
        self.top_states = []

        self._draw_list = []
        self._draw_list_dirty = False

    def add(self, count, mode, state, *data):
        formats, initial_arrays = _parse_data(data)
        domain = self._get_domain(False, mode, state, formats)
        domain.__formats = formats
            
        # Create vertex list and initialize
        vlist = domain.create(count)
        for i, array in initial_arrays:
            vlist.set_attribute_data(i, array)

        return vlist

    def migrate(self, vertex_list, mode, state, batch):
        '''Migrate a vertex list to another batch and/or state.

        `vertex_list` and `mode` together identify the vertex list to migrate.
        `state` and `batch` are new owners of the vertex list after migration.  

        The results are undefined if `mode` is not correct or if `vertex_list`
        does not belong to this batch (they are not checked and will not
        necessarily throw an exception immediately).

        `batch` can remain unchanged if only a state change is desired.
        
        :Parameters:
            `vertex_list` : `VertexList`
                A vertex list currently belonging to this batch.
            `mode` : int
                The current GL drawing mode of the vertex list.
            `state` : `State`
                The new state to migrate to.
            `batch` : `Batch`
                The batch to migrate to (or the current batch).

        '''
        formats = vertex_list.domain.__formats
        domain = batch._get_domain(False, mode, state, formats)
        vertex_list.migrate(domain)

    def add_indexed(self, count, mode, state, indices, *data):
        formats, initial_arrays = _parse_data(data)
        domain = self._get_domain(True, mode, state, formats)
            
        # Create vertex list and initialize
        vlist = domain.create(count, len(indices))
        start = vlist.start
        vlist.set_index_data(map(lambda i: i + start, indices))
        for i, array in initial_arrays:
            vlist.set_attribute_data(i, array)

        return vlist 

    def _get_domain(self, indexed, mode, state, formats):
        if state is None:
            state = null_state
        
        # Batch state
        if state not in self.state_map:
            self._add_state(state)

        domain_map = self.state_map[state]

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

    def _add_state(self, state):
        self.state_map[state] = {}
        if state.parent is None:
            self.top_states.append(state)
        else:
            if state.parent not in self.state_map:
                self._add_state(state.parent)
            if state.parent not in self.state_children:
                self.state_children[state.parent] = []
            self.state_children[state.parent].append(state)
        self._draw_list_dirty = True

    def _update_draw_list(self):
        # Visit state tree in preorder and create a list of bound methods
        # to call.
        draw_list = []

        def visit(state):
            draw_list.append(state.set)

            # Draw domains using this state
            domain_map = self.state_map[state]
            for (_, mode, _), domain in domain_map.items():
                draw_list.append(
                    (lambda d, m: lambda: d.draw(m))(domain, mode))

            # Sort and visit child states of this state
            children = self.state_children.get(state)
            if children:
                children.sort()
                for child in children:
                    visit(child)

            draw_list.append(state.unset)

        self.top_states.sort()
        for state in self.top_states:
            visit(state)

        self._draw_list = draw_list
        self._draw_list_dirty = False

        if _debug_graphics_batch:
            self._dump_draw_list()

    def _dump_draw_list(self):
        def dump(state, indent=''):
            print indent, 'Begin state', state
            domain_map = self.state_map[state]
            for _, domain in domain_map.items():
                print indent, '  ', domain
            for child in self.state_children.get(state, ()):
                dump(child, indent + '  ')
            print indent, 'End state', state

        print 'Draw list for %r:' % self
        for state in self.top_states:
            dump(state)
        
    def draw(self):
        if self._draw_list_dirty:
            self._update_draw_list()

        for func in self._draw_list:
            func()

    # TODO: remove?
    def draw_subset(self, vertex_lists):
        # Horrendously inefficient.
        def visit(state):
            state.set()

            # Draw domains using this state
            domain_map = self.state_map[state]
            for (_, mode, _), domain in domain_map.items():
                for list in vertex_lists:
                    if list.domain is domain:
                        list.draw(mode)

            # Sort and visit child states of this state
            children = self.state_children.get(state)
            if children:
                children.sort()
                for child in children:
                    visit(child)

            state.unset()

        self.top_states.sort()
        for state in self.top_states:
            visit(state)

class AbstractState(object):
    def __init__(self, parent=None):
        self.parent = parent
        
    def set(self):
        pass

    def unset(self):
        pass

    def set_recursive(self):
        '''Set this state and its ancestry.

        Call this method if you are using a state in isolation: the
        parent states will be called in top-down order, with this class's
        `set` being called last.
        '''
        if self.parent:
            self.parent.set_recursive()
        self.set()

    def unset_recursive(self):
        '''Unset this state and its ancestry.

        The inverse of `set_recursive`.
        '''
        state = self
        while state:
            state.unset()
            state = state.parent

class NullState(AbstractState):
    pass

null_state = NullState()

class TextureState(AbstractState):
    # Don't use this, create your own state classes that are more specific.
    # This is just an example.
    def __init__(self, texture, parent=None):
        super(TextureState, self).__init__(parent)
        self.texture = texture

    def set(self):
        glEnable(self.texture.target)
        glBindTexture(self.texture.target, self.texture.id)

    def unset(self):
        glDisable(self.texture.target)

    def __hash__(self):
        return hash((self.texture.target, self.texture.id, self.parent))

    def __eq__(self, other):
        return (self.texture.target == other.texture.target and
            self.texture.id == other.texture.id and
            self.parent == self.parent)

    def __repr__(self):
        return '%s(id=%d)' % (self.__class__.__name__, self.texture.id)

class OrderedState(AbstractState):
    # This can be useful as a top-level state, or as a superclass for other
    # states that need to be ordered.
    #
    # As a top-level state it's useful because graphics can be composited in a
    # known order even if they don't know about each other or share any known
    # state.
    def __init__(self, order, parent=None):
        super(OrderedState, self).__init__(parent)
        self.order = order

    def __cmp__(self, other):
        if isinstance(other, OrderedState):
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
