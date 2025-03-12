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
    ('int8_t',  True,   0): 'c_int8',
    ('int16_t', True,   0): 'c_int16',
    ('int32_t', True,   0): 'c_int32',
    ('int64_t', True,   0): 'c_int64',
    ('uint8_t', True,   0): 'c_uint8',
    ('uint16_t',True,   0): 'c_uint16',
    ('uint32_t',True,   0): 'c_uint32',
    ('uint64_t',True,   0): 'c_uint64',
    ('wchar_t', True,   0): 'c_wchar',
    ('ptrdiff_t',True,  0): 'c_ptrdiff_t',  # Requires definition in preamble
}

reserved_names = ['None', 'True', 'False']

def get_ctypes_type(typ, declarator):
    signed = True
    typename = 'int'
    longs = 0
    t = None
    for specifier in typ.specifiers:
        if isinstance(specifier, StructTypeSpecifier):
            t = CtypesStruct(specifier)
        elif isinstance(specifier, EnumSpecifier):
            t = CtypesEnum(specifier)
        elif specifier == 'signed':
            signed = True
        elif specifier == 'unsigned':
            signed = False
        elif specifier == 'long':
            longs += 1
        else:
            typename = str(specifier)
    if not t:
        ctypes_name = ctypes_type_map.get((typename, signed, longs), typename)
        t = CtypesType(ctypes_name)

    while declarator and declarator.pointer:
        if declarator.parameters is not None:
            t = CtypesFunction(t, declarator.parameters)
        a = declarator.array
        while a:
            t = CtypesArray(t, a.size)
            a = a.array

        if type(t) == CtypesType and t.name == 'c_char':
            t = CtypesType('c_char_p')
        elif type(t) == CtypesType and t.name == 'c_wchar':
            t = CtypesType('c_wchar_p')
        else:
            t = CtypesPointer(t, declarator.qualifiers)
        declarator = declarator.pointer
    if declarator and declarator.parameters is not None:
        t = CtypesFunction(t, declarator.parameters)
    if declarator:
        a = declarator.array
        while a:
            t = CtypesArray(t, a.size)
            a = a.array
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

class CtypesTypeVisitor(object):
    def visit_struct(self, struct):
        pass

    def visit_enum(self, enum):
        pass

class CtypesType(object):
    def __init__(self, name):
        self.name = name

    def get_required_type_names(self):
        '''Return all type names defined or needed by this type'''
        return (self.name,)

    def visit(self, visitor):
        pass

    def __str__(self):
        return self.name

class CtypesPointer(CtypesType):
    def __init__(self, destination, qualifiers):
        self.destination = destination
        # ignore qualifiers, ctypes can't use them

    def get_required_type_names(self):
        if self.destination:
            return self.destination.get_required_type_names()
        else:
            return ()

    def visit(self, visitor):
        if self.destination:
            self.destination.visit(visitor)

    def __str__(self):
        return 'POINTER(%s)' % str(self.destination)

class CtypesArray(CtypesType):
    def __init__(self, base, count):
        self.base = base
        self.count = count
    
    def get_required_type_names(self):
        # XXX Could be sizeofs within count expression
        return self.base.get_required_type_names()
 
    def visit(self, visitor):
        # XXX Could be sizeofs within count expression
        self.base.visit(visitor)

    def __str__(self):
        if self.count is None:
            return 'POINTER(%s)' % str(self.base)
        if type(self.base) == CtypesArray:
            return '(%s) * %s' % (str(self.base), str(self.count))
        else:
            return '%s * %s' % (str(self.base), str(self.count))

class CtypesFunction(CtypesType):
    def __init__(self, restype, parameters):
        if parameters and parameters[-1] == '...':
            # XXX Hmm, how to handle VARARGS with ctypes?  For now,
            # drop it off (will cause errors).
            parameters = parameters[:-1]
            
        self.restype = restype

        # Don't allow POINTER(None) (c_void_p) as a restype... causes errors
        # when ctypes automagically returns it as an int.
        # Instead, convert to POINTER(c_void).  c_void is not a ctypes type,
        # you can make it any arbitrary type.
        if type(self.restype) == CtypesPointer and \
           type(self.restype.destination) == CtypesType and \
           self.restype.destination.name == 'None':
            self.restype = CtypesPointer(CtypesType('c_void'), ())

        self.argtypes = [remove_function_pointer(
                            get_ctypes_type(p.type, p.declarator)) \
                         for p in parameters]

    def get_required_type_names(self):
        lst = list(self.restype.get_required_type_names())
        for a in self.argtypes:
            lst += list(a.get_required_type_names())
        return lst

    def visit(self, visitor):
        self.restype.visit(visitor)
        for a in self.argtypes:
            a.visit(visitor)

    def __str__(self):
        return 'CFUNCTYPE(%s)' % ', '.join([str(self.restype)] + \
            [str(a) for a in self.argtypes])

last_tagnum = 0
def anonymous_struct_tag():
    global last_tagnum
    last_tagnum += 1
    return 'anon_%d' % last_tagnum

class CtypesStruct(CtypesType):
    def __init__(self, specifier):
        self.is_union = specifier.is_union
        self.tag = specifier.tag
        if not self.tag:
            self.tag = anonymous_struct_tag()

        if specifier.declarations:
            self.opaque = False
            self.members = []
            for declaration in specifier.declarations:
                t = get_ctypes_type(declaration.type, declaration.declarator)
                declarator = declaration.declarator
                if declarator is None:
                    # XXX TEMPORARY while struct with no typedef not filled in
                    return
                while declarator.pointer:
                    declarator = declarator.pointer
                name = declarator.identifier
                self.members.append((name, t))
        else:
            self.opaque = True
            self.members = []

    def get_required_type_names(self):
        lst = ['struct_%s' % self.tag]
        for m in self.members:
            lst += m[1].get_required_type_names()
        return lst

    def visit(self, visitor):
        visitor.visit_struct(self)

    def __str__(self):
        return 'struct_%s' % self.tag

last_tagnum = 0
def anonymous_enum_tag():
    global last_tagnum
    last_tagnum += 1
    return 'anon_%d' % last_tagnum

class CtypesEnum(CtypesType):
    def __init__(self, specifier):
        self.tag = specifier.tag
        if not self.tag:
            self.tag = anonymous_enum_tag()

        value = 0
        context = EvaluationContext()
        self.enumerators = []
        for e in specifier.enumerators:
            if e.expression:
                try:
                    value = int(e.expression.evaluate(context))
                except:
                    pass
            self.enumerators.append((e.name, value))
            value += 1

    def get_required_type_names(self):
        return []

    def visit(self, visitor):
        visitor.visit_enum(self)

    def __str__(self):
        return 'enum_%s' % self.tag

class CtypesParser(CParser):
    '''Parse a C file for declarations that can be used by ctypes.
    
    Subclass and override the handle_ctypes_* methods.
    '''
    def handle_define(self, name, value, filename, lineno):
        # Handle #define style of typedeffing.
        # XXX At the moment, just a hack for `int`, which is used by
        # Status and Bool in Xlib.h.  More complete functionality would
        # parse value as a type (back into cparser).
        if value == 'int':
            t = CtypesType('c_int')
            self.handle_ctypes_type_definition(
                name, t, filename, lineno)

    def handle_define_constant(self, name, value, filename, lineno):
        if name in reserved_names:
            name += '_'
        self.handle_ctypes_constant(name, value, filename, lineno)

    def handle_declaration(self, declaration, filename, lineno):
        t = get_ctypes_type(declaration.type, declaration.declarator)
        declarator = declaration.declarator
        if declarator is None:
            # XXX TEMPORARY while struct with no typedef not filled in
            return
        while declarator.pointer:
            declarator = declarator.pointer
        name = declarator.identifier
        if declaration.storage == 'typedef':
            self.handle_ctypes_type_definition(
                name, remove_function_pointer(t), filename, lineno)
        elif type(t) == CtypesFunction:
            self.handle_ctypes_function(
                name, t.restype, t.argtypes, filename, lineno)
        elif declaration.storage != 'static':
            self.handle_ctypes_variable(name, t, filename, lineno)

    # ctypes parser interface.  Override these methods in your subclass.

    def handle_ctypes_constant(self, name, value, filename, lineno):
        pass

    def handle_ctypes_type_definition(self, name, ctype, filename, lineno):
        pass

    def handle_ctypes_function(self, name, restype, argtypes, filename, lineno):
        pass

    def handle_ctypes_variable(self, name, ctype, filename, lineno):
        pass

