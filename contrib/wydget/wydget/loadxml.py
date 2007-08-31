from xml.etree import ElementTree

class XMLLoadError(Exception):
    pass

xml_registry = {}

def fromFile(parent, file):
    '''Load a gui frame and any child elements from the XML file.

    The elements will be added as children on "parent" which may be any
    other widget or a GUI instance.
    '''
    try:
        element = ElementTree.parse(file).getroot()
    except Exception, error:
        raise XMLLoadError, '%s (%r)'%(error, file)
    assert element.tag == 'frame', 'XML root tag must be <frame>'
    return getConstructor(element.tag)(element, parent)

def fromString(parent, string):
    '''Load a gui frame and any child elements from the XML string.

    The elements will be added as children on "parent" which may be any
    other widget or a GUI instance.
    '''
    try:
        element = ElementTree.fromstring(string)
    except Exception, error:
        raise XMLLoadError, '%s (%r)'%(error, string)
    assert element.tag == 'frame', 'XML root tag must be <frame>'
    return getConstructor(element.tag)(element, parent)

def getConstructor(name):
    '''Wrap the constructor retrieval to present a nicer error message.
    '''
    try:
        return xml_registry[name].fromXML
    except KeyError:
        raise KeyError, 'No constructor for XML element %r'%name

def parseAttributes(element):
    '''Convert various XML element attribute strings into Python values.
    '''
    kw = {}
    for key, value in element.items():
        if key == 'class':
            value = tuple(value.split(' '))
            key = 'classes'
        elif key in ('is_exclusive', 'scrollable', 'is_visible', 'is_blended',
                'is_enabled', 'is_vertical', 'show_value', 'expand'):
            value = { 'true': True, 'false': False, }[value.lower()]
        kw[key] = value
    return kw

