#!/usr/bin/env python

'''
Support for loading XML resource files
======================================

This module provides the Resource class which loads XML resource files
which may contain scene2d image files, atlases, tile sets and maps.

---------------
Getting Started
---------------

Assuming the following XML file called "example.xml"::

    <?xml version="1.0"?>
    <resource>
      <require file="ground-tiles.xml" namespace="ground" />
     
      <rectmap id="level1">
       <column>
        <cell>
          <tile ref="ground:grass" />
        </cell>
        <cell>
          <tile ref="ground:house" />
          <property type="bool" name="secretobjective" value="True" />
        </cell>
       </column>
      </map>
    </resource>

You may load that resource and examine it::

  >>> r = Resource.load('example.xml')
  >>> r['level1']

XXX TBD


-----------------
XML file contents
-----------------

XML resource files must contain a document-level tag <resource>::

    <?xml version="1.0"?>
    <resource>
     ...
    </resource>

You may draw in other resource files by using the <require> tag:

    <require file="road-tiles.xml" />

This will load "road-tiles.xml" into the resource's namespace.
If you wish to avoid id clashes you may supply a namespace:

    <require file="road-tiles.xml" namespace="road" />

Other tags within <resource> are handled by factories. Standard factories
exist for:

<image file="" id="">
    Loads the file into a scene2d.Image2d object.

<imageatlas file="" [id="" size="x,y"]>
    Sets up an image atlas for child <image> tags to use. Child tags are of
    the form:

        <image offset="" id="" [size=""]>

    If the <imageatlas> tag does not provide a size attribute then all
    child <image> tags must provide one.

<tileset id="">
    Sets up a scene2d.TileSet object. Child tags are of the form:

       <tile id="">
         [<image ...>]
       </tile>

    The <image> tag is optional, this tiles may have only properties (or be
    completely empty).

<rectmap id="" tile_size="" [origin=""]>
    Sets up a scene2d.RectMap object. Child tags are of the form:

       <column>
        <cell tile="" />
       </column>

Most tags may additionally have properties specified as:

   <property [type=""] name="" value="" />

Where type is one of "unicode", "int", "float" or "bool". The property will
be a unicode string by default if no type is specified.

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import os
import xml.dom
import xml.dom.minidom


# support for converting 
xml_to_python = {
    'unicode': unicode,
    'int': int,
    'float': float,
    'bool': bool,
}

class ResourceError(Exception):
    pass


class Resource(dict):

    cache = {}

    def __init__(self, filename, paths=None):
        self.filename = filename
        if paths is None:
            self.paths = []
        else:
            self.paths = paths

        self.namespaces = {}        # map local name to filename
        dom = xml.dom.minidom.parse(filename)
        tag = dom.documentElement
        if tag.tagName != 'resource':
            raise ResourceError('document is <%s> instead of <resource>'%
                tag.tagName)
        try:
            self.handle(dom.documentElement)
        finally:
            dom.unlink()

    NOT_LOADED = 'Not Loaded'
    @classmethod
    def load(cls, filename, paths=None):
        '''Load the resource from the XML in the specified file.
        '''
        # make sure we can find files relative to this one
        dirname = os.path.dirname(filename)
        if dirname:
            if paths:
                paths = list(paths)
            else:
                paths = []
            paths.append(dirname)

        if filename in cls.cache:
            if cls.cache[filename] is cls.NOT_LOADED:
                raise ResourceError('Loop in XML files loading "%s"'%filename)
            return cls.cache[filename]

        cls.cache[filename] = cls.NOT_LOADED
        obj = cls(filename, paths)
        cls.cache[filename] = obj
        return obj

    def find_file(self, filename):
        if os.path.isabs(filename):
            return filename
        if os.path.exists(filename):
            return filename
        for path in self.paths:
            fn = os.path.join(path, filename)
            if os.path.exists(fn):
                return fn
        raise ResourceError('File "%s" not found in any paths'%filename)

    def resource_factory(self, tag):
        for tag in tag.childNodes:
            self.handle(tag)

    def requires_factory(self, tag):
        filename = self.find_file(tag.getAttribute('file'))
        # check opened resource files cache

        resource = Resource.load(filename)

        ns = tag.getAttribute('namespace')
        if ns:
            self.namespaces[ns] = resource.file
        else:
            # copy over all the resources from the require'd file
            # last man standing wins
            self.update(resource)

    factories = {
        'resource': resource_factory,
        'requires': requires_factory,
    }
    @classmethod
    def add_factory(cls, name, factory):
        cls.factories[name] = factory

    def handle(self, tag):
        if not hasattr(tag, 'tagName'): return
        ref = tag.getAttribute('ref')
        if not ref:
            return self.factories[tag.tagName](self, tag)
        return self.get_resource(ref)

    def add_resource(self, id, resource):
        self[id] = resource
    def get_resource(self, ref):
        if ':' in ref:
            ns, ref = ref.split(':', 1)
            resources = self.cache[self.namespaces[ns]]
            return resources[ref]
        return self[ref]

    @staticmethod
    def handle_properties(tag):
        properties = {}
        for tag in tag.getElementsByTagName('property'):
            name = tag.getAttribute('name')
            type = tag.getAttribute('type') or 'unicode'
            value = tag.getAttribute('value')
            properties[name] = xml_to_python[type](value)
        return properties


def register_factory(name):
    def decorate(func):
        Resource.add_factory(name, func)
        return func
    return decorate

