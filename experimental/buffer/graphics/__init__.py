#!/usr/bin/python
# $Id:$

import ctypes

from pyglet.gl import *

# Local imports
import vertexbuffer
import vertexattribute
import vertexdomain

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
        assert data, 'No attribute formats given'

        if state is None:
            state = null_state
        
        # Batch state
        if state not in self.state_map:
            self._add_state(state)

        domain_map = self.state_map[state]

        # Split out attribute formats
        formats = []
        initial_arrays = []
        for i, format in enumerate(data):
            if isinstance(format, tuple):
                format, array = format
                initial_arrays.append((i, array))
            formats.append(format)
        formats = tuple(formats)

        # Find domain given formats, indices and mode
        key = (formats, mode, False)
        try:
            domain = domain_map[key]
        except KeyError:
            # Create domain
            domain = vertexdomain.create_domain(*formats)
            domain_map[key] = domain
            self._draw_list_dirty = True
            
        # Create vertex list and initialize
        vlist = domain.create(count)
        for i, array in initial_arrays:
            vlist.set_attribute_data(i, array)

        return vlist

    def add_indexed(self, mode, state, indices, *data):
        pass # TODO

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
        
    def draw(self):
        if self._draw_list_dirty:
            self._update_draw_list()

        for func in self._draw_list:
            func()

class AbstractState(object):
    def __init__(self, parent=None):
        self.parent = parent
        
    def set(self):
        pass

    def unset(self):
        pass

class NullState(AbstractState):
    pass

null_state = NullState()

class TextureState(AbstractState):
    def __init__(self, texture, parent=None):
        super(TextureState, self).__init__(parent)
        self.texture = texture

    def set(self):
        glEnable(self.texture.target)
        glBindTexture(self.texture.target, self.texture.id)

    def unset(self):
        glDisable(self.texture.target)
