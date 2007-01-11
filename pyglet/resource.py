
import os
import xml.dom
import xml.dom.minidom


xml_to_python = {
    'str': unicode,
    'int': int,
    'float': float,
    'bool': bool,
}



class ResourceLoader(object):

    cache = {}

    def __init__(self, filename, paths=None):
        self.filename = filename
        if paths is None:
            self.paths = []
        else:
            self.paths = paths

        self.resources = {}
        self.namespaces = {}        # map local name to filename
        dom = xml.dom.minidom.parse(filename)
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
                raise ValueError, 'Loop in XML files'
            return cls.cache[filename]

        cls.cache[filename] = cls.NOT_LOADED
        obj = cls(filename, paths)
        cls.cache[filename] = obj
        return obj

    def find_file(self, filename):
        if os.path.isabs(filename):
            return filename
        for path in self.paths:
            fn = os.path.join(path, filename)
            if os.path.exists(fn):
                return fn
        raise ValueError, 'File "%s" not found in any paths'%filename

    def load_resource(self, tag):
        for tag in tag.childNodes:
            self.handle(tag)

    def load_requires(self, tag):
        filename = self.find_file(tag.getAttribute('file'))
        # check opened resource files cache

        resource = ResourceLoader.load(filename)

        if tag.hasAttribute('namespace'):
            self.namespaces[tag.getAttribute('namespace')] = resource.file
        else:
            # copy over all the resources from the require'd file
            # last man standing wins
            self.resources.update(resource.resources)

    factories = {
        'resource': load_resource,
        'requires': load_requires,
    }
    @classmethod
    def add_factory(cls, name, factory):
        cls.factories[name] = factory

    def handle(self, tag):
        if not hasattr(tag, 'tagName'): return
        if not tag.hasAttribute('ref'):
            return self.factories[tag.tagName](self, tag)
        ref = tag.getAttribute('ref')
        return self.get_resource(ref)

    def add_resource(self, id, resource):
        self.resources[id] = resource
    def get_resource(self, ref):
        if ':' in ref:
            ns, ref = ref.split(':', 1)
            resources = self.cache[self.namespaces[ns]].resources
            return resources[ref]
        return self.resources[ref]

    @staticmethod
    def handle_properties(tag):
        properties = {}
        for tag in tag.getElementsByTagName('property'):
            name = tag.getAttribute('name')
            type = tag.getAttribute('type')
            value = tag.getAttribute('value')
            properties[name] = xml_to_python[type](value)
        return properties

def register_loader(name):
    def decorate(func):
        ResourceLoader.add_factory(name, func)
        return func
    return decorate

