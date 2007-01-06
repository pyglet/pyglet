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
    __slots__ = 'width height'.split()

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

        Note that the image tags are optional:

            <tileset width="" height="">
             <image filename="">
              <tile id="">
               <origin x="" y="" />
               <meta name="" type="" value="" />
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

        if filename in cls.tilesets:
            return cls.tilesets[filename]
        dirname = os.path.dirname(filename)

        dom = xml.dom.minidom.parse(filename)
        tileset = dom.documentElement

        obj = cls()
        obj.width = int(tileset.getAttribute('width'))
        obj.height = int(tileset.getAttribute('height'))
        for child in tileset.childNodes:
            if not hasattr(child, 'tagName'): continue
            if child.tagName == 'image':
                filename = child.getAttribute('filename')
                if not os.path.isabs(filename):
                    filename = os.path.join(dirname, filename)
                image = Image2d.load(filename)

                for child in child.childNodes:
                    if not hasattr(child, 'tagName'): continue
                    id = child.getAttribute('id')
                    origin = child.getElementsByTagName('origin')[0]
                    x, y = map(int, (origin.getAttribute('x'),
                        origin.getAttribute('y')))

                    subimage = image.subimage(x, y, obj.width, obj.height)

                    meta = {}
                    for tag in child.getElementsByTagName('meta'):
                        name = tag.getAttribute('name')
                        type = tag.getAttribute('type')
                        value = tag.getAttribute('value')
                        meta[name] = xml_to_python[type](value)
                    subimage.quad_list
                    obj[id] = Tile(id, meta, subimage)
            else:
                id = child.getAttribute('id')
                meta = {}
                for tag in child.getElementsByTagName('meta'):
                    name = tag.getAttribute('name')
                    type = tag.getAttribute('type')
                    value = tag.getAttribute('value')
                    meta[name] = xml_to_python[type](value)
                obj[id] = Tile(id, meta, None)
        dom.unlink()
        cls.tilesets[filename] = obj
        return obj

