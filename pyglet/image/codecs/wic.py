from __future__ import annotations

import os
from ctypes import byref, memmove
from typing import BinaryIO, Sequence

from pyglet.image import ImageData
from pyglet.image.codecs import ImageDecodeException, ImageDecoder, ImageEncoder
from pyglet.image.codecs.wincodec_lib import (
    CLSID_WICImagingFactory1,
    CLSID_WICImagingFactory2,
    GUID_ContainerFormatBmp,
    GUID_ContainerFormatJpeg,
    GUID_ContainerFormatPng,
    GUID_ContainerFormatTiff,
    GUID_ContainerFormatWmp,
    GUID_WICPixelFormat24bppBGR,
    GUID_WICPixelFormat32bppBGRA,
    IID_IWICImagingFactory1,
    IID_IWICImagingFactory2,
    IPropertyBag2,
    IWICBitmap,
    IWICBitmapDecoder,
    IWICBitmapEncoder,
    IWICBitmapFlipRotator,
    IWICBitmapFrameDecode,
    IWICBitmapFrameEncode,
    IWICFormatConverter,
    IWICImagingFactory,
    IWICImagingFactory2,
    IWICMetadataQueryReader,
    IWICStream,
    WICBitmapCacheOnDemand,
    WICBitmapDitherTypeNone,
    WICBitmapEncoderNoCache,
    WICBitmapPaletteTypeCustom,
    WICBitmapTransformFlipVertical,
    WICDecodeMetadataCacheOnDemand,
)
from pyglet.libs.win32 import _kernel32 as kernel32
from pyglet.libs.win32 import _ole32 as ole32
from pyglet.libs.win32 import com
from pyglet.libs.win32.constants import (
    CLSCTX_INPROC_SERVER,
    GENERIC_WRITE,
    GMEM_MOVEABLE,
    STREAM_SEEK_SET,
)
from pyglet.libs.win32.types import BOOL, BYTE, PROPVARIANT, STATSTG, UINT, ULONG, IStream


def _create_factory() -> IWICImagingFactory2 | IWICImagingFactory | None:
    """Get a WIC Factory.

    Factory 2 should be available since Windows 7 with a Platform Update, but be on the safe side.
    """
    try:
        factory = IWICImagingFactory2()
        ole32.CoCreateInstance(CLSID_WICImagingFactory2,
                               None,
                               CLSCTX_INPROC_SERVER,
                               IID_IWICImagingFactory2,
                               byref(factory))
        return factory
    except OSError:
        pass

    try:
        factory = IWICImagingFactory()
        ole32.CoCreateInstance(CLSID_WICImagingFactory1,
                               None,
                               CLSCTX_INPROC_SERVER,
                               IID_IWICImagingFactory1,
                               byref(factory))
        return factory
    except OSError:
        pass

    return None

_factory = _create_factory()
if not _factory:
    raise ImportError("Could not create WIC factory.")

def get_factory() -> IWICImagingFactory2 | IWICImagingFactory:
    """Retrieve the current WIC factory.

    WIC interfaces with many other libraries such as DirectWrite and Direct2D.
    """
    return _factory

def _get_bitmap_frame(bitmap_decoder: IWICBitmapDecoder, frame_index: int) -> IWICBitmapFrameDecode:
    bitmap = IWICBitmapFrameDecode()
    bitmap_decoder.GetFrame(frame_index, byref(bitmap))
    return bitmap

def get_bitmap(width: int, height: int, target_fmt: com.GUID=GUID_WICPixelFormat32bppBGRA) -> IWICBitmap:
    """Create a WIC Bitmap.

    Caller is responsible for releasing ``IWICBitmap``.
    """
    bitmap = IWICBitmap()
    _factory.CreateBitmap(width, height,
                      target_fmt,
                      WICBitmapCacheOnDemand,
                      byref(bitmap))
    return bitmap


def extract_image_data(bitmap: IWICBitmap, target_fmt: com.GUID = GUID_WICPixelFormat32bppBGRA) -> ImageData:
    """Extra image data from IWICBitmap into ImageData, specifying target format.

    .. note:: ``bitmap`` is released before this function returns.
    """
    width = UINT()
    height = UINT()

    bitmap.GetSize(byref(width), byref(height))

    width = int(width.value)
    height = int(height.value)

    # Get image pixel format
    pf = com.GUID(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    bitmap.GetPixelFormat(byref(pf))

    fmt = 'BGRA'
    # If target format is not what we want (32bit BGRA) convert it.
    if pf != target_fmt:
        converter = IWICFormatConverter()
        _factory.CreateFormatConverter(byref(converter))

        conversion_possible = BOOL()
        converter.CanConvert(pf, target_fmt, byref(conversion_possible))

        # 99% of the time conversion will be possible to default.
        # However, we check to be safe and fallback to 24 bit BGR if not possible.
        if not conversion_possible:
            target_fmt = GUID_WICPixelFormat24bppBGR
            fmt = 'BGR'

        converter.Initialize(bitmap, target_fmt, WICBitmapDitherTypeNone, None, 0, WICBitmapPaletteTypeCustom)

        bitmap.Release()
        bitmap = converter

    # Most images are loaded with a negative pitch, which requires list comprehension to fix.
    # Create a flipped bitmap through the decoder rather through Python to increase performance.
    flipper = IWICBitmapFlipRotator()
    _factory.CreateBitmapFlipRotator(byref(flipper))

    flipper.Initialize(bitmap, WICBitmapTransformFlipVertical)

    stride = len(fmt) * width
    buffer_size = stride * height

    buffer = (BYTE * buffer_size)()

    flipper.CopyPixels(None, stride, buffer_size, byref(buffer))

    flipper.Release()
    bitmap.Release()  # Can be converter.

    return ImageData(width, height, fmt, buffer)


class WICDecoder(ImageDecoder):
    """Windows Imaging Component implementation for image decoding.

    This decoder is a replacement for GDI/GDI+ starting with Windows 7.
    """
    def __init__(self) -> None:  # noqa: D107
        super(ImageDecoder, self).__init__()
        self._factory = get_factory()

    def get_file_extensions(self) -> Sequence[str]:
        return ['.bmp', '.jpg', '.jpeg', '.png', '.tif', '.tiff', '.ico', '.jxr', '.hdp', '.wdp']

    def _load_bitmap_decoder(self, filename: str, file: BinaryIO | None = None) -> tuple[IWICBitmapDecoder, IStream]:
        data = file.read()

        # Create a HGLOBAL with image data
        hglob = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        ptr = kernel32.GlobalLock(hglob)
        memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(hglob)

        # Create IStream for the HGLOBAL
        stream = IStream()
        ole32.CreateStreamOnHGlobal(hglob, True, byref(stream))

        # Load image from stream
        decoder = IWICBitmapDecoder()
        status = self._factory.CreateDecoderFromStream(stream, None, WICDecodeMetadataCacheOnDemand, byref(decoder))
        if status != 0:
            stream.Release()
            raise ImageDecodeException('WIC cannot load %r' % (filename or file))

        return decoder, stream

    def decode(self, filename: str, file: BinaryIO | None) -> ImageData:
        if not file:
            with open(filename, 'rb') as f:
                bitmap_decoder, stream = self._load_bitmap_decoder(filename, f)
                bitmap = _get_bitmap_frame(bitmap_decoder, 0)
                image_data = extract_image_data(bitmap)
        else:
            bitmap_decoder, stream = self._load_bitmap_decoder(filename, file)
            bitmap = _get_bitmap_frame(bitmap_decoder, 0)
            image_data = extract_image_data(bitmap)

        bitmap_decoder.Release()
        stream.Release()
        return image_data

    @staticmethod
    def get_property_value(reader: IWICMetadataQueryReader, metadata_name: str) -> int:
        """Uses a metadata name and reader to return a single value.

        Can be used to get metadata from images.

        Handles cleanup of PROPVARIANT.

        Returns:
            0 on failure.
        """
        try:
            prop = PROPVARIANT()
            reader.GetMetadataByName(metadata_name, byref(prop))
            value = prop.llVal
            ole32.PropVariantClear(byref(prop))
        except OSError:
            value = 0

        return value


def get_decoders() -> Sequence[ImageDecoder]:  # noqa: D103
    return [WICDecoder()]


extension_to_container = {
    '.bmp': GUID_ContainerFormatBmp,
    '.jpg': GUID_ContainerFormatJpeg,
    '.jpeg': GUID_ContainerFormatJpeg,
    '.tif': GUID_ContainerFormatTiff,
    '.tiff': GUID_ContainerFormatTiff,
    '.wmp': GUID_ContainerFormatWmp,
    '.jxr': GUID_ContainerFormatWmp,
    '.wdp': GUID_ContainerFormatWmp,
    '.png': GUID_ContainerFormatPng,
}


class WICEncoder(ImageEncoder):  # noqa: D101
    def get_file_extensions(self) -> Sequence[str]:
        return list(extension_to_container)

    def encode(self, image: ImageData, filename: str, file: BinaryIO | None) -> None:
        image = image.get_image_data()

        wicstream = IWICStream()
        encoder = IWICBitmapEncoder()
        frame = IWICBitmapFrameEncode()
        property_bag = IPropertyBag2()

        ext = (filename and os.path.splitext(filename)[1]) or '.png'

        # Choose container based on extension. Default to PNG.
        container = extension_to_container.get(ext, GUID_ContainerFormatPng)

        _factory.CreateStream(byref(wicstream))
        # https://docs.microsoft.com/en-us/windows/win32/wic/-wic-codec-native-pixel-formats#native-image-formats
        if container == GUID_ContainerFormatJpeg:
            # Expects BGR, no transparency available. Hard coded.
            fmt = 'BGR'
            default_format = GUID_WICPixelFormat24bppBGR
        else:
            # Windows encodes in BGRA.
            if len(image.format) == 3:
                fmt = 'BGR'
                default_format = GUID_WICPixelFormat24bppBGR
            else:
                fmt = 'BGRA'
                default_format = GUID_WICPixelFormat32bppBGRA

        pitch = image.width * len(fmt)

        image_data = image.get_data(fmt, -pitch)

        size = pitch * image.height

        if file:
            istream = IStream()
            ole32.CreateStreamOnHGlobal(None, True, byref(istream))
            wicstream.InitializeFromIStream(istream)
        else:
            istream = None
            wicstream.InitializeFromFilename(filename, GENERIC_WRITE)

        _factory.CreateEncoder(container, None, byref(encoder))

        encoder.Initialize(wicstream, WICBitmapEncoderNoCache)

        encoder.CreateNewFrame(byref(frame), byref(property_bag))

        frame.Initialize(property_bag)

        frame.SetSize(image.width, image.height)

        frame.SetPixelFormat(byref(default_format))

        data = (BYTE * size).from_buffer(bytearray(image_data))

        frame.WritePixels(image.height, pitch, size, data)

        frame.Commit()

        encoder.Commit()

        if file and istream:
            sts = STATSTG()
            istream.Stat(byref(sts), 0)
            stream_size = sts.cbSize
            istream.Seek(0, STREAM_SEEK_SET, None)

            buf = (BYTE * stream_size)()
            written = ULONG()
            istream.Read(byref(buf), stream_size, byref(written))

            if written.value == stream_size:
                file.write(buf)
            else:
                print(f"Failed to read all of the data from stream attempting to save {file}")

            istream.Release()

        encoder.Release()
        frame.Release()
        property_bag.Release()
        wicstream.Release()


def get_encoders() -> Sequence[ImageEncoder]:  # noqa: D103
    return [WICEncoder()]
