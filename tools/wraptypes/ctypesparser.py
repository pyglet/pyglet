#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

from cparser import *

ctypes_type_map = {
     # typename signed  longs
    ('void',    True,   0): 'None',
    ('int',     True,   0): 'c_int',
    ('int',     False,  0): 'c_uint',
    ('int',     True,   1): 'c_long',
    ('int',     False,  1): 'c_ulong',
    ('int',     True,   2): 'c_longlong',
    ('int',     False,  2): 'c_ulonglong',
    ('char',    True,   0): 'c_char',
    ('char',    False,  0): 'c_ubyte',
    ('short',   True,   0): 'c_short',
    ('short',   False,  0): 'c_ushort',
    ('float',   True,   0): 'c_float',
    ('double',  True,   0): 'c_double',
    ('size_t',  True,   0): 'c_size_t',
    ('int8_t',  True,   0): 'c_int8_t',
    ('int16_t', True,   0): 'c_int16_t',
    ('int32_t', True,   0): 'c_int32_t',
    ('int64_t', True,   0): 'c_int64_t',
    ('uint8_t', True,   0): 'c_uint8_t',
    ('uint16_t',True,   0): 'c_uint16_t',
    ('uint32_t',True,   0): 'c_uint32_t',
    ('uint64_t',True,   0): 'c_uint64_t',
}

def get_ctypes_type(typ, declarator):
    signed = True
    typename = 'int'
    longs = 0
    for specifier in typ.specifiers:
        if specifier == 'signed':
            signed = True
        elif specifier == 'unsigned':
            signed = False
        elif specifier == 'long':
            longs += 1
        else:
            typename = str(specifier)
    ctypes_name = ctypes_type_map.get((typename, signed, longs), typename)
    t = CtypesType(ctypes_name)

    while declarator and declarator.pointer:
        if declarator.parameters is not None:
            t = CtypesFunction(t, declarator.parameters)
        t = CtypesPointer(t, declarator.qualifiers)
        declarator = declarator.pointer
    if declarator and declarator.parameters is not None:
        t = CtypesFunction(t, declarator.parameters)
    return t
    
# Remove one level of indirection from funtion pointer; needed for typedefs
# and function parameters.
def remove_function_pointer(t):
    if type(t) == CtypesPointer and type(t.destination) == CtypesFunction:
        return t.destination
    elif type(t) == CtypesPointer:
        t.destination = remove_function_pointer(t.destination)
        return t
    else:
        return t

class CtypesType(object):
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

class CtypesPointer(CtypesType):
    def __init__(self, destination, qualifiers):
        self.destination = destination
        # ignore qualifiers, ctypes can't use them

    def __str__(self):
        return 'POINTER(%s)' % str(self.destination)

class CtypesFunction(CtypesType):
    def __init__(self, restype, parameters):
        self.restype = restype
        self.argtypes = [remove_function_pointer(
                            get_ctypes_type(p.type, p.declarator)) \
                         for p in parameters]

    def __str__(self):
        return 'CFUNCTYPE(%s)' % ', '.join([str(self.restype)] + \
            [str(a) for a in self.argtypes])

class CtypesParser(CParser):
    '''Parse a C file for declarations that can be used by ctypes.
    
    Subclass and override the handle_ctypes_* methods.
    '''
    def handle_define(self, name, value):
        if not value:
            return
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            value = value[1:-1].decode('string_escape')
        else:
            try:
                if value[:2] == '0x':
                    value = int(value[2:], 16)
                elif value[0] == '0':
                    value = int(value, 8)
                else:
                    value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    value = None
        if value:
            self.handle_ctypes_constant(name, value)

    def handle_declaration(self, declaration):
        t = get_ctypes_type(declaration.type, declaration.declarator)
        declarator = declaration.declarator
        while declarator.pointer:
            declarator = declarator.pointer
        name = declarator.identifier
        if declaration.storage == 'typedef':
            self.handle_ctypes_type_definition(name, remove_function_pointer(t))
        elif type(t) == CtypesFunction:
            self.handle_ctypes_function(name, t.restype, t.argtypes)
        elif declaration.storage != 'static':
            self.handle_ctypes_variable(name, t)

    # ctypes parser interface.  Override these methods in your subclass.

    def handle_ctypes_constant(self, name, value):
        pass

    def handle_ctypes_type_definition(self, name, ctype):
        pass

    def handle_ctypes_function(self, name, restype, argtypes):
        pass

    def handle_ctypes_variable(self, name, ctype):
        pass

