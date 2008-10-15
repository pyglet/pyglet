#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes as c
import gzip
import marshal
import sys

class AnonymousStruct(c.Structure):
    __slots__ = ()
    _fields_ = (
        ('foo', c.c_int),
    )

class AnonymousUnion(c.Union):
    __slots__ = ()
    _fields_ = (
        ('foo', c.c_int),
    )

class EnumType(type(c.c_int)):
    def __new__(metaclass, name, bases, dict):
        cls = type(c.c_int).__new__(metaclass, name, bases, dict)
        return cls

class Enum(c.c_int):
    __metaclass__ = EnumType
    _values_ = ()

    @classmethod
    def from_param(cls, obj):
        assert obj in cls._values_
        return cls(obj)

class FFILibrary(object):
    def __init__(self, ffi_file, lib):
        data = gzip.GzipFile(mode='r', fileobj=ffi_file).read()
        self.lib = lib
        self.map = marshal.loads(data)
        self.type_map = {}
        self.forward_map = {}
        self.builtin_type_map = {
            'void': None,
            'char': c.c_char,
            'signed char': c.c_char,
            'unsigned char': c.c_byte,
            'wchar_t': c.c_wchar,
            'short': c.c_short,
            'signed short': c.c_short,
            'unsigned short': c.c_ushort,
            'int': c.c_int,
            'signed int': c.c_int,
            'unsigned int': c.c_uint,
            'long': c.c_long,
            'signed long': c.c_long,
            'unsigned long': c.c_ulong,
            'long long': c.c_longlong,
            'signed long long': c.c_longlong,
            'unsigned long long': c.c_ulonglong,
            'float': c.c_float,
            'double': c.c_double,
            '...': c.c_int, # Sentinal for va_args list
        }

    def dump(self, name):
        print self.map[name]

    def __getattr__(self, name):
        kind, value = self.map[name]
        if kind == 'constant':
            result = value
        elif kind == 'typedef':
            result = self.get_type(value) 
        elif kind == 'enum':
            result = self.get_enum_type(name, value)
        elif kind == 'struct':
            result = self.get_class_type(name, value, c.Structure)
        elif kind == 'union':
            result = self.get_class_type(name, value, c.Union)
        elif kind == 'function':
            address = c.addressof(getattr(self.lib, name))
            result_type = self.get_type(value)
            result = result_type.from_address(address)
        elif kind == 'variable':
            address = c.addressof(getattr(self.lib, name))
            result_type = self.get_type(value)
            result = result_type.from_address(address)
        else:
            raise RuntimeError(kind)

        setattr(self, name, result)
        return result

    def get_type(self, parts):
        try:
            return self.type_map[parts]
        except KeyError:
            pass

        result = self.get_base_type(parts[0])
        for part in parts[1:]:
            if part == 'p':
                result = c.POINTER(result)
            elif type(part) is tuple:
                if part[0] == 'f':
                    result = self.get_function_type(result, part[1:])
                elif part[0] == 'a':
                    result = self.get_array_type(result, part[1:])
                else:
                    raise RuntimeError(part)
            else:
                raise RuntimeError(part)

        self.type_map[parts] = result
        return result

    def get_base_type(self, name):
        try:
            return self.type_map[name]
        except KeyError:
            pass

        try:
            return self.builtin_type_map[name]
        except KeyError:
            pass

        try:
            return self.forward_map[name]
        except KeyError:
            pass

        try:
            kind, value = self.map[name]
        except KeyError:
            if name.startswith('struct '):
                return AnonymousStruct
            elif name.startswith('union '):
                return AnonymousUnion
            else:
                raise RuntimeError('FFI contains no type "%s"' % name)

        if kind == 'typedef':
            return self.get_type(value)
        elif kind == 'enum':
            return self.get_enum_type(name, value)
        elif kind == 'struct':
            return self.get_class_type(name, value, c.Structure)
        elif kind == 'union':
            return self.get_class_type(name, value, c.Union)
        else:
            raise RuntimeError(kind)

    def get_enum_type(self, name, items):
        class _FFIEnum(Enum):
            pass
        _FFIEnum.__name__ = name

        for key, value in items:
            setattr(_FFIEnum, key, value)
        _FFIEnum._values_ = tuple([value for key, value in items])

        return _FFIEnum

    def get_class_type(self, name, fields, base):
        slots = tuple(name for name, _ in fields)

        class _FFIStruct(base):
            __slots__ = slots
        _FFIStruct.__name__ = name

        self.forward_map[name] = _FFIStruct
        _FFIStruct._fields_ = tuple((name, self.get_type(type)) 
                                    for (name, type) in fields)
        del self.forward_map[name]
        return _FFIStruct

    def get_function_type(self, restype, params):
        params = map(self.get_type, params)
        return c.CFUNCTYPE(restype, *params)

    def get_array_type(self, element_type, dimensions):
        result = element_type
        # TODO is order reversed for multi-dim?
        for d in dimensions:
            result = element_type * d
        return result

if __name__ == '__main__':
    ffi_filename = sys.argv[1]
    libname = sys.argv[2]
    lib = FFILibrary(open(ffi_filename, 'rb'), c.cdll.LoadLibrary(libname))

    if len(sys.argv) > 3:
        lib.dump(sys.argv[3])
    else:
        for key in lib.map:
            print key, getattr(lib, key)
            try:
                getattr(lib, key)
            except AttributeError, e:
                print e

