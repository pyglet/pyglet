"""Codec for the QOI image format.

This module contains an encoder and decoder for the QOI (Quite OK Image) format.
See https://qoiformat.org/ and https://github.com/phoboslab/qoi for more details.
"""
import struct

from pyglet.image import ImageData
from pyglet.image.codecs import ImageDecoder, ImageEncoder, ImageDecodeException, ImageEncodeException


QOI_OP_INDEX =  0x00    # 00xxxxxx
QOI_OP_DIFF =   0x40    # 01xxxxxx
QOI_OP_LUMA =   0x80    # 10xxxxxx
QOI_OP_RUN =    0xc0    # 11xxxxxx
QOI_OP_RGB =    0xfe    # 11111110
QOI_OP_RGBA =   0xff    # 11111111
QOI_MASK_2 =    0xc0    # 11000000


class QOIImageDecoder(ImageDecoder):

    def get_file_extensions(self):
        return ['.qoi']

    def decode(self, filename, file):
        if not file:
            file = open(filename, 'rb')

        raw = file.read()
        if len(raw) < 14:
            raise ImageDecodeException("Unexpected end of QOI data.")
        magic, width, height, channels, _ = struct.unpack(">4sIIBB", raw[:14])
        if magic != b'qoif':
            raise ImageDecodeException("Does not appear to be a valid QOI file.")

        px_len = width * height * channels
        pixel_data = bytearray(px_len)
        hash_array = [0] * 64

        r = g = b = 0
        a = 255

        run = 0
        pos = 14
        data_len = len(raw)

        has_alpha = channels == 4
        # micro optimization to avoid module lookup:
        op_index = QOI_OP_INDEX
        op_diff = QOI_OP_DIFF
        op_luma = QOI_OP_LUMA
        op_rgb = QOI_OP_RGB
        op_rgba = QOI_OP_RGBA
        mask2 = QOI_MASK_2

        for i in range(-channels, px_len, channels):
            hash_array[(r * 3 + g * 5 + b * 7 + a * 11) & 0x3F] = ((a if has_alpha else 255) << 24) | (r << 16) | (g << 8) | b
            if i >= 0:
                pixel_data[i] = r
                pixel_data[i + 1] = g
                pixel_data[i + 2] = b
                if has_alpha:
                    pixel_data[i + 3] = a
            if run > 0:
                run -= 1
                continue
            if pos >= data_len:
                raise ImageDecodeException("Unexpected end of QOI data.")
            b1 = raw[pos]
            pos += 1
            if b1 == op_rgb:
                if pos + 3 > data_len:
                    raise ImageDecodeException("Unexpected end of QOI data.")
                r = raw[pos]
                g = raw[pos + 1]
                b = raw[pos + 2]
                pos += 3
                continue
            if b1 == op_rgba:
                if pos + 4 > data_len:
                    raise ImageDecodeException("Unexpected end of QOI data.")
                r = raw[pos]
                g = raw[pos + 1]
                b = raw[pos + 2]
                a = raw[pos + 3]
                pos += 4
                continue
            if (b1 & mask2) == op_index:
                packed = hash_array[b1]
                a = (packed >> 24) & 0xFF
                r = (packed >> 16) & 0xFF
                g = (packed >> 8) & 0xFF
                b = packed & 0xFF
                continue
            if (b1 & mask2) == op_diff:
                r = (r + ((b1 >> 4) & 0x03) - 2) & 0xFF
                g = (g + ((b1 >> 2) & 0x03) - 2) & 0xFF
                b = (b + (b1 & 0x03) - 2) & 0xFF
                continue
            if (b1 & mask2) == op_luma:
                if pos >= data_len:
                    raise ImageDecodeException("Unexpected end of QOI data.")
                b2 = raw[pos]
                pos += 1
                vg = (b1 & 0x3F) - 32
                r = (r + vg - 8 + ((b2 >> 4) & 0x0F)) & 0xFF
                g = (g + vg) & 0xFF
                b = (b + vg - 8 + (b2 & 0x0F)) & 0xFF
                continue
            run = b1 & 0x3F

        fmt = {3: 'RGB', 4: 'RGBA'}[channels]

        return ImageData(width, height, fmt, bytes(pixel_data), pitch=-width * channels)


class QOIImageEncoder(ImageEncoder):

    def get_file_extensions(self):
        return ['.qoi']

    def encode(self, image, filename, file):
        if not file:
            file = open(filename, 'wb')

        image_data = image.get_image_data()
        image_format = image_data.format
        if image_format not in ('RGB', 'RGBA'):
            raise ImageEncodeException(f"QOI encoding of {image_format} images is not supported.")

        alpha = image_format == 'RGBA'
        width = image_data.width
        height = image_data.height
        pixel_bytes = image_data.get_bytes(image_format, -width * len(image_format))

        channels = 4 if alpha else 3

        data = bytearray()
        data.extend(struct.pack(">4sIIBB", b'qoif', width, height, channels, 1))    # header

        hash_array = [0] * 64

        run = 0
        r = g = b = 0
        a = 255
        px_shift = (a << 24) | (r << 16) | (g << 8) | b

        n = len(pixel_bytes)
        # micro optimization to avoid module and dot lookups:
        data_append = data.append
        op_index = QOI_OP_INDEX
        op_diff = QOI_OP_DIFF
        op_luma = QOI_OP_LUMA
        op_run = QOI_OP_RUN
        op_rgb = QOI_OP_RGB
        op_rgba = QOI_OP_RGBA

        if channels == 4:
            for i in range(0, n, 4):
                pr, pg, pb, pa = r, g, b, a
                ps = px_shift
                r = pixel_bytes[i]
                g = pixel_bytes[i + 1]
                b = pixel_bytes[i + 2]
                a = pixel_bytes[i + 3]
                px_shift = (a << 24) | (r << 16) | (g << 8) | b

                if px_shift == ps:
                    run += 1
                    if run == 62 or i + 4 >= n:
                        data_append(op_run | (run - 1))
                        run = 0
                    continue

                if run:
                    data_append(op_run | (run - 1))
                    run = 0

                index_pos = (r * 3 + g * 5 + b * 7 + a * 11) & 0x3F
                if hash_array[index_pos] == px_shift:
                    data_append(op_index | index_pos)
                    continue
                hash_array[index_pos] = px_shift

                if a != pa:
                    data_append(op_rgba)
                    data_append(r)
                    data_append(g)
                    data_append(b)
                    data_append(a)
                    continue

                vr = ((r - pr + 128) & 0xFF) - 128
                vg = ((g - pg + 128) & 0xFF) - 128
                vb = ((b - pb + 128) & 0xFF) - 128

                vg_r = ((vr - vg + 128) & 0xFF) - 128
                vg_b = ((vb - vg + 128) & 0xFF) - 128

                if -3 < vr < 2 and -3 < vg < 2 and -3 < vb < 2:
                    data_append(op_diff | ((vr + 2) << 4) | ((vg + 2) << 2) | (vb + 2))
                    continue

                if -9 < vg_r < 8 and -9 < vg_b < 8 and -33 < vg < 32:
                    data_append(op_luma | (vg + 32))
                    data_append(((vg_r + 8) << 4) | (vg_b + 8))
                    continue

                data_append(op_rgb)
                data_append(r)
                data_append(g)
                data_append(b)

            data.extend((0, 0, 0, 0, 0, 0, 0, 1))
            file.write(data)
            return

        # 3 channel path:
        for i in range(0, n, 3):
            pr, pg, pb = r, g, b
            ps = px_shift
            r = pixel_bytes[i]
            g = pixel_bytes[i + 1]
            b = pixel_bytes[i + 2]
            px_shift = (255 << 24) | (r << 16) | (g << 8) | b

            if px_shift == ps:
                run += 1
                if run == 62 or i + 3 >= n:
                    data_append(op_run | (run - 1))
                    run = 0
                continue

            if run:
                data_append(op_run | (run - 1))
                run = 0

            index_pos = (r * 3 + g * 5 + b * 7 + 2805) & 0x3F
            if hash_array[index_pos] == px_shift:
                data_append(op_index | index_pos)
                continue
            hash_array[index_pos] = px_shift

            vr = ((r - pr + 128) & 0xFF) - 128
            vg = ((g - pg + 128) & 0xFF) - 128
            vb = ((b - pb + 128) & 0xFF) - 128

            vg_r = ((vr - vg + 128) & 0xFF) - 128
            vg_b = ((vb - vg + 128) & 0xFF) - 128

            if -3 < vr < 2 and -3 < vg < 2 and -3 < vb < 2:
                data_append(op_diff | ((vr + 2) << 4) | ((vg + 2) << 2) | (vb + 2))
                continue

            if -9 < vg_r < 8 and -9 < vg_b < 8 and -33 < vg < 32:
                data_append(op_luma | (vg + 32))
                data_append(((vg_r + 8) << 4) | (vg_b + 8))
                continue

            data_append(op_rgb)
            data_append(r)
            data_append(g)
            data_append(b)

        data.extend((0, 0, 0, 0, 0, 0, 0, 1))
        file.write(data)


def get_decoders():
    return [QOIImageDecoder()]


def get_encoders():
    return [QOIImageEncoder()]
