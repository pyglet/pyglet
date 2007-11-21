#!/usr/bin/python
# $Id:$

import ctypes

from pyglet.gl import *

# Local imports
import vertexbuffer
import vertexattribute
import vertexdomain

def draw(mode, *data, **kwargs):
    '''Draw a primitive immediately.

    :Parameters:
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
    size = None

    glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
    #import pdb; pdb.set_trace()

    for format, array in data:
        attribute = vertexattribute.create_attribute(format)
        assert size is None or size == len(array) // attribute.count, \
            'Lengths of arrays are inconsistent, cannot determine number ' \
            'of vertices.'
        size = len(array) // attribute.count
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

