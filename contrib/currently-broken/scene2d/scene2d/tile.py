#!/usr/bin/env python

'''
Management of tile sets
=======================

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os
import xml.dom
import xml.dom.minidom

from scene2d.image import Image2d, Drawable
from resource import Resource, register_factory
from scene2d.drawable import *


@register_factory('tileset')
def tileset_factory(resource, tag):
    id = tag.getAttribute('id')
    properties = resource.handle_properties(tag)
    tileset = TileSet(id, properties)
    resource.add_resource(tileset.id, tileset)

    for child in tag.childNodes:
        if not hasattr(child, 'tagName'): continue
        id = child.getAttribute('id')
        offset = child.getAttribute('offset')
        if offset:
            offset = map(int, offset.split(','))
        else:
            offset = None
        properties = resource.handle_properties(child)
        image = child.getElementsByTagName('image')
        if image:
            image = resource.handle(image[0])
        else:
            image = None
        tile = Tile(id, properties, image, offset)
        resource.add_resource(id, tile)
        tileset[id] = tile

    return tileset


class Tile(Drawable):
    def __init__(self, id, properties, image, offset=None):
        super(Tile, self).__init__()
        self.id = id
        self.properties = properties
        self.image = image
        self.offset = offset

    def __repr__(self):
        return '<%s object at 0x%x id=%r offset=%r properties=%r>'%(
            self.__class__.__name__, id(self), self.id, self.offset,
                self.properties)

    def get_drawstyle(self):
        '''Use the image style as a basis and modify to move.
        '''
        style = self.image.get_style()
        if self.offset is not None:
            style = style.copy()
            x, y = self.offset
            style.x, style.y = x, y
        return style


class TileSet(dict):
    '''Contains a tile set loaded from a map file and optionally image(s).
    '''
    def __init__(self, id, properties):
        self.id = id
        self.properties = properties

    # We retain a cache of opened tilesets so that multiple maps may refer to
    # the same tileset and we don't waste resources by duplicating the
    # tilesets in memory.
    tilesets = {}

    tile_id = 0
    @classmethod
    def generate_id(cls):
        cls.tile_id += 1
        return str(cls.tile_id)

    def add(self, properties, image, id=None):
        '''Add a new Tile to this TileSet, generating a unique id if
        necessary.'''
        if id is None:
            id = self.generate_id()
        self[id] = Tile(id, properties, image)

    @classmethod
    def load_xml(cls, filename, id):
        '''Load the tileset from the XML in the specified file.

        Return a TileSet instance.
        '''
        return Resource.load(filename)[id]

