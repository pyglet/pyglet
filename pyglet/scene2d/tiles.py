#!/usr/bin/env python

'''
Management of tile sets
=======================

-----------------
Tileset Map Files
-----------------

XML files with the following structure:

<tileset width="" height="">
 <image filename="">
  <tile id="">
   <origin x="" y="" />
   <meta type="" value="" />
  </tile>
  ...
 </image>
 ...
 <tile id="">
  <meta name="" type="" value="" />
 </tile>
 ...
</tileset>
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os
import xml.dom
import xml.dom.minidom

from pyglet.scene2d.image import Image2d
from pyglet.resource import register_loader

@register_loader('tileset')
def tileset_factory(loader, tag):
    id = tag.getAttribute('id')
    properties = loader.handle_properties(tag)
    tileset = TileSet(id, properties)
    loader.add_resource(tileset.id, tileset)

    for child in tag.childNodes:
        if not hasattr(child, 'tagName'): continue
        id = child.getAttribute('id')
        properties = loader.handle_properties(child)
        image = child.getElementsByTagName('image')
        if image: image = loader.handle(image[0])
        else: image = None
        loader.add_resource(id, Tile(id, properties, image))

    return tileset

__all__ = ['Tile', 'TileSet']

class Tile(object):
    __slots__ = 'id meta image'.split()
    def __init__(self, id, meta, image):
        self.id = id
        self.meta = meta
        self.image = image

xml_to_python = {
    'str': str,
    'unicode': unicode,
    'int': int,
    'float': float,
    'bool': bool,
}

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

    def add(self, meta, image, id=None):
        '''Add a new Tile to this TileSet, generating a unique id if
        necessary.'''
        if id is None:
            id = self.generate_id()
        self[id] = Tile(id, meta, image)

    @classmethod
    def load_xml(cls, filename):
        '''Load the tileset from the XML in the specified file.

        '''

        # XXX hook into resource loading and specify XML format
        raise NotImplemented()

