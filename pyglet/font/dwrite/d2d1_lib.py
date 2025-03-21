from __future__ import annotations

import os
import platform
from ctypes import (
    HRESULT,
    POINTER,
    Structure,
    c_void_p,
    c_wchar_p,
    windll,
)
from ctypes.wintypes import BOOL, FLOAT, UINT

from pyglet.font.dwrite.d2d1_types_lib import (
    D2D1_COLOR_F,
    D2D1_POINT_2F,
    D2D1_RECT_F,
    D2D1_SIZE_F,
    D2D1_SIZE_U,
    D2D_POINT_2F,
)
from pyglet.font.dwrite.dwrite_lib import (
    DWRITE_GLYPH_IMAGE_FORMATS,
    DWRITE_GLYPH_RUN,
    DWRITE_GLYPH_RUN_DESCRIPTION,
    DWRITE_MEASURING_MODE,
    IDWriteTextFormat,
    IDWriteTextLayout,
)
from pyglet.image.codecs.wincodec_lib import IWICBitmap, IWICBitmapSource
from pyglet.libs.win32 import c_void, com
from pyglet.libs.win32.types import BYTE, UINT32, UINT64

# --- Direct2D
try:
    d2d1 = "d2d1"

    # System32 and SysWOW64 folders are opposite perception in Windows x64.
    # System32 = x64 dll's | SysWOW64 = x86 dlls
    # By default ctypes only seems to look in system32 regardless of Python architecture, which has x64 dlls.
    if platform.architecture()[0] == "32bit" and platform.machine().endswith("64"):  # Machine is x64, Python is x86.
        d2d1 = os.path.join(os.environ["WINDIR"], "SysWOW64", "d2d1.dll")

    d2d_lib = windll.LoadLibrary(d2d1)
except OSError:
    # Doesn't exist? Should stop import of library.
    msg = "d2d1 Not Found"
    raise ImportError(msg)  # noqa: B904

D2D1_FACTORY_TYPE = UINT
D2D1_FACTORY_TYPE_SINGLE_THREADED = 0
D2D1_FACTORY_TYPE_MULTI_THREADED = 1

D2D1_COLOR_BITMAP_GLYPH_SNAP_OPTION = UINT
D2D1_COLOR_BITMAP_GLYPH_SNAP_OPTION_DEFAULT = 0
D2D1_COLOR_BITMAP_GLYPH_SNAP_OPTION_DISABLE = 1
D2D1_COLOR_BITMAP_GLYPH_SNAP_OPTION_FORCE_DWORD = 0xffffffff


D2D1_TEXT_ANTIALIAS_MODE = UINT
D2D1_TEXT_ANTIALIAS_MODE_DEFAULT = 0
D2D1_TEXT_ANTIALIAS_MODE_CLEARTYPE = 1
D2D1_TEXT_ANTIALIAS_MODE_GRAYSCALE = 2
D2D1_TEXT_ANTIALIAS_MODE_ALIASED = 3

D2D1_RENDER_TARGET_TYPE = UINT
D2D1_RENDER_TARGET_TYPE_DEFAULT = 0
D2D1_RENDER_TARGET_TYPE_SOFTWARE = 1
D2D1_RENDER_TARGET_TYPE_HARDWARE = 2

D2D1_FEATURE_LEVEL = UINT
D2D1_FEATURE_LEVEL_DEFAULT = 0

D2D1_RENDER_TARGET_USAGE = UINT
D2D1_RENDER_TARGET_USAGE_NONE = 0
D2D1_RENDER_TARGET_USAGE_FORCE_BITMAP_REMOTING = 1
D2D1_RENDER_TARGET_USAGE_GDI_COMPATIBLE = 2

DXGI_FORMAT = UINT
DXGI_FORMAT_UNKNOWN = 0

D2D1_ALPHA_MODE = UINT
D2D1_ALPHA_MODE_UNKNOWN = 0
D2D1_ALPHA_MODE_PREMULTIPLIED = 1
D2D1_ALPHA_MODE_STRAIGHT = 2
D2D1_ALPHA_MODE_IGNORE = 3

D2D1_DRAW_TEXT_OPTIONS = UINT
D2D1_DRAW_TEXT_OPTIONS_NO_SNAP = 0x00000001
D2D1_DRAW_TEXT_OPTIONS_CLIP = 0x00000002
D2D1_DRAW_TEXT_OPTIONS_ENABLE_COLOR_FONT = 0x00000004
D2D1_DRAW_TEXT_OPTIONS_DISABLE_COLOR_BITMAP_SNAPPING = 0x00000008
D2D1_DRAW_TEXT_OPTIONS_NONE = 0x00000000
D2D1_DRAW_TEXT_OPTIONS_FORCE_DWORD = 0xffffffff

DXGI_FORMAT_B8G8R8A8_UNORM = 87

D2D1_BITMAP_INTERPOLATION_MODE = UINT
D2D1_BITMAP_INTERPOLATION_MODE_NEAREST_NEIGHBOR = 0
D2D1_BITMAP_INTERPOLATION_MODE_LINEAR = 1
D2D1_BITMAP_INTERPOLATION_MODE_FORCE_DWORD = 0xffffffff

D2D1_BITMAP_OPTIONS = UINT
D2D1_BITMAP_OPTIONS_NONE = 0x00000000
D2D1_BITMAP_OPTIONS_TARGET = 0x00000001
D2D1_BITMAP_OPTIONS_CANNOT_DRAW = 0x00000002
D2D1_BITMAP_OPTIONS_CPU_READ = 0x00000004
D2D1_BITMAP_OPTIONS_GDI_COMPATIBLE = 0x00000008


D2D1CreateFactory = d2d_lib.D2D1CreateFactory
D2D1CreateFactory.restype = HRESULT
D2D1CreateFactory.argtypes = [D2D1_FACTORY_TYPE, com.REFIID, c_void_p, c_void_p]




class D2D1_PIXEL_FORMAT(Structure):
    _fields_ = (
        ("format", DXGI_FORMAT),
        ("alphaMode", D2D1_ALPHA_MODE),
    )


class D2D1_RENDER_TARGET_PROPERTIES(Structure):
    _fields_ = (
        ("type", D2D1_RENDER_TARGET_TYPE),
        ("pixelFormat", D2D1_PIXEL_FORMAT),
        ("dpiX", FLOAT),
        ("dpiY", FLOAT),
        ("usage", D2D1_RENDER_TARGET_USAGE),
        ("minLevel", D2D1_FEATURE_LEVEL),
    )

class D2D1_BITMAP_PROPERTIES(Structure):
    _fields_ = (
        ("pixelFormat", D2D1_PIXEL_FORMAT),
        ("dpiX", FLOAT),
        ("dpiY", FLOAT),
    )

ID2D1ColorContext = c_void_p
class D2D1_BITMAP_PROPERTIES1(Structure):
    _fields_ = (
        ("pixelFormat", D2D1_PIXEL_FORMAT),
        ("dpiX", FLOAT),
        ("dpiY", FLOAT),
        ("bitmapOptions", D2D1_BITMAP_OPTIONS),
        ("colorContext", ID2D1ColorContext),
    )

class ID2D1Resource(com.pIUnknown):
    _methods_ = [
        ("GetFactory",
         com.STDMETHOD()),
    ]


class ID2D1Brush(ID2D1Resource):
    _methods_ = [
        ("SetOpacity",
         com.STDMETHOD()),
        ("SetTransform",
         com.STDMETHOD()),
        ("GetOpacity",
         com.STDMETHOD()),
        ("GetTransform",
         com.STDMETHOD()),
    ]


class ID2D1SolidColorBrush(ID2D1Brush):
    _methods_ = [
        ("SetColor",
         com.METHOD(None, POINTER(D2D1_COLOR_F))),
        ("GetColor",
         com.STDMETHOD()),
    ]

D2D1_DEVICE_CONTEXT_OPTIONS = UINT
D2D1_DEVICE_CONTEXT_OPTIONS_NONE = 0
D2D1_DEVICE_CONTEXT_OPTIONS_ENABLE_MULTITHREADED_OPTIMIZATIONS = 1
D2D1_DEVICE_CONTEXT_OPTIONS_FORCE_DWORD = 0xffffffff

D2D1_TAG = UINT64

D2D1_MAP_OPTIONS = UINT
D2D1_MAP_OPTIONS_NONE = 0
D2D1_MAP_OPTIONS_READ = 1
D2D1_MAP_OPTIONS_WRITE = 2
D2D1_MAP_OPTIONS_DISCARD = 4

class D2D1_MAPPED_RECT(Structure):
    _fields_ = [
        ("pitch", UINT32),
        ("bits", POINTER(BYTE)),
    ]

class ID2D1Image(ID2D1Resource):
    _methods_ = []

class ID2D1Bitmap(ID2D1Image):
    _methods_ = [
        ("GetSize",
         com.METHOD(D2D1_SIZE_F)),
        ("GetPixelSize",
         com.METHOD(D2D1_SIZE_U)),
        ("GetPixelFormat",
         com.METHOD(D2D1_PIXEL_FORMAT)),
        ("GetDpi",
         com.METHOD(c_void, POINTER(FLOAT), POINTER(FLOAT))),
        ("CopyFromBitmap",
         com.STDMETHOD()),
        ("CopyFromRenderTarget",
         com.STDMETHOD()),
        ("CopyFromMemory",
         com.STDMETHOD()),
    ]

class ID2D1Bitmap1(ID2D1Bitmap):
    _methods_ = [
        ("GetColorContext",
         com.STDMETHOD()),
        ("GetOptions",
         com.METHOD(D2D1_BITMAP_OPTIONS)),
        ("GetSurface",
         com.STDMETHOD()),
        ("Map",
         com.STDMETHOD(D2D1_MAP_OPTIONS, POINTER(D2D1_MAPPED_RECT))),
        ("Unmap",
         com.STDMETHOD()),
    ]


class IDXGISurface(com.pIUnknown):
    ...

class ID2D1RenderTarget(ID2D1Resource):
    _methods_ = [
        ("CreateBitmap",
         com.STDMETHOD(D2D1_SIZE_U, c_void_p, UINT32, POINTER(D2D1_BITMAP_PROPERTIES), POINTER(ID2D1Bitmap))),
        ("CreateBitmapFromWicBitmap",
         com.STDMETHOD(IWICBitmapSource, POINTER(D2D1_BITMAP_PROPERTIES), POINTER(ID2D1Bitmap))),
        ("CreateSharedBitmap",
         com.STDMETHOD()),
        ("CreateBitmapBrush",
         com.STDMETHOD()),
        ("CreateSolidColorBrush",
         com.STDMETHOD(POINTER(D2D1_COLOR_F), c_void_p, POINTER(ID2D1SolidColorBrush))),
        ("CreateGradientStopCollection",
         com.STDMETHOD()),
        ("CreateLinearGradientBrush",
         com.STDMETHOD()),
        ("CreateRadialGradientBrush",
         com.STDMETHOD()),
        ("CreateCompatibleRenderTarget",
         com.STDMETHOD()),
        ("CreateLayer",
         com.STDMETHOD()),
        ("CreateMesh",
         com.STDMETHOD()),
        ("DrawLine",
         com.STDMETHOD()),
        ("DrawRectangle",
         com.STDMETHOD()),
        ("FillRectangle",
         com.STDMETHOD()),
        ("DrawRoundedRectangle",
         com.STDMETHOD()),
        ("FillRoundedRectangle",
         com.STDMETHOD()),
        ("DrawEllipse",
         com.STDMETHOD()),
        ("FillEllipse",
         com.STDMETHOD()),
        ("DrawGeometry",
         com.STDMETHOD()),
        ("FillGeometry",
         com.STDMETHOD()),
        ("FillMesh",
         com.STDMETHOD()),
        ("FillOpacityMask",
         com.METHOD(None, ID2D1Bitmap, ID2D1Brush, UINT, POINTER(D2D1_RECT_F), POINTER(D2D1_RECT_F))),
        ("DrawBitmap",
         com.STDMETHOD(ID2D1Bitmap, POINTER(D2D1_RECT_F), FLOAT, D2D1_BITMAP_INTERPOLATION_MODE, POINTER(D2D1_RECT_F))),
        ("DrawText",
         com.STDMETHOD()),
        ("DrawTextLayout",
         com.METHOD(c_void, D2D_POINT_2F, IDWriteTextLayout, ID2D1Brush, UINT32)),
        ("DrawGlyphRun",
         com.METHOD(c_void, D2D_POINT_2F, POINTER(DWRITE_GLYPH_RUN), ID2D1Brush, UINT32)),
        ("SetTransform",
         com.METHOD(c_void)),
        ("GetTransform",
         com.STDMETHOD()),
        ("SetAntialiasMode",
         com.METHOD(c_void, D2D1_TEXT_ANTIALIAS_MODE)),
        ("GetAntialiasMode",
         com.STDMETHOD()),
        ("SetTextAntialiasMode",
         com.METHOD(c_void, D2D1_TEXT_ANTIALIAS_MODE)),
        ("GetTextAntialiasMode",
         com.STDMETHOD()),
        ("SetTextRenderingParams",
         com.STDMETHOD()),
        ("GetTextRenderingParams",
         com.STDMETHOD()),
        ("SetTags",
         com.STDMETHOD()),
        ("GetTags",
         com.STDMETHOD()),
        ("PushLayer",
         com.STDMETHOD()),
        ("PopLayer",
         com.STDMETHOD()),
        ("Flush",
         com.STDMETHOD(POINTER(D2D1_TAG), POINTER(D2D1_TAG))),
        ("SaveDrawingState",
         com.STDMETHOD()),
        ("RestoreDrawingState",
         com.STDMETHOD()),
        ("PushAxisAlignedClip",
         com.STDMETHOD()),
        ("PopAxisAlignedClip",
         com.STDMETHOD()),
        ("Clear",
         com.METHOD(c_void, POINTER(D2D1_COLOR_F))),
        ("BeginDraw",
         com.METHOD(c_void)),
        ("EndDraw",
         com.STDMETHOD(POINTER(D2D1_TAG), POINTER(D2D1_TAG))),
        ("GetPixelFormat",
         com.STDMETHOD()),
        ("SetDpi",
         com.STDMETHOD(FLOAT, FLOAT)),
        ("GetDpi",
         com.STDMETHOD()),
        ("GetSize",
         com.STDMETHOD()),
        ("GetPixelSize",
         com.STDMETHOD()),
        ("GetMaximumBitmapSize",
         com.STDMETHOD()),
        ("IsSupported",
         com.METHOD(BOOL, POINTER(D2D1_RENDER_TARGET_PROPERTIES))),
    ]


class ID2D1DeviceContext(ID2D1RenderTarget):
    _methods_ = [
        ("CreateBitmap_Context",
         com.STDMETHOD(D2D1_SIZE_U, c_void_p, UINT32, POINTER(D2D1_BITMAP_PROPERTIES1), POINTER(ID2D1Bitmap1))),
        ("CreateBitmapFromWicBitmap_Context",
         com.STDMETHOD(IWICBitmapSource, POINTER(D2D1_BITMAP_PROPERTIES1), POINTER(ID2D1Bitmap1))),
        ("CreateColorContext",
         com.STDMETHOD()),
        ("CreateColorContextFromFilename",
         com.STDMETHOD()),
        ("CreateColorContextFromWicColorContext",
         com.STDMETHOD()),
        ("CreateBitmapFromDxgiSurface",
         com.STDMETHOD(IDXGISurface, POINTER(D2D1_BITMAP_PROPERTIES1), POINTER(ID2D1Bitmap1))),
        ("CreateEffect",
         com.STDMETHOD()),
        ("CreateGradientStopCollection_Context",
         com.STDMETHOD()),
        ("CreateImageBrush",
         com.STDMETHOD()),
        ("CreateBitmapBrush_Context",
         com.STDMETHOD()),
        ("CreateCommandList",
         com.STDMETHOD()),
        ("IsDxgiFormatSupported",
         com.STDMETHOD()),
        ("IsBufferPrecisionSupported",
         com.STDMETHOD()),
        ("GetImageLocalBounds",
         com.STDMETHOD()),
        ("GetImageWorldBounds",
         com.STDMETHOD()),
        ("GetGlyphRunWorldBounds",
         com.STDMETHOD()),
        ("GetDevice",
         com.STDMETHOD()),
        ("SetTarget",
         com.STDMETHOD(c_void_p)),
        ("GetTarget",
         com.METHOD(c_void, POINTER(c_void_p))),
        ("SetRenderingControls",
         com.STDMETHOD()),
        ("GetRenderingControls",
         com.STDMETHOD()),
        ("SetPrimitiveBlend",
         com.STDMETHOD()),
        ("GetPrimitiveBlend",
         com.STDMETHOD()),
        ("SetUnitMode",
         com.STDMETHOD()),
        ("GetUnitMode",
         com.STDMETHOD()),
        ("DrawGlyphRun_Context",
         com.METHOD(c_void, D2D_POINT_2F, POINTER(DWRITE_GLYPH_RUN), POINTER(DWRITE_GLYPH_RUN_DESCRIPTION), ID2D1Brush, UINT32)),
        ("DrawImage",
         com.STDMETHOD()),
        ("DrawGdiMetafile",
         com.STDMETHOD()),
        ("DrawBitmap_Context",
         com.STDMETHOD()),
        ("PushLayer_Context",
         com.STDMETHOD()),
        ("InvalidateEffectInputRectangle",
         com.STDMETHOD()),
        ("GetEffectInvalidRectangleCount",
         com.STDMETHOD()),
        ("GetEffectInvalidRectangles",
         com.STDMETHOD()),
        ("GetEffectRequiredInputRectangles",
         com.STDMETHOD()),
        ("FillOpacityMask_Context",
         com.METHOD(None, ID2D1Bitmap, ID2D1Brush, POINTER(D2D1_RECT_F), POINTER(D2D1_RECT_F))),
    ]

class ID2D1DeviceContext1(ID2D1DeviceContext):
    _methods_ = [
        ("CreateFilledGeometryRealization",
         com.STDMETHOD()),
        ("CreateStrokedGeometryRealization",
         com.STDMETHOD()),
        ("DrawGeometryRealization",
         com.STDMETHOD()),
    ]

class ID2D1DeviceContext2(ID2D1DeviceContext1):
    _methods_ = [
        ("CreateInk",
         com.STDMETHOD()),
        ("CreateInkStyle",
         com.STDMETHOD()),
        ("CreateGradientMesh",
         com.STDMETHOD()),
        ("CreateImageSourceFromWic",
         com.STDMETHOD()),
        ("CreateLookupTable3D",
         com.STDMETHOD()),
        ("CreateImageSourceFromDxgi",
         com.STDMETHOD()),
        ("GetGradientMeshWorldBounds",
         com.STDMETHOD()),
        ("DrawInk",
         com.STDMETHOD()),
        ("DrawGradientMesh",
         com.STDMETHOD()),
        ("DrawGdiMetafile2",
         com.STDMETHOD()),
        ("CreateTransformedImageSource",
         com.STDMETHOD()),
    ]

class ID2D1DeviceContext3(ID2D1DeviceContext2):
    _methods_ = [
        ("CreateSpriteBatch",
         com.STDMETHOD()),
        ("DrawSpriteBatch",
         com.STDMETHOD()),
    ]

ID2D1SvgGlyphStyle = c_void_p
class ID2D1DeviceContext4(ID2D1DeviceContext3):
    _methods_ = [
        ("CreateSvgGlyphStyle",
         com.STDMETHOD()),
        ("DrawText4",
         com.STDMETHOD(c_wchar_p, UINT32, IDWriteTextFormat, D2D1_RECT_F, ID2D1Brush, ID2D1SvgGlyphStyle, UINT32, D2D1_DRAW_TEXT_OPTIONS, DWRITE_MEASURING_MODE)),
        ("DrawTextLayout4",
         com.STDMETHOD(D2D1_POINT_2F, IDWriteTextLayout, ID2D1Brush, ID2D1SvgGlyphStyle, UINT32, D2D1_DRAW_TEXT_OPTIONS)),
        ("DrawColorBitmapGlyphRun",
         com.METHOD(c_void, DWRITE_GLYPH_IMAGE_FORMATS, D2D1_POINT_2F, POINTER(DWRITE_GLYPH_RUN), DWRITE_MEASURING_MODE, D2D1_COLOR_BITMAP_GLYPH_SNAP_OPTION)),
        ("DrawSvgGlyphRun",
         com.METHOD(c_void, D2D_POINT_2F, POINTER(DWRITE_GLYPH_RUN), ID2D1Brush, ID2D1SvgGlyphStyle, UINT32, DWRITE_MEASURING_MODE)),
        ("GetColorBitmapGlyphImage",
         com.STDMETHOD()),
        ("GetSvgGlyphImage",
         com.STDMETHOD()),
    ]





class ID2D1Device(ID2D1Resource):
    _methods_ = [
        ("CreateDeviceContext", com.STDMETHOD(D2D1_DEVICE_CONTEXT_OPTIONS, POINTER(ID2D1DeviceContext))),
        ("CreatePrintControl", com.STDMETHOD()),
        ("SetMaximumTextureMemory", com.STDMETHOD()),
        ("GetMaximumTextureMemory", com.STDMETHOD()),
        ("ClearResources", com.STDMETHOD()),
    ]

class ID2D1Device1(ID2D1Device):
    _methods_ = [
        ("GetRenderingPriority", com.STDMETHOD()),  # D2D1_RENDERING_PRIORITY GetRenderingPriority()
        ("SetRenderingPriority", com.STDMETHOD()),
        ("CreateDeviceContext1", com.STDMETHOD(D2D1_DEVICE_CONTEXT_OPTIONS, POINTER(ID2D1DeviceContext1))),
    ]

class ID2D1Device2(ID2D1Device1):
    _methods_ = [
        ("CreateDeviceContext2", com.STDMETHOD()),
        ("FlushDeviceContexts", com.STDMETHOD()),
        ("GetDxgiDevice", com.STDMETHOD()),
    ]

class ID2D1Device3(ID2D1Device2):
    _methods_ = [
        ("CreateDeviceContext3", com.STDMETHOD()),
    ]

class ID2D1Device4(ID2D1Device3):
    _methods_ = [
        ("CreateDeviceContext4", com.STDMETHOD(D2D1_DEVICE_CONTEXT_OPTIONS, POINTER(ID2D1DeviceContext4))),
        ("SetMaximumColorGlyphCacheMemory", com.METHOD(c_void, UINT64)),
        ("GetMaximumColorGlyphCacheMemory", com.METHOD(UINT64)),
    ]



class ID2D1Factory(com.pIUnknown):
    _methods_ = [
        ("ReloadSystemMetrics",
         com.STDMETHOD()),
        ("GetDesktopDpi",
         com.STDMETHOD()),
        ("CreateRectangleGeometry",
         com.STDMETHOD()),
        ("CreateRoundedRectangleGeometry",
         com.STDMETHOD()),
        ("CreateEllipseGeometry",
         com.STDMETHOD()),
        ("CreateGeometryGroup",
         com.STDMETHOD()),
        ("CreateTransformedGeometry",
         com.STDMETHOD()),
        ("CreatePathGeometry",
         com.STDMETHOD()),
        ("CreateStrokeStyle",
         com.STDMETHOD()),
        ("CreateDrawingStateBlock",
         com.STDMETHOD()),
        ("CreateWicBitmapRenderTarget",
         com.STDMETHOD(IWICBitmap, POINTER(D2D1_RENDER_TARGET_PROPERTIES), POINTER(ID2D1RenderTarget))),
        ("CreateHwndRenderTarget",
         com.STDMETHOD()),
        ("CreateDxgiSurfaceRenderTarget",
         com.STDMETHOD()),
        ("CreateDCRenderTarget",
         com.STDMETHOD()),
    ]


class ID2D1Factory1(ID2D1Factory):
    _methods_ = [
        ("CreateDevice", com.STDMETHOD(c_void_p, POINTER(ID2D1Device))),
        ("CreateStrokeStyle1", com.STDMETHOD()),
        ("CreatePathGeometry1", com.STDMETHOD()),
        ("CreateDrawingStateBlock1", com.STDMETHOD()),
        ("CreateGdiMetafile", com.STDMETHOD()),
        ("RegisterEffectFromStream", com.STDMETHOD()),
        ("RegisterEffectFromString", com.STDMETHOD()),
        ("UnregisterEffect", com.STDMETHOD()),
        ("GetRegisteredEffects", com.STDMETHOD()),
        ("GetEffectProperties", com.STDMETHOD()),
    ]

class ID2D1Factory2(ID2D1Factory1):
    _methods_ = [
        ("CreateDevice2", com.STDMETHOD()),
    ]

class ID2D1Factory3(ID2D1Factory2):
    _methods_ = [
        ("CreateDevice3", com.STDMETHOD()),
    ]


class ID2D1Factory4(ID2D1Factory3):
    _methods_ = [
        ("CreateDevice4", com.STDMETHOD()),
    ]

class ID2D1Factory5(ID2D1Factory4):
    _methods_ = [
        ("CreateDevice5",
         com.STDMETHOD(c_void_p, POINTER(ID2D1Device4))),
    ]


IID_ID2D1Factory = com.GUID(0x06152247, 0x6f50, 0x465a, 0x92, 0x45, 0x11, 0x8b, 0xfd, 0x3b, 0x60, 0x07)
IID_ID2D1Factory1 = com.GUID(0xbb12d362,0xdaee,0x4b9a,0xaa,0x1d,0x14,0xba,0x40,0x1c,0xfa,0x1f)
#IID_ID2D1Factory2 = com.GUID.from_string("94f81a73-9212-4376-9c58-b16a3a0d3992")
IID_ID2D1Factory4 = com.GUID.from_string("bd4ec2d2-0662-4bee-ba8e-6f29f032e096")
IID_ID2D1Factory5 = com.GUID.from_string("c4349994-838e-4b0f-8cab-44997d9eeacc")

# Default render parameters for D2D.
default_target_properties = D2D1_RENDER_TARGET_PROPERTIES(
    type=D2D1_RENDER_TARGET_TYPE_DEFAULT,
    pixelFormat=D2D1_PIXEL_FORMAT(
        format=DXGI_FORMAT_UNKNOWN,
        alphaMode=D2D1_ALPHA_MODE_UNKNOWN,
    ),
    dpiX=0.0,
    dpiY=0.0,
    usage=D2D1_RENDER_TARGET_USAGE_NONE,
    min_level=D2D1_FEATURE_LEVEL_DEFAULT,
)

default_bitmap_properties = D2D1_BITMAP_PROPERTIES1(
    pixelFormat=D2D1_PIXEL_FORMAT(
        format=DXGI_FORMAT_B8G8R8A8_UNORM,
        alphaMode=D2D1_ALPHA_MODE_PREMULTIPLIED,
    ),
    dpiX=0.0,
    dpiY=0.0,
    bitmapOptions=D2D1_BITMAP_OPTIONS_TARGET | D2D1_BITMAP_OPTIONS_CANNOT_DRAW,
)

default_bitmap_properties0 = D2D1_BITMAP_PROPERTIES(
    pixelFormat=D2D1_PIXEL_FORMAT(
        format=DXGI_FORMAT_B8G8R8A8_UNORM,
        alphaMode=D2D1_ALPHA_MODE_PREMULTIPLIED,
    ),
    dpiX=0.0,
    dpiY=0.0,
)

IID_ID2D1DeviceContext = com.GUID(0xe8f7fe7a, 0x191c, 0x466d, 0xad, 0x95, 0x97, 0x56, 0x78, 0xbd, 0xa9, 0x98)
IID_ID2D1DeviceContext4 = com.GUID.from_string("8c427831-3d90-4476-b647-c4fae349e4db")
