from __future__ import annotations
import struct

import pyglet
from ctypes import POINTER, Structure, c_void_p, c_char_p, c_uint32, c_size_t, c_int, byref, c_int32

try:
    lib = pyglet.lib.load_library("spirv-cross-c-shared")
except ImportError:
    raise ImportError("spirv-cross-c-shared library not found.")

spvc_result = c_int
SPVC_SUCCESS = 0

# The SPIR-V is invalid. Should have been caught by validation ideally.
ERROR_INVALID_SPIRV = -1

# The SPIR-V might be valid or invalid, but SPIRV-Cross currently cannot correctly translate this to your target language.
ERROR_UNSUPPORTED_SPIRV = -2

# If for some reason we hit this, new or malloc failed.
ERROR_OUT_OF_MEMORY = -3

# Invalid API argument.
ERROR_INVALID_ARGUMENT = -4
ERROR_INTERNAL = -5

SPVC_ERROR_INT_MAX = 0x7fffffff


# The Parsed IR payload will be copied, and the handle can be reused to create other compiler instances.
SPVC_CAPTURE_MODE_COPY = 0

# The payload will now be owned by the compiler.
# parsed_ir should now be considered a dead blob and must not be used further.
# This is optimal for performance and should be the go-to option.
SPVC_CAPTURE_MODE_TAKE_OWNERSHIP = 1

spvc_backend = c_int
SPVC_BACKEND_NONE = 0
SPVC_BACKEND_GLSL = 1  # spirv_cross::CompilerGLSL
SPVC_BACKEND_HLSL = 2  #CompilerHLSL
SPVC_BACKEND_MSL = 3  # CompilerMSL
SPVC_BACKEND_CPP = 4  # CompilerCPP
SPVC_BACKEND_JSON = 5  # CompilerReflection
SPVC_BACKEND_INT_MAX = 0x7fffffff


# Structures (opaque to the c-library)
class spvc_context(c_void_p):
    pass

class spvc_parsed_ir(c_void_p):
    pass

class spvc_compiler(c_void_p):
    pass

class spvc_resources(c_void_p):
    pass

SpvExecutionModel = c_int

class spvc_entry_point(Structure):
    _fields_ = [
        ('execution_model', SpvExecutionModel),
        ('name', c_char_p),
    ]

SpvId = c_uint32

spvc_resource_type = c_int
spvc_type_id = SpvId
spvc_variable_id = SpvId  # SPIRVariable
spvc_constant_id = SpvId  # SPIRConstant

spvc_capture_mode = c_int

class spvc_reflected_resource(Structure):
    _fields_ = [
        ("id", spvc_variable_id),
        ("type_id", spvc_type_id),
        ("base_type_id", spvc_type_id),
        ("name", c_char_p),
    ]


spvc_context_create = lib.spvc_context_create
spvc_context_create.restype = spvc_result
spvc_context_create.argtypes = [POINTER(spvc_context)]

spvc_context_destroy = lib.spvc_context_destroy
spvc_context_destroy.restype = spvc_result
spvc_context_destroy.argtypes = [spvc_context]

spvc_context_release_allocations = lib.spvc_context_release_allocations
spvc_context_release_allocations.restype = None
spvc_context_release_allocations.argtypes = [spvc_context]

spvc_context_get_last_error_string = lib.spvc_context_get_last_error_string
spvc_context_get_last_error_string.restype = c_char_p
spvc_context_get_last_error_string.argtypes = [spvc_context]

spvc_context_parse_spirv = lib.spvc_context_parse_spirv
spvc_context_parse_spirv.restype = spvc_result
spvc_context_parse_spirv.argtypes = [spvc_context, POINTER(SpvId), c_size_t, POINTER(spvc_parsed_ir)]

spvc_context_create_compiler = lib.spvc_context_create_compiler
spvc_context_create_compiler.restype = spvc_result
spvc_context_create_compiler.argtypes = [spvc_context, spvc_backend, spvc_parsed_ir, spvc_capture_mode, POINTER(spvc_compiler)]

lib.spvc_compiler_create_shader_resources.restype = spvc_result
lib.spvc_compiler_create_shader_resources.argtypes = [spvc_compiler, POINTER(spvc_resources)]

lib.spvc_resources_get_resource_list_for_type.restype = spvc_result
lib.spvc_resources_get_resource_list_for_type.argtypes = [spvc_resources, spvc_resource_type, POINTER(POINTER(spvc_reflected_resource)), POINTER(c_size_t)]

lib.spvc_compiler_get_decoration.restype = c_uint32
lib.spvc_compiler_get_decoration.argtypes = [spvc_compiler, SpvId, c_int]

lib.spvc_compiler_get_name.restype = c_char_p
lib.spvc_compiler_get_name.argtypes = [spvc_compiler, c_uint32]

spvc_compiler_compile = lib.spvc_compiler_compile
spvc_compiler_compile.restype = spvc_result
spvc_compiler_compile.argtypes = [spvc_compiler, POINTER(c_char_p)]