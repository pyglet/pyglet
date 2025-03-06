"""Windows Imaging Component library definitions for Windows OS."""
from ctypes import byref, c_void_p, memmove

from pyglet.image import ImageData
from pyglet.image.codecs import ImageDecodeException, ImageDecoder, ImageEncoder, os
from pyglet.libs.win32 import _kernel32 as kernel32
from pyglet.libs.win32 import _ole32 as ole32
from pyglet.libs.win32 import com
from pyglet.libs.win32.constants import (
    CLSCTX_INPROC_SERVER,
    GENERIC_WRITE,
    GMEM_MOVEABLE,
    STREAM_SEEK_SET,
    WINDOWS_8_OR_GREATER,
)
from pyglet.libs.win32.types import (
    BOOL,
    BYTE,
    DOUBLE,
    DWORD,
    LPCWSTR,
    POINTER,
    PROPVARIANT,
    STATSTG,
    UINT,
    ULONG,
    IStream,
)

CLSID_WICImagingFactory1 = com.GUID(0xcacaf262, 0x9370, 0x4615, 0xa1, 0x3b, 0x9f, 0x55, 0x39, 0xda, 0x4c, 0xa)
CLSID_WICImagingFactory2 = com.GUID(0x317d06e8, 0x5f24, 0x433d, 0xbd, 0xf7, 0x79, 0xce, 0x68, 0xd8, 0xab, 0xc2)


WICBitmapCreateCacheOption = UINT
WICBitmapNoCache = 0
WICBitmapCacheOnDemand = 0x1
WICBitmapCacheOnLoad = 0x2
WICBITMAPCREATECACHEOPTION_FORCE_DWORD = 0x7fffffff

WICBitmapPaletteType = UINT
WICBitmapPaletteTypeCustom = 0

WICBitmapTransformOptions = UINT
WICBitmapTransformRotate0 = 0
WICBitmapTransformRotate90 = 0x1
WICBitmapTransformRotate180 = 0x2
WICBitmapTransformRotate270 = 0x3
WICBitmapTransformFlipHorizontal = 0x8
WICBitmapTransformFlipVertical = 0x10

WICBitmapDitherType = UINT
WICBitmapDitherTypeNone = 0
WICBitmapDitherTypeSolid = 0
WICBitmapDitherTypeOrdered4x4 = 0x1
WICBitmapDitherTypeOrdered8x8 = 0x2
WICBitmapDitherTypeOrdered16x16 = 0x3
WICBitmapDitherTypeSpiral4x4 = 0x4
WICBitmapDitherTypeSpiral8x8 = 0x5
WICBitmapDitherTypeDualSpiral4x4 = 0x6
WICBitmapDitherTypeDualSpiral8x8 = 0x7
WICBitmapDitherTypeErrorDiffusion = 0x8
WICBITMAPDITHERTYPE_FORCE_DWORD = 0x7fffffff
WICBITMAPTRANSFORMOPTIONS_FORCE_DWORD = 0x7fffffff

WICDecodeOptions = UINT
WICDecodeMetadataCacheOnDemand = 0
WICDecodeMetadataCacheOnLoad = 0x1
WICMETADATACACHEOPTION_FORCE_DWORD = 0x7fffffff

WICBitmapEncoderCacheOption = UINT
WICBitmapEncoderCacheInMemory = 0x0
WICBitmapEncoderCacheTempFile = 0x1
WICBitmapEncoderNoCache = 0x2
WICBITMAPENCODERCACHEOPTION_FORCE_DWORD = 0x7fffffff

# Different pixel formats.
REFWICPixelFormatGUID = POINTER(com.GUID)
GUID_WICPixelFormatDontCare = com.GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x00)
GUID_WICPixelFormat1bppIndexed = com.GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x01)
GUID_WICPixelFormat2bppIndexed = com.GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x02)
GUID_WICPixelFormat4bppIndexed = com.GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x03)
GUID_WICPixelFormat8bppIndexed = com.GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x04)
GUID_WICPixelFormatBlackWhite = com.GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x05)
GUID_WICPixelFormat2bppGray = com.GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x06)
GUID_WICPixelFormat4bppGray = com.GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x07)
GUID_WICPixelFormat8bppGray = com.GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x08)
GUID_WICPixelFormat8bppAlpha = com.GUID(0xe6cd0116, 0xeeba, 0x4161, 0xaa, 0x85, 0x27, 0xdd, 0x9f, 0xb3, 0xa8, 0x95)
GUID_WICPixelFormat16bppBGR555 = com.GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x09)
GUID_WICPixelFormat16bppBGR565 = com.GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x0a)
GUID_WICPixelFormat16bppBGRA5551 = com.GUID(0x05ec7c2b, 0xf1e6, 0x4961, 0xad, 0x46, 0xe1, 0xcc, 0x81, 0x0a, 0x87, 0xd2)
GUID_WICPixelFormat16bppGray = com.GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x0b)
GUID_WICPixelFormat24bppBGR = com.GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x0c)
GUID_WICPixelFormat24bppRGB = com.GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x0d)
GUID_WICPixelFormat32bppBGR = com.GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x0e)
GUID_WICPixelFormat32bppBGRA = com.GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x0f)
GUID_WICPixelFormat32bppPBGRA = com.GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x10)
GUID_WICPixelFormat32bppRGB = com.GUID(0xd98c6b95, 0x3efe, 0x47d6, 0xbb, 0x25, 0xeb, 0x17, 0x48, 0xab, 0x0c,
                                       0xf1)  # 7 platform update?
GUID_WICPixelFormat32bppRGBA = com.GUID(0xf5c7ad2d, 0x6a8d, 0x43dd, 0xa7, 0xa8, 0xa2, 0x99, 0x35, 0x26, 0x1a, 0xe9)
GUID_WICPixelFormat32bppPRGBA = com.GUID(0x3cc4a650, 0xa527, 0x4d37, 0xa9, 0x16, 0x31, 0x42, 0xc7, 0xeb, 0xed, 0xba)
GUID_WICPixelFormat48bppRGB = com.GUID(0x6fddc324, 0x4e03, 0x4bfe, 0xb1, 0x85, 0x3d, 0x77, 0x76, 0x8d, 0xc9, 0x15)
GUID_WICPixelFormat48bppBGR = com.GUID(0xe605a384, 0xb468, 0x46ce, 0xbb, 0x2e, 0x36, 0xf1, 0x80, 0xe6, 0x43, 0x13)

GUID_ContainerFormatBmp = com.GUID(0x0af1d87e, 0xfcfe, 0x4188, 0xbd, 0xeb, 0xa7, 0x90, 0x64, 0x71, 0xcb, 0xe3)
GUID_ContainerFormatPng = com.GUID(0x1b7cfaf4, 0x713f, 0x473c, 0xbb, 0xcd, 0x61, 0x37, 0x42, 0x5f, 0xae, 0xaf)
GUID_ContainerFormatIco = com.GUID(0xa3a860c4, 0x338f, 0x4c17, 0x91, 0x9a, 0xfb, 0xa4, 0xb5, 0x62, 0x8f, 0x21)
GUID_ContainerFormatJpeg = com.GUID(0x19e4a5aa, 0x5662, 0x4fc5, 0xa0, 0xc0, 0x17, 0x58, 0x02, 0x8e, 0x10, 0x57)
GUID_ContainerFormatTiff = com.GUID(0x163bcc30, 0xe2e9, 0x4f0b, 0x96, 0x1d, 0xa3, 0xe9, 0xfd, 0xb7, 0x88, 0xa3)
GUID_ContainerFormatGif = com.GUID(0x1f8a5601, 0x7d4d, 0x4cbd, 0x9c, 0x82, 0x1b, 0xc8, 0xd4, 0xee, 0xb9, 0xa5)
GUID_ContainerFormatWmp = com.GUID(0x57a37caa, 0x367a, 0x4540, 0x91, 0x6b, 0xf1, 0x83, 0xc5, 0x09, 0x3a, 0x4b)


class IPropertyBag2(com.pIUnknown):
    _methods_ = [
        ('Read',
         com.STDMETHOD()),
        ('Write',
         com.STDMETHOD()),
        ('CountProperties',
         com.STDMETHOD()),
        ('GetPropertyInfo',
         com.STDMETHOD()),
        ('LoadObject',
         com.STDMETHOD())
    ]


class IWICPalette(com.pIUnknown):
    _methods_ = [
        ('InitializePredefined',
         com.STDMETHOD()),
        ('InitializeCustom',
         com.STDMETHOD()),
        ('InitializeFromBitmap',
         com.STDMETHOD()),
        ('InitializeFromPalette',
         com.STDMETHOD()),
        ('GetType',
         com.STDMETHOD()),
        ('GetColorCount',
         com.STDMETHOD()),
        ('GetColors',
         com.STDMETHOD()),
        ('IsBlackWhite',
         com.STDMETHOD()),
        ('IsGrayscale',
         com.STDMETHOD()),
        ('HasAlpha',
         com.STDMETHOD()),
    ]


class IWICStream(IStream, com.pIUnknown):
    _methods_ = [
        ('InitializeFromIStream',
         com.STDMETHOD(IStream)),
        ('InitializeFromFilename',
         com.STDMETHOD(LPCWSTR, DWORD)),
        ('InitializeFromMemory',
         com.STDMETHOD(POINTER(BYTE), DWORD)),
        ('InitializeFromIStreamRegion',
         com.STDMETHOD()),
    ]


class IWICBitmapFrameEncode(com.pIUnknown):
    _methods_ = [
        ('Initialize',
         com.STDMETHOD(IPropertyBag2)),
        ('SetSize',
         com.STDMETHOD(UINT, UINT)),
        ('SetResolution',
         com.STDMETHOD()),
        ('SetPixelFormat',
         com.STDMETHOD(REFWICPixelFormatGUID)),
        ('SetColorContexts',
         com.STDMETHOD()),
        ('SetPalette',
         com.STDMETHOD(IWICPalette)),
        ('SetThumbnail',
         com.STDMETHOD()),
        ('WritePixels',
         com.STDMETHOD(UINT, UINT, UINT, POINTER(BYTE))),
        ('WriteSource',
         com.STDMETHOD()),
        ('Commit',
         com.STDMETHOD()),
        ('GetMetadataQueryWriter',
         com.STDMETHOD())
    ]


class IWICBitmapEncoder(com.pIUnknown):
    _methods_ = [
        ('Initialize',
         com.STDMETHOD(IWICStream, WICBitmapEncoderCacheOption)),
        ('GetContainerFormat',
         com.STDMETHOD()),
        ('GetEncoderInfo',
         com.STDMETHOD()),
        ('SetColorContexts',
         com.STDMETHOD()),
        ('SetPalette',
         com.STDMETHOD()),
        ('SetThumbnail',
         com.STDMETHOD()),
        ('SetPreview',
         com.STDMETHOD()),
        ('CreateNewFrame',
         com.STDMETHOD(POINTER(IWICBitmapFrameEncode), POINTER(IPropertyBag2))),
        ('Commit',
         com.STDMETHOD()),
        ('GetMetadataQueryWriter',
         com.STDMETHOD())
    ]


class IWICComponentInfo(com.pIUnknown):
    _methods_ = [
        ('GetComponentType',
         com.STDMETHOD()),
        ('GetCLSID',
         com.STDMETHOD()),
        ('GetSigningStatus',
         com.STDMETHOD()),
        ('GetAuthor',
         com.STDMETHOD()),
        ('GetVendorGUID',
         com.STDMETHOD()),
        ('GetVersion',
         com.STDMETHOD()),
        ('GetSpecVersion',
         com.STDMETHOD()),
        ('GetFriendlyName',
         com.STDMETHOD())
    ]


class IWICPixelFormatInfo(IWICComponentInfo, com.pIUnknown):
    _methods_ = [
        ('GetFormatGUID',
         com.STDMETHOD(POINTER(com.GUID))),
        ('GetColorContext',
         com.STDMETHOD()),
        ('GetBitsPerPixel',
         com.STDMETHOD(POINTER(UINT))),
        ('GetChannelCount',
         com.STDMETHOD(POINTER(UINT))),
        ('GetChannelMask',
         com.STDMETHOD())
    ]


class IWICBitmapSource(com.pIUnknown):
    _methods_ = [
        ('GetSize',
         com.STDMETHOD(POINTER(UINT), POINTER(UINT))),
        ('GetPixelFormat',
         com.STDMETHOD(REFWICPixelFormatGUID)),
        ('GetResolution',
         com.STDMETHOD(POINTER(DOUBLE), POINTER(DOUBLE))),
        ('CopyPalette',
         com.STDMETHOD()),
        ('CopyPixels',
         com.STDMETHOD(c_void_p, UINT, UINT, c_void_p)),
    ]


class IWICFormatConverter(IWICBitmapSource, com.pIUnknown):
    _methods_ = [
        ('Initialize',
         com.STDMETHOD(IWICBitmapSource, REFWICPixelFormatGUID, WICBitmapDitherType, c_void_p, DOUBLE,
                       WICBitmapPaletteType)),
        ('CanConvert',
         com.STDMETHOD(REFWICPixelFormatGUID, REFWICPixelFormatGUID, POINTER(BOOL))),
    ]


class IWICMetadataQueryReader(com.pIUnknown):
    _methods_ = [
        ('GetContainerFormat',
         com.STDMETHOD()),
        ('GetLocation',
         com.STDMETHOD()),
        ('GetMetadataByName',
         com.STDMETHOD(LPCWSTR, c_void_p)),
        ('GetEnumerator',
         com.STDMETHOD()),
    ]


class IWICBitmapFrameDecode(IWICBitmapSource, com.pIUnknown):
    _methods_ = [
        ('GetMetadataQueryReader',
         com.STDMETHOD(POINTER(IWICMetadataQueryReader))),
        ('GetColorContexts',
         com.STDMETHOD()),
        ('GetThumbnail',
         com.STDMETHOD(POINTER(IWICBitmapSource))),
    ]


class IWICBitmapFlipRotator(IWICBitmapSource, com.pIUnknown):
    _methods_ = [
        ('Initialize',
         com.STDMETHOD(IWICBitmapSource, WICBitmapTransformOptions)),
    ]


class IWICBitmap(IWICBitmapSource, com.pIUnknown):
    _methods_ = [
        ('Lock',
         com.STDMETHOD()),
        ('SetPalette',
         com.STDMETHOD()),
        ('SetResolution',
         com.STDMETHOD())
    ]


class IWICBitmapDecoder(com.pIUnknown):
    _methods_ = [
        ('QueryCapability',
         com.STDMETHOD()),
        ('Initialize',
         com.STDMETHOD()),
        ('GetContainerFormat',
         com.STDMETHOD()),
        ('GetDecoderInfo',
         com.STDMETHOD()),
        ('CopyPalette',
         com.STDMETHOD()),
        ('GetMetadataQueryReader',
         com.STDMETHOD(POINTER(IWICMetadataQueryReader))),
        ('GetPreview',
         com.STDMETHOD()),
        ('GetColorContexts',
         com.STDMETHOD()),
        ('GetThumbnail',
         com.STDMETHOD()),
        ('GetFrameCount',
         com.STDMETHOD(POINTER(UINT))),
        ('GetFrame',
         com.STDMETHOD(UINT, POINTER(IWICBitmapFrameDecode))),
    ]


IID_IWICImagingFactory1 = com.GUID(0xec5ec8a9, 0xc395, 0x4314, 0x9c, 0x77, 0x54, 0xd7, 0xa9, 0x35, 0xff, 0x70)
IID_IWICImagingFactory2 = com.GUID(0x7B816B45, 0x1996, 0x4476, 0xB1, 0x32, 0xDE, 0x9E, 0x24, 0x7C, 0x8A, 0xF0)


IID_IWICPixelFormatInfo = com.GUID(0xE8EDA601, 0x3D48, 0x431a, 0xAB, 0x44, 0x69, 0x05, 0x9B, 0xE8, 0x8B, 0xBE)


class IWICImagingFactory(com.pIUnknown):
    _methods_ = [
        ('CreateDecoderFromFilename',
         com.STDMETHOD(LPCWSTR, com.GUID, DWORD, WICDecodeOptions, POINTER(IWICBitmapDecoder))),
        ('CreateDecoderFromStream',
         com.STDMETHOD(com.pIUnknown, c_void_p, WICDecodeOptions, POINTER(IWICBitmapDecoder))),
        ('CreateDecoderFromFileHandle',
         com.STDMETHOD()),
        ('CreateComponentInfo',
         com.STDMETHOD(com.GUID, POINTER(IWICComponentInfo))),
        ('CreateDecoder',
         com.STDMETHOD()),
        ('CreateEncoder',
         com.STDMETHOD(POINTER(com.GUID), POINTER(com.GUID), POINTER(IWICBitmapEncoder))),
        ('CreatePalette',
         com.STDMETHOD(POINTER(IWICPalette))),
        ('CreateFormatConverter',
         com.STDMETHOD(POINTER(IWICFormatConverter))),
        ('CreateBitmapScaler',
         com.STDMETHOD()),
        ('CreateBitmapClipper',
         com.STDMETHOD()),
        ('CreateBitmapFlipRotator',
         com.STDMETHOD(POINTER(IWICBitmapFlipRotator))),
        ('CreateStream',
         com.STDMETHOD(POINTER(IWICStream))),
        ('CreateColorContext',
         com.STDMETHOD()),
        ('CreateColorTransformer',
         com.STDMETHOD()),
        ('CreateBitmap',
         com.STDMETHOD(UINT, UINT, REFWICPixelFormatGUID, WICBitmapCreateCacheOption, POINTER(IWICBitmap))),
        ('CreateBitmapFromSource',
         com.STDMETHOD()),
        ('CreateBitmapFromSourceRect',
         com.STDMETHOD()),
        ('CreateBitmapFromMemory',
         com.STDMETHOD(UINT, UINT, REFWICPixelFormatGUID, UINT, UINT, POINTER(BYTE), POINTER(IWICBitmap))),
        ('CreateBitmapFromHBITMAP',
         com.STDMETHOD()),
        ('CreateBitmapFromHICON',
         com.STDMETHOD()),
        ('CreateComponentEnumerator',
         com.STDMETHOD()),
        ('CreateFastMetadataEncoderFromDecoder',
         com.STDMETHOD()),
        ('CreateFastMetadataEncoderFromFrameDecode',
         com.STDMETHOD()),
        ('CreateQueryWriter',
         com.STDMETHOD()),
        ('CreateQueryWriterFromReader',
         com.STDMETHOD())
    ]

class IWICImagingFactory2(IWICImagingFactory):
    _methods_ = [
        ('CreateImageEncoder',
         com.STDMETHOD()),
    ]
