#!/usr/bin/env python

'''VERSION_1_0
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

import ctypes as _ctypes
from pyglet.GLU import get_function as _get_function

GLU_VERSION_1_1 = 1
GLU_VERSION_1_2 = 1
GLU_VERSION_1_3 = 1

# StringName
GLU_VERSION = 100800
GLU_EXTENSIONS = 100801

# ErrorCode
GLU_INVALID_ENUM = 100900
GLU_INVALID_VALUE = 100901
GLU_OUT_OF_MEMORY = 100902
GLU_INVALID_OPERATION = 100904

# NurbsDisplay
#      GLU_FILL
GLU_OUTLINE_POLYGON = 100240
GLU_OUTLINE_PATCH = 100241

# NurbsCallback
GLU_NURBS_ERROR = 100103
GLU_ERROR = 100103
GLU_NURBS_BEGIN = 100164
GLU_NURBS_BEGIN_EXT = 100164
GLU_NURBS_VERTEX = 100165
GLU_NURBS_VERTEX_EXT = 100165
GLU_NURBS_NORMAL = 100166
GLU_NURBS_NORMAL_EXT = 100166
GLU_NURBS_COLOR = 100167
GLU_NURBS_COLOR_EXT = 100167
GLU_NURBS_TEXTURE_COORD = 100168
GLU_NURBS_TEX_COORD_EXT = 100168
GLU_NURBS_END = 100169
GLU_NURBS_END_EXT = 100169
GLU_NURBS_BEGIN_DATA = 100170
GLU_NURBS_BEGIN_DATA_EXT = 100170
GLU_NURBS_VERTEX_DATA = 100171
GLU_NURBS_VERTEX_DATA_EXT = 100171
GLU_NURBS_NORMAL_DATA = 100172
GLU_NURBS_NORMAL_DATA_EXT = 100172
GLU_NURBS_COLOR_DATA = 100173
GLU_NURBS_COLOR_DATA_EXT = 100173
GLU_NURBS_TEXTURE_COORD_DATA = 100174
GLU_NURBS_TEX_COORD_DATA_EXT = 100174
GLU_NURBS_END_DATA = 100175
GLU_NURBS_END_DATA_EXT = 100175

# NurbsError
GLU_NURBS_ERROR1 = 100251
GLU_NURBS_ERROR2 = 100252
GLU_NURBS_ERROR3 = 100253
GLU_NURBS_ERROR4 = 100254
GLU_NURBS_ERROR5 = 100255
GLU_NURBS_ERROR6 = 100256
GLU_NURBS_ERROR7 = 100257
GLU_NURBS_ERROR8 = 100258
GLU_NURBS_ERROR9 = 100259
GLU_NURBS_ERROR10 = 100260
GLU_NURBS_ERROR11 = 100261
GLU_NURBS_ERROR12 = 100262
GLU_NURBS_ERROR13 = 100263
GLU_NURBS_ERROR14 = 100264
GLU_NURBS_ERROR15 = 100265
GLU_NURBS_ERROR16 = 100266
GLU_NURBS_ERROR17 = 100267
GLU_NURBS_ERROR18 = 100268
GLU_NURBS_ERROR19 = 100269
GLU_NURBS_ERROR20 = 100270
GLU_NURBS_ERROR21 = 100271
GLU_NURBS_ERROR22 = 100272
GLU_NURBS_ERROR23 = 100273
GLU_NURBS_ERROR24 = 100274
GLU_NURBS_ERROR25 = 100275
GLU_NURBS_ERROR26 = 100276
GLU_NURBS_ERROR27 = 100277
GLU_NURBS_ERROR28 = 100278
GLU_NURBS_ERROR29 = 100279
GLU_NURBS_ERROR30 = 100280
GLU_NURBS_ERROR31 = 100281
GLU_NURBS_ERROR32 = 100282
GLU_NURBS_ERROR33 = 100283
GLU_NURBS_ERROR34 = 100284
GLU_NURBS_ERROR35 = 100285
GLU_NURBS_ERROR36 = 100286
GLU_NURBS_ERROR37 = 100287

# NurbsProperty
GLU_AUTO_LOAD_MATRIX = 100200
GLU_CULLING = 100201
GLU_SAMPLING_TOLERANCE = 100203
GLU_DISPLAY_MODE = 100204
GLU_PARAMETRIC_TOLERANCE = 100202
GLU_SAMPLING_METHOD = 100205
GLU_U_STEP = 100206
GLU_V_STEP = 100207
GLU_NURBS_MODE = 100160
GLU_NURBS_MODE_EXT = 100160
GLU_NURBS_TESSELLATOR = 100161
GLU_NURBS_TESSELLATOR_EXT = 100161
GLU_NURBS_RENDERER = 100162
GLU_NURBS_RENDERER_EXT = 100162

# NurbsSampling
GLU_OBJECT_PARAMETRIC_ERROR = 100208
GLU_OBJECT_PARAMETRIC_ERROR_EXT = 100208
GLU_OBJECT_PATH_LENGTH = 100209
GLU_OBJECT_PATH_LENGTH_EXT = 100209
GLU_PATH_LENGTH = 100215
GLU_PARAMETRIC_ERROR = 100216
GLU_DOMAIN_DISTANCE = 100217

# NurbsTrim
GLU_MAP1_TRIM_2 = 100210
GLU_MAP1_TRIM_3 = 100211

# QuadricDrawStyle
GLU_POINT = 100010
GLU_LINE = 100011
GLU_FILL = 100012
GLU_SILHOUETTE = 100013

# QuadricCallback
#      GLU_ERROR

# QuadricNormal
GLU_SMOOTH = 100000
GLU_FLAT = 100001
GLU_NONE = 100002

# QuadricOrientation
GLU_OUTSIDE = 100020
GLU_INSIDE = 100021

# TessCallback
GLU_TESS_BEGIN = 100100
GLU_BEGIN = 100100
GLU_TESS_VERTEX = 100101
GLU_VERTEX = 100101
GLU_TESS_END = 100102
GLU_END = 100102
GLU_TESS_ERROR = 100103
GLU_TESS_EDGE_FLAG = 100104
GLU_EDGE_FLAG = 100104
GLU_TESS_COMBINE = 100105
GLU_TESS_BEGIN_DATA = 100106
GLU_TESS_VERTEX_DATA = 100107
GLU_TESS_END_DATA = 100108
GLU_TESS_ERROR_DATA = 100109
GLU_TESS_EDGE_FLAG_DATA = 100110
GLU_TESS_COMBINE_DATA = 100111

# TessContour
GLU_CW = 100120
GLU_CCW = 100121
GLU_INTERIOR = 100122
GLU_EXTERIOR = 100123
GLU_UNKNOWN = 100124

# TessProperty
GLU_TESS_WINDING_RULE = 100140
GLU_TESS_BOUNDARY_ONLY = 100141
GLU_TESS_TOLERANCE = 100142

# TessError
GLU_TESS_ERROR1 = 100151
GLU_TESS_ERROR2 = 100152
GLU_TESS_ERROR3 = 100153
GLU_TESS_ERROR4 = 100154
GLU_TESS_ERROR5 = 100155
GLU_TESS_ERROR6 = 100156
GLU_TESS_ERROR7 = 100157
GLU_TESS_ERROR8 = 100158
GLU_TESS_MISSING_BEGIN_POLYGON = 100151
GLU_TESS_MISSING_BEGIN_CONTOUR = 100152
GLU_TESS_MISSING_END_POLYGON = 100153
GLU_TESS_MISSING_END_CONTOUR = 100154
GLU_TESS_COORD_TOO_LARGE = 100155
GLU_TESS_NEED_COMBINE_CALLBACK = 100156

# TessWinding
GLU_TESS_WINDING_ODD = 100130
GLU_TESS_WINDING_NONZERO = 100131
GLU_TESS_WINDING_POSITIVE = 100132
GLU_TESS_WINDING_NEGATIVE = 100133
GLU_TESS_WINDING_ABS_GEQ_TWO = 100134

GLUfuncptr = _ctypes.CFUNCTYPE(None)

gluBeginCurve = _get_function('gluBeginCurve', [_ctypes.c_void_p], None)
gluBeginPolygon = _get_function('gluBeginPolygon', [_ctypes.c_void_p], None)
gluBeginSurface = _get_function('gluBeginSurface', [_ctypes.c_void_p], None)
gluBeginTrim = _get_function('gluBeginTrim', [_ctypes.c_void_p], None)
gluBuild1DMipmapLevels = _get_function('gluBuild1DMipmapLevels', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_void_p], _ctypes.c_int)
gluBuild1DMipmaps = _get_function('gluBuild1DMipmaps', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], _ctypes.c_int)
gluBuild2DMipmapLevels = _get_function('gluBuild2DMipmapLevels', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_void_p], _ctypes.c_int)
gluBuild2DMipmaps = _get_function('gluBuild2DMipmaps', [_ctypes.c_uint, _ctypes.c_int, _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint, _ctypes.c_uint, _ctypes.c_void_p], _ctypes.c_int)

gluCylinder = _get_function('gluCylinder', [_ctypes.c_void_p, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.c_int, _ctypes.c_int], None)
gluDeleteNurbsRenderer = _get_function('gluDeleteNurbsRenderer', [_ctypes.c_void_p], None)
gluDeleteQuadric = _get_function('gluDeleteQuadric', [_ctypes.c_void_p], None)
gluDeleteTess = _get_function('gluDeleteTess', [_ctypes.c_void_p], None)
gluDisk = _get_function('gluDisk', [_ctypes.c_void_p, _ctypes.c_double, _ctypes.c_double, _ctypes.c_int, _ctypes.c_int], None)
gluEndCurve = _get_function('gluEndCurve', [_ctypes.c_void_p], None)
gluEndPolygon = _get_function('gluEndPolygon', [_ctypes.c_void_p], None)
gluEndSurface = _get_function('gluEndSurface', [_ctypes.c_void_p], None)
gluEndTrim = _get_function('gluEndTrim', [_ctypes.c_void_p], None)
gluErrorString = _get_function('gluErrorString', [_ctypes.c_uint], _ctypes.c_char_p)
gluGetNurbsProperty = _get_function('gluGetNurbsProperty', [_ctypes.c_void_p, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_float)], None)
gluGetTessProperty = _get_function('gluGetTessProperty', [_ctypes.c_void_p, _ctypes.c_uint, _ctypes.POINTER(_ctypes.c_double)], None)
gluLoadSamplingMatrices = _get_function('gluLoadSamplingMatrices', [_ctypes.c_void_p, _ctypes.POINTER(_ctypes.c_float), _ctypes.POINTER(_ctypes.c_float), _ctypes.POINTER(_ctypes.c_int)], None)
gluLookAt = _get_function('gluLookAt', [_ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double], None)
gluNewNurbsRenderer = _get_function('gluNewNurbsRenderer', [], _ctypes.c_void_p)
gluNewQuadric = _get_function('gluNewQuadric', [], _ctypes.c_void_p)
gluNewTess = _get_function('gluNewTess', [], _ctypes.c_void_p)
gluNextContour = _get_function('gluNextContour', [_ctypes.c_void_p, _ctypes.c_uint], None)

gluNurbsCallbackDataEXT = _get_function('gluNurbsCallbackDataEXT', [_ctypes.c_void_p, _ctypes.c_void_p], None)
gluNurbsCurve = _get_function('gluNurbsCurve', [_ctypes.c_void_p, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_float), _ctypes.c_int, _ctypes.POINTER(_ctypes.c_float), _ctypes.c_int, _ctypes.c_uint], None)
gluNurbsProperty = _get_function('gluNurbsProperty', [_ctypes.c_void_p, _ctypes.c_uint, _ctypes.c_float], None)
gluNurbsSurface = _get_function('gluNurbsSurface', [_ctypes.c_void_p, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_float), _ctypes.c_int, _ctypes.POINTER(_ctypes.c_float), _ctypes.c_int, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_float), _ctypes.c_int, _ctypes.c_int, _ctypes.c_uint], None)
gluOrtho2D = _get_function('gluOrtho2D', [_ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double], None)
gluPartialDisk = _get_function('gluPartialDisk', [_ctypes.c_void_p, _ctypes.c_double, _ctypes.c_double, _ctypes.c_int, _ctypes.c_int, _ctypes.c_double, _ctypes.c_double], None)
gluPerspective = _get_function('gluPerspective', [_ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double], None)
gluPickMatrix = _get_function('gluPickMatrix', [_ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.POINTER(_ctypes.c_int)], None)
gluProject = _get_function('gluProject', [_ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.POINTER(_ctypes.c_double), _ctypes.POINTER(_ctypes.c_double), _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_double), _ctypes.POINTER(_ctypes.c_double), _ctypes.POINTER(_ctypes.c_double)], _ctypes.c_int)
gluPwlCurve = _get_function('gluPwlCurve', [_ctypes.c_void_p, _ctypes.c_int, _ctypes.POINTER(_ctypes.c_float), _ctypes.c_int, _ctypes.c_uint], None)
gluQuadricCallback = _get_function('gluQuadricCallback', [_ctypes.c_void_p, _ctypes.c_uint, GLUfuncptr], None)
gluQuadricDrawStyle = _get_function('gluQuadricDrawStyle', [_ctypes.c_void_p, _ctypes.c_uint], None)
gluQuadricNormals = _get_function('gluQuadricNormals', [_ctypes.c_void_p, _ctypes.c_uint], None)
gluQuadricOrientation = _get_function('gluQuadricOrientation', [_ctypes.c_void_p, _ctypes.c_uint], None)
gluQuadricTexture = _get_function('gluQuadricTexture', [_ctypes.c_void_p, _ctypes.c_ubyte], None)
gluSphere = _get_function('gluSphere', [_ctypes.c_void_p, _ctypes.c_double, _ctypes.c_int, _ctypes.c_int], None)
gluTessBeginContour = _get_function('gluTessBeginContour', [_ctypes.c_void_p], None)
gluTessBeginPolygon = _get_function('gluTessBeginPolygon', [_ctypes.c_void_p, _ctypes.c_void_p], None)
gluTessCallback = _get_function('gluTessCallback', [_ctypes.c_void_p, _ctypes.c_uint, GLUfuncptr], None)
gluTessEndContour = _get_function('gluTessEndContour', [_ctypes.c_void_p], None)
gluTessEndPolygon = _get_function('gluTessEndPolygon', [_ctypes.c_void_p], None)
gluTessNormal = _get_function('gluTessNormal', [_ctypes.c_void_p, _ctypes.c_double, _ctypes.c_double, _ctypes.c_double], None)
gluTessProperty = _get_function('gluTessProperty', [_ctypes.c_void_p, _ctypes.c_uint, _ctypes.c_double], None)
gluTessVertex = _get_function('gluTessVertex', [_ctypes.c_void_p, _ctypes.POINTER(_ctypes.c_double), _ctypes.c_void_p], None)
gluUnProject = _get_function('gluUnProject', [_ctypes.c_double, _ctypes.c_double, _ctypes.c_double, _ctypes.POINTER(_ctypes.c_double), _ctypes.POINTER(_ctypes.c_double), _ctypes.POINTER(_ctypes.c_int), _ctypes.POINTER(_ctypes.c_double), _ctypes.POINTER(_ctypes.c_double), _ctypes.POINTER(_ctypes.c_double)], _ctypes.c_int)
