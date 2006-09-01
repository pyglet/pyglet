
"""EXT_framebuffer_object
http://oss.sgi.com/projects/ogl-sample/registry/EXT/framebuffer_object.txt
"""

import ctypes as _ctypes
from pyglet.GL import get_function as _get_function
from pyglet.GL import c_ptrdiff_t as _c_ptrdiff_t
GL_INVALID_FRAMEBUFFER_OPERATION_EXT = 0x0506
GL_MAX_RENDERBUFFER_SIZE_EXT = 0x84E8
GL_FRAMEBUFFER_BINDING_EXT = 0x8CA6
GL_RENDERBUFFER_BINDING_EXT = 0x8CA7
GL_FRAMEBUFFER_ATTACHMENT_OBJECT_TYPE_EXT = 0x8CD0
GL_FRAMEBUFFER_ATTACHMENT_OBJECT_NAME_EXT = 0x8CD1
GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_LEVEL_EXT = 0x8CD2
GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_CUBE_MAP_FACE_EXT = 0x8CD3
GL_FRAMEBUFFER_ATTACHMENT_TEXTURE_3D_ZOFFSET_EXT = 0x8CD4
GL_FRAMEBUFFER_COMPLETE_EXT = 0x8CD5
GL_FRAMEBUFFER_INCOMPLETE_ATTACHMENT_EXT = 0x8CD6
GL_FRAMEBUFFER_INCOMPLETE_MISSING_ATTACHMENT_EXT = 0x8CD7
GL_FRAMEBUFFER_INCOMPLETE_DIMENSIONS_EXT = 0x8CD9
GL_FRAMEBUFFER_INCOMPLETE_FORMATS_EXT = 0x8CDA
GL_FRAMEBUFFER_INCOMPLETE_DRAW_BUFFER_EXT = 0x8CDB
GL_FRAMEBUFFER_INCOMPLETE_READ_BUFFER_EXT = 0x8CDC
GL_FRAMEBUFFER_UNSUPPORTED_EXT = 0x8CDD
GL_MAX_COLOR_ATTACHMENTS_EXT = 0x8CDF
GL_COLOR_ATTACHMENT0_EXT = 0x8CE0
GL_COLOR_ATTACHMENT1_EXT = 0x8CE1
GL_COLOR_ATTACHMENT2_EXT = 0x8CE2
GL_COLOR_ATTACHMENT3_EXT = 0x8CE3
GL_COLOR_ATTACHMENT4_EXT = 0x8CE4
GL_COLOR_ATTACHMENT5_EXT = 0x8CE5
GL_COLOR_ATTACHMENT6_EXT = 0x8CE6
GL_COLOR_ATTACHMENT7_EXT = 0x8CE7
GL_COLOR_ATTACHMENT8_EXT = 0x8CE8
GL_COLOR_ATTACHMENT9_EXT = 0x8CE9
GL_COLOR_ATTACHMENT10_EXT = 0x8CEA
GL_COLOR_ATTACHMENT11_EXT = 0x8CEB
GL_COLOR_ATTACHMENT12_EXT = 0x8CEC
GL_COLOR_ATTACHMENT13_EXT = 0x8CED
GL_COLOR_ATTACHMENT14_EXT = 0x8CEE
GL_COLOR_ATTACHMENT15_EXT = 0x8CEF
GL_DEPTH_ATTACHMENT_EXT = 0x8D00
GL_STENCIL_ATTACHMENT_EXT = 0x8D20
GL_FRAMEBUFFER_EXT = 0x8D40
GL_RENDERBUFFER_EXT = 0x8D41
GL_RENDERBUFFER_WIDTH_EXT = 0x8D42
GL_RENDERBUFFER_HEIGHT_EXT = 0x8D43
GL_RENDERBUFFER_INTERNAL_FORMAT_EXT = 0x8D44
GL_STENCIL_INDEX1_EXT = 0x8D46
GL_STENCIL_INDEX4_EXT = 0x8D47
GL_STENCIL_INDEX8_EXT = 0x8D48
GL_STENCIL_INDEX16_EXT = 0x8D49
GL_RENDERBUFFER_RED_SIZE_EXT = 0x8D50
GL_RENDERBUFFER_GREEN_SIZE_EXT = 0x8D51
GL_RENDERBUFFER_BLUE_SIZE_EXT = 0x8D52
GL_RENDERBUFFER_ALPHA_SIZE_EXT = 0x8D53
GL_RENDERBUFFER_DEPTH_SIZE_EXT = 0x8D54
GL_RENDERBUFFER_STENCIL_SIZE_EXT = 0x8D55
glBindFramebufferEXT = _get_function('glBindFramebufferEXT', [_ctypes.c_uint, _ctypes.c_uint], None)
glBindRenderbufferEXT = _get_function('glBindRenderbufferEXT', [_ctypes.c_uint, _ctypes.c_uint], None)
glCheckFramebufferStatusEXT = _get_function('glCheckFramebufferStatusEXT', [_ctypes.c_uint], _ctypes.c_uint)
glDeleteFramebuffersEXT = _get_function('glDeleteFramebuffersEXT', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glDeleteRenderbuffersEXT = _get_function('glDeleteRenderbuffersEXT', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glFramebufferRenderbufferEXT = _get_function('glFramebufferRenderbufferEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint], None)
glFramebufferTexture1DEXT = _get_function('glFramebufferTexture1DEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int], None)
glFramebufferTexture2DEXT = _get_function('glFramebufferTexture2DEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int], None)
glFramebufferTexture3DEXT = _get_function('glFramebufferTexture3DEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int], None)
glGenFramebuffersEXT = _get_function('glGenFramebuffersEXT', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glGenRenderbuffersEXT = _get_function('glGenRenderbuffersEXT', [_ctypes.c_int, _ctypes.POINTER(_ctypes.c_uint)], None)
glGenerateMipmapEXT = _get_function('glGenerateMipmapEXT', [_ctypes.c_uint], None)
glGetFramebufferAttachmentParameterivEXT = _get_function('glGetFramebufferAttachmentParameterivEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glGetRenderbufferParameterivEXT = _get_function('glGetRenderbufferParameterivEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_int)], None)
glIsFramebufferEXT = _get_function('glIsFramebufferEXT', [_ctypes.c_uint], _ctypes.c_ubyte)
glIsRenderbufferEXT = _get_function('glIsRenderbufferEXT', [_ctypes.c_uint], _ctypes.c_ubyte)
glRenderbufferStorageEXT = _get_function('glRenderbufferStorageEXT', [_ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int], None)
