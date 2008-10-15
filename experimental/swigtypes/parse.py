#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import gzip
import cPickle as marshal
import optparse
import os
import sys
import xml.sax

def parse_type(type_string):
    '''Get a tuple of the type components for a SWIG-formatted type.

    For example, given the type "p.f(p.struct _XExtData).int",
    return ('int', ('f', ('struct _XExtData', 'p'),), 'p')

    Qualifiers are ignored (removed).
    '''
    # Scan the type string left-to-right
    buf = ''

    stack = [()]

    def flush(): # buf = flush()
        if buf:
            stack[-1] = stack[-1] + (buf,)
        return ''
    def push():
        stack.append(())
    def pop():
        item = finalize(stack.pop())
        if item is not None:
            stack[-1] = stack[-1] + (item,)
    def finalize(item):
        assert type(item) is tuple
        if not item:
            # Empty tuple is dropped (empty param list)
            return
        elif item[0] == 'q':
            # Discard qualifiers 
            return
        
        # Reverse (puts pointers at end)
        item = item[::-1]

        # Reverse arguments of function
        if item[-1] == 'f':
            item = item[::-1]

            # Empty out (void) param list
            if item == ('f', ('void',)):
                item = ('f',)
        # Varargs encoding
        elif item[-1] == 'v':
            item = '...'
        # Array encoding
        elif item[-1] == 'a':
            try:
                item = ('a',) + tuple(int(j[0]) for j in item[-2::-1])
            except (TypeError, ValueError):
                # TODO arrays of dimension given by sizeof expression
                item = ('a', 0)

        # Remove one level of indirection for function types (CFUNCTYPE is
        # already a pointer)
        off = 0
        for i, j in enumerate(item):
            if type(j) is tuple and j and j[0] == 'f':
                item = item[:i+1+off] + item[i+2+off:]
                off -= 1
        return item
    
    for c in type_string:
        if c == '.':
            buf = flush()
        elif c == '(':
            push()              # Push param list
            buf = flush()
            push()              # Push item
        elif c == ',':
            buf = flush()
            pop()               # Pop item
            push()              # Push item
        elif c == ')':
            buf = flush()
            pop()               # Pop item
            pop()               # Pop param list
        else:
            buf += c
    flush()
            
    type_tuple = finalize(stack[0])
    return type_tuple

class SwigInterfaceHandler(object):
    def __init__(self):
        self.name = None
        self.cdecls = []
        self.constants = []

    def attribute(self, attrs):
        if attrs['name'] == 'name':
            self.name = str(attrs['value'])

    def typemap(self, attrs):
        return IgnoreElementHandler()

    def cdecl(self, attrs):
        handler = CDeclHandler(attrs)
        self.cdecls.append(handler)
        return handler

    def constant(self, attrs):
        handler = ConstantHandler(attrs)
        self.constants.append(handler)
        return handler

    def class_(self, attrs):
        handler = ClassHandler(attrs)
        self.cdecls.append(handler)
        return handler

    def classforward(self, attrs):
        handler = ClassForwardHandler(attrs)
        self.cdecls.append(handler)
        return handler

    def enum(self, attrs):
        handler = EnumHandler(attrs)
        self.cdecls.append(handler)
        return handler

    def get_map(self):
        map = {}
        for cdecl in self.cdecls:
            # ('typedef', type)
            if cdecl.kind == 'typedef':
                map[cdecl.name] = (cdecl.kind, cdecl.get_type(with_decl=True))
            # ('enum', items)
            elif cdecl.kind == 'enum':
                enum = (cdecl.kind, cdecl.get_items())
                map[cdecl.kind + ' ' + cdecl.name] = enum
                map[cdecl.get_tdname()] = enum
            # ('struct', variables)
            # ('union', variables)
            elif cdecl.kind in ('struct', 'union'):
                class_ = (cdecl.kind, cdecl.get_variables())
                map[cdecl.kind + ' ' + cdecl.name] = class_
                map[cdecl.get_tdname()] = class_
            # ('function', type)
            elif cdecl.kind == 'function':
                map[cdecl.name] = (cdecl.kind, cdecl.get_type(with_decl=True))
            # ('variable', type)
            elif cdecl.kind == 'variable':
                map[cdecl.name] = (cdecl.kind, cdecl.get_type())
            else:
                assert False, (cdecl.kind, cdecl.type, cdecl.name)

        # Constants: ('constant', value)
        for constant in self.constants:
            map[constant.name] = ('constant', constant.get_value())

        import pprint
        pprint.pprint(map)

        return map

class IgnoreElementHandler(object):
    pass

class ConstantHandler(object):
    name = None
    value = None
    type = None

    def __init__(self, attrs):
        pass

    def attribute(self, attrs):
        name = attrs['name']
        if name == 'name':
            self.name = str(attrs['value'])
        elif name == 'value':
            self.value = str(attrs['value'])
        elif name == 'type':
            self.type = str(attrs['value'])

    def get_value(self):
        if self.type in ('int', 'long'):
            # Yes, ugly and bad -- most C int constants can also be
            # parsed as Python expressions; e.g. "1L << 8".
            return int(eval(self.value))
        return self.value

class EnumHandler(object):
    name = None
    tdname = None
    kind = 'enum'
    unnamed = False

    def __init__(self, attrs):
        self.items = []

    def attribute(self, attrs):
        name = attrs['name']
        if name == 'name' and not self.unnamed:
            self.name = str(attrs['value'])
        elif name == 'unnamed':
            self.name = str(attrs['value'])
            self.unnamed = True
        elif name == 'tdname':
            self.tdname = str(attrs['value'])

    def enumitem(self, attrs):
        handler = EnumItemHandler(attrs)
        self.items.append(handler)
        return handler

    def get_items(self):
        items = []
        index = 0
        for item in self.items:
            try: 
                # TODO parse enumvalueex properly
                index = int(item.value)
            except ValueError:
                index += 1
            items.append((item.name, index))
        return tuple(items)

    def get_tdname(self):
        if self.tdname:
            return self.tdname
        else:
            return self.name

class EnumItemHandler(object):
    name = None
    value = None
    type = None
    
    def __init__(self, attrs):
        pass

    def attribute(self, attrs):
        name = attrs['name']
        if name == 'name':
            self.name = str(attrs['value'])
        elif name == 'unnamed':
            self.name = str(attrs['value'])
        elif name == 'enumvalueex':
            self.value = str(attrs['value'])
        elif name == 'type':
            self.type = str(attrs['value'])

    def get_value(self):
        if self.type in ('int', 'long'):
            # Yes, ugly and bad -- most C int constants can also be
            # parsed as Python expressions; e.g. "1L << 8".
            return int(eval(self.value))
        return self.value

class CDeclHandler(object):
    name = None
    kind = None
    type = None
    decl = ''
    params = None

    def __init__(self, attrs):
        pass

    def attribute(self, attrs):
        name = attrs['name']
        if name == 'name':
            self.name = str(attrs['value'])
        elif name == 'kind':
            self.kind = str(attrs['value'])
        elif name == 'type':
            self.type = str(attrs['value'])
        elif name == 'decl':
            self.decl = str(attrs['value'])

    def parmlist(self, attrs):
        self.params = []
        handler = ParmListHandler(attrs, self.params)
        return handler

    def get_params(self):
        # (type, ...)
        if self.params is None:
            return None
        return tuple(p.get_type() for p in self.params)

    def get_type(self, with_decl=False):
        if with_decl:
            return parse_type(self.decl + self.type)
        else:
            return parse_type(self.type)

    def __str__(self):
        if self.params:
            return self.name + \
                '(' + ', '.join(map(str, self.params)) + ') : ' + self.type
        else:
            return self.name + ' : ' + self.type

class ParmListHandler(object):
    def __init__(self, attrs, params):
        self.params = params
    
    def parm(self, attrs):
        param = ParmHandler(attrs)
        self.params.append(param)
        return param

class ParmHandler(object):
    name = ''
    type = None

    def __init__(self, attrs):
        pass

    def attribute(self, attrs):
        name = attrs['name']
        if name == 'name':
            self.name = str(attrs['value'])
        elif name == 'type':
            self.type = str(attrs['value'])

    def get_type(self):
        return parse_type(self.type)

    def __str__(self):
        return self.name + ' : ' + self.type

class ClassHandler(object):
    name = ''
    kind = None
    tdname = None
    unnamed = False

    def __init__(self, attrs):
        self.cdecls = []

    def attribute(self, attrs):
        name = attrs['name']
        if name == 'name' and not self.unnamed:
            self.name = str(attrs['value'])
        elif name == 'unnamed':
            self.name = str(attrs['value'])
            self.unnamed = True
        elif name == 'kind':
            self.kind = str(attrs['value'])
            assert self.kind in ('struct', 'union'), self.kind
        elif name == 'tdname':
            self.tdname = str(attrs['value'])

    def cdecl(self, attrs):
        handler = CDeclHandler(attrs)
        self.cdecls.append(handler)
        return handler

    def get_variables(self):
        # ((name, type), ...)
        return tuple((cdecl.name,  cdecl.get_type(with_decl=True)) 
                     for cdecl in self.cdecls if cdecl.kind == 'variable')

    def get_tdname(self):
        if self.tdname:
            return self.tdname
        else:
            return self.name

class ClassForwardHandler(object):
    name = ''
    kind = None
    tdname = None

    def __init__(self, attrs):
        pass

    def attribute(self, attrs):
        name = attrs['name']
        if name == 'name':
            self.name = str(attrs['value'])
        elif name == 'kind':
            self.kind = str(attrs['value'])
            assert self.kind in ('struct', 'union'), self.kind
        elif name == 'tdname':
            self.tdname = str(attrs['value'])

    def get_variables(self):
        return ()

    def get_tdname(self):
        if self.tdname:
            return self.tdname
        else:
            return self.name

class FFIContentHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.swig_interface_handler = SwigInterfaceHandler()
        self.stack = [self.swig_interface_handler]

    def startElement(self, name, attrs):
        if name == 'class':
            name = 'class_'

        top = self.stack[-1]
        func = getattr(top, name, None)
        if func:
            self.stack.append(func(attrs))
        else:
            self.stack.append(top)

    def endElement(self, name):
        del self.stack[-1]

class KeepGoingErrorHandler(xml.sax.handler.ErrorHandler):
    def error(self, exception):
        print exception

    def fatalError(self, exception):
        print exception

def parse(xml_filename, output_filename):
    handler = FFIContentHandler()
    error_handler = KeepGoingErrorHandler()
    xml.sax.parse(xml_filename, handler, error_handler)
    map = handler.swig_interface_handler.get_map()
    data = marshal.dumps(map)
    output_file = gzip.open(output_filename, 'w')
    output_file.write(data)
    output_file.close()

if __name__ == '__main__':
    usage = 'usage: %prog [options] <module.xml>'
    op = optparse.OptionParser(usage=usage)
    op.add_option('-o', '--output')
    (options, args) = op.parse_args(sys.argv[1:])

    if len(args) < 1:
        print >> sys.stderr, 'No input file given'
        sys.exit(1)

    xml_filename = args[0]
    module_name, _ = os.path.splitext(os.path.basename(xml_filename))
    ffi_filename = module_name + '.ffi'

    parse(xml_filename, ffi_filename)
