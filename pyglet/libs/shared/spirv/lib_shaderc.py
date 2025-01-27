from __future__ import annotations

import ctypes
from ctypes import c_char_p, c_size_t, c_void_p, POINTER

import pyglet

# Load the shaderc_shared.dll
lib_shaderc = pyglet.lib.load_library("shaderc_shared")

shaderc_shader_kind = ctypes.c_int32
shaderc_source_language_glsl = 0
shaderc_source_language_hlsl = 1

shaderc_vertex_shader = 0
shaderc_fragment_shader = 1
shaderc_compute_shader = 2
shaderc_geometry_shader = 3
shaderc_tess_control_shader = 4
shaderc_tess_evaluation_shader = 5

shaderc_optimization_level_zero = 0  # no optimization
shaderc_optimization_level_size = 1  # optimize towards reducing code size
shaderc_optimization_level_performance = 2  # optimize towards performance

class shaderc_compiler_t(c_void_p):
    pass

class shaderc_compilation_result(c_void_p):
    pass

class shaderc_compile_options(c_void_p):
    pass

# Define types for function arguments and return values
shaderc_compiler_initialize = lib_shaderc.shaderc_compiler_initialize
shaderc_compiler_initialize.restype = shaderc_compiler_t
shaderc_compiler_initialize.argtypes = []

shaderc_compiler_release = lib_shaderc.shaderc_compiler_release
shaderc_compiler_release.restype = None
shaderc_compiler_release.argtypes = [shaderc_compiler_t]

shaderc_compile_into_spv = lib_shaderc.shaderc_compile_into_spv
shaderc_compile_into_spv.restype = shaderc_compilation_result
shaderc_compile_into_spv.argtypes = [shaderc_compiler_t, c_char_p, c_size_t, shaderc_shader_kind, c_char_p, c_char_p,
                                     shaderc_compile_options]

shaderc_result_release = lib_shaderc.shaderc_result_release
shaderc_result_release.restype = None
shaderc_result_release.argtypes = [shaderc_compilation_result]

shaderc_result_get_bytes = lib_shaderc.shaderc_result_get_bytes
shaderc_result_get_bytes.restype = POINTER(ctypes.c_ubyte)
shaderc_result_get_bytes.argtypes = [c_void_p]

shaderc_result_get_length = lib_shaderc.shaderc_result_get_length
shaderc_result_get_length.restype = ctypes.c_size_t
shaderc_result_get_length.argtypes = [c_void_p]

shaderc_result_get_error_message = lib_shaderc.shaderc_result_get_error_message
shaderc_result_get_error_message.restype = c_char_p
shaderc_result_get_error_message.argtypes = [c_void_p]

shaderc_result_get_compilation_status = lib_shaderc.shaderc_result_get_compilation_status
shaderc_result_get_compilation_status.restype = shaderc_compilation_result
shaderc_result_get_compilation_status.argtypes = [shaderc_compilation_result]

# Options
shaderc_compile_options_initialize = lib_shaderc.shaderc_compile_options_initialize
shaderc_compile_options_initialize.restype = c_void_p
shaderc_compile_options_initialize.argtypes = []

shaderc_compile_options_set_target_spirv = lib_shaderc.shaderc_compile_options_set_target_spirv
shaderc_compile_options_set_target_spirv.argtypes = [shaderc_compile_options, ]
shaderc_compile_options_set_target_spirv.restype = None

shaderc_optimization_level = ctypes.c_int32
shaderc_compile_options_set_generate_debug_info = lib_shaderc.shaderc_compile_options_set_generate_debug_info
shaderc_compile_options_set_generate_debug_info.argtypes = [shaderc_compile_options]
shaderc_compile_options_set_generate_debug_info.restype = None

shaderc_compile_options_set_optimization_level = lib_shaderc.shaderc_compile_options_set_optimization_level
shaderc_compile_options_set_optimization_level.argtypes = [shaderc_compile_options, shaderc_optimization_level]
shaderc_compile_options_set_optimization_level.restype = None
