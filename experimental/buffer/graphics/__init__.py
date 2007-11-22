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
    #import pdb; pdb.set_trace()

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

    def add(self, count, mode, state, *data):
        assert data, 'No attribute formats given'

        if state is None:
            state = null_state
        
        # Batch state
        if state not in self.state_map:
            self.state_map[state] = {}
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
            
        # Create vertex list and initialize
        vlist = domain.create(count)
        for i, array in initial_arrays:
            vlist.set_attribute_data(i, array)

        return vlist

    def add_indexed(self, mode, state, indices, *data):
        pass # TODO
        
    def draw(self):
        for state, domain_map in self.state_map.items():
            state.set()
            for (_, mode, _), domain in domain_map.items():
                domain.draw(mode)
            state.unset()

class AbstractState(object):
    def set(self):
        pass

    def unset(self):
        pass

class NullState(AbstractState):
    pass

null_state = NullState()

class TextureState(AbstractState):
    def __init__(self, texture):
        self.texture = texture

    def set(self):
        glEnable(self.texture.target)
        glBindTexture(self.texture.target, self.texture.id)

    def unset(self):
        glDisable(self.texture.target)
