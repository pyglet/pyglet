"""Decoder for Aseprite animation files in .ase or .aseprite format.
"""

import io
import zlib
import struct

from pyglet.image import ImageData, Animation, AnimationFrame
from pyglet.image.codecs import ImageDecoder, ImageDecodeException


#   Documentation for the Aseprite format can be found here:
#   https://raw.githubusercontent.com/aseprite/aseprite/master/docs/ase-file-specs.md


BYTE = "B"
WORD = "H"
SHORT = "h"
DWORD = "I"

BLEND_MODES = {0: 'Normal',
               1: 'Multiply',
               2: 'Screen',
               3: 'Overlay',
               4: 'Darken',
               5: 'Lighten',
               6: 'Color Dodge',
               7: 'Color Burn',
               8: 'Hard Light',
               9: 'Soft Light',
               10: 'Difference',
               11: 'Exclusion',
               12: 'Hue',
               13: 'Saturation',
               14: 'Color',
               15: 'Luminosity'}

PALETTE_DICT = {}
PALETTE_INDEX = 0


def _unpack(fmt, file):
    """Unpack little endian bytes fram a file-like object. """
    size = struct.calcsize(fmt)
    data = file.read(size)
    if len(data) < size:
        raise ImageDecodeException('Unexpected EOF')
    return struct.unpack("<" + fmt, data)[0]


def _chunked_iter(seq, size):
    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


#########################################
#   Class for Aseprite compliant header
#########################################

class AsepriteHeader:
    def __init__(self, file):
        self.file_size = _unpack(DWORD, file)
        self.magic_number = hex(_unpack(WORD, file))
        self.num_frames = _unpack(WORD, file)
        self.width = _unpack(WORD, file)
        self.height = _unpack(WORD, file)
        self.color_depth = _unpack(WORD, file)
        self.flags = _unpack(DWORD, file)
        self.speed = _unpack(WORD, file)
        self._zero = _unpack(DWORD, file)
        self._zero = _unpack(DWORD, file)
        self.palette_index = _unpack(BYTE, file)
        self._ignore = _unpack(BYTE * 3, file)
        self.number_of_colors = _unpack(WORD, file)
        self._zero = _unpack(BYTE * 94, file)


#########################################
#   Class for Aseprite animation frames
#########################################

class Frame(object):
    def __init__(self, num_chunks, duration, header, data):
        self.num_chunks = num_chunks
        self.duration = duration
        self.color_depth = header.color_depth
        self.width = header.width
        self.height = header.height
        self._data = data
        self.chunks = self._parse_chunks()
        self.cels = [c for c in self.chunks if type(c) == CelChunk]
        self.layers = [c for c in self.chunks if type(c) == LayerChunk]

    def _parse_chunks(self):
        fileobj = io.BytesIO(self._data)
        chunks = []
        for chunk in range(self.num_chunks):
            chunk_size = _unpack(DWORD, fileobj)
            chunk_type = format(_unpack(WORD, fileobj), "#06x")
            header_size = struct.calcsize(DWORD + WORD)
            chunk_data = fileobj.read(chunk_size - header_size)
            if chunk_type in ("0x0004", "0x0011", "0x2016"):
                chunks.append(DeprecatedChunk(chunk_size, chunk_type, chunk_data))
            elif chunk_type == "0x2004":
                chunks.append(LayerChunk(chunk_size, chunk_type, chunk_data))
            elif chunk_type == "0x2005":
                chunks.append(CelChunk(chunk_size, chunk_type, chunk_data))
            elif chunk_type == "0x2017":
                chunks.append(PathChunk(chunk_size, chunk_type, chunk_data))
            elif chunk_type == "0x2018":
                chunks.append(FrameTagsChunk(chunk_size, chunk_type, chunk_data))
            elif chunk_type == "0x2019":
                palette_chunk = PaletteChunk(chunk_size, chunk_type, chunk_data)
                chunks.append(palette_chunk)
                global PALETTE_DICT
                PALETTE_DICT = palette_chunk.palette_dict.copy()
            elif chunk_type == "0x2020":
                chunks.append(UserDataChunk(chunk_size, chunk_type, chunk_data))
        return chunks

    def _pad_pixels(self, cel):
        """For cels that don't fill the entire frame, pad with zeros."""
        fileobj = io.BytesIO(cel.pixel_data)

        padding = b'\x00\x00\x00\x00'
        top_pad = padding * (self.width * cel.y_pos)
        left_pad = padding * cel.x_pos
        right_pad = padding * (self.width - cel.x_pos - cel.width)
        bottom_pad = padding * (self.width * (self.height - cel.height - cel.y_pos))
        line_size = cel.width * 4   # (RGBA)

        pixel_array = top_pad
        for i in range(cel.height):
            pixel_array += (left_pad + fileobj.read(line_size) + right_pad)
        pixel_array += bottom_pad

        return pixel_array

    @staticmethod
    def _blend_pixels(bottom, top, mode):
        # Iterate over the arrays in chunks of 4 (RGBA):
        bottom_iter = _chunked_iter(bottom, 4)
        top_iter = _chunked_iter(top, 4)

        if mode == 'Normal':
            final_array = []
            # If RGBA values are > 0, use the top pixel.
            for bottom_pixel, top_pixel in zip(bottom_iter, top_iter):
                if any(top_pixel) > 0:      # Any of R, G, B, A > 0
                    final_array.extend(top_pixel)
                else:
                    final_array.extend(bottom_pixel)
            return bytes(final_array)

        # TODO: implement additional blend modes
        else:
            raise ImageDecodeException("Unsupported blend mode: '{}'".format(mode))

    def _convert_to_rgba(self, cel):
        if self.color_depth == 8:
            global PALETTE_INDEX
            pixel_array = []
            for pixel in cel.pixel_data:
                if pixel == PALETTE_INDEX:
                    pixel_array.extend([0, 0, 0, 0])
                else:
                    pixel_array.extend(PALETTE_DICT[pixel])
            cel.pixel_data = bytes(pixel_array)
            return cel

        elif self.color_depth == 16:
            greyscale_iter = _chunked_iter(cel.pixel_data, 2)
            pixel_array = []
            for pixel in greyscale_iter:
                rgba = (pixel[0] * 3) + pixel[1]
                pixel_array.append(rgba)
            cel.pixel_data = bytes(pixel_array)
            return cel

        else:
            return cel

    def get_pixel_array(self, layers):
        # Start off with an empty RGBA base:
        pixel_array = bytes(4 * self.width * self.height)

        # Blend each layer's cel data one-by-one:
        for cel in self.cels:
            cel = self._convert_to_rgba(cel)
            padded_pixels = self._pad_pixels(cel)
            blend_mode = BLEND_MODES[layers[cel.layer_index].blend_mode]
            pixel_array = self._blend_pixels(pixel_array, padded_pixels, blend_mode)

        return pixel_array


#########################################
#   Aseprite Chunk type definitions
#########################################

class Chunk:
    def __init__(self, size, chunk_type):
        self.size = size
        self.chunk_type = chunk_type


class LayerChunk(Chunk):
    def __init__(self, size, chunk_type, data):
        super().__init__(size, chunk_type)
        fileobj = io.BytesIO(data)
        self.flags = _unpack(WORD, fileobj)
        self.layer_type = _unpack(WORD, fileobj)
        self.child_level = _unpack(WORD, fileobj)
        _ignored_width = _unpack(WORD, fileobj)
        _ignored_height = _unpack(WORD, fileobj)
        self.blend_mode = _unpack(WORD, fileobj)
        self.opacity = _unpack(BYTE, fileobj)
        _zero_unused = _unpack(BYTE * 3, fileobj)
        name_length = _unpack(WORD, fileobj)
        self.name = fileobj.read(name_length)
        if hasattr(self.name, "decode"):
            self.name = self.name.decode('utf8')


class CelChunk(Chunk):
    def __init__(self, size, chunk_type, data):
        super().__init__(size, chunk_type)
        fileobj = io.BytesIO(data)
        self.layer_index = _unpack(WORD, fileobj)
        self.x_pos = _unpack(SHORT, fileobj)
        self.y_pos = _unpack(SHORT, fileobj)
        self.opacity_level = _unpack(BYTE, fileobj)
        self.cel_type = _unpack(WORD, fileobj)
        _zero_unused = _unpack(BYTE * 7, fileobj)
        if self.cel_type == 0:
            self.width = _unpack(WORD, fileobj)
            self.height = _unpack(WORD, fileobj)
            self.pixel_data = fileobj.read()
        elif self.cel_type == 1:
            self.frame_position = _unpack(WORD, fileobj)
        elif self.cel_type == 2:
            self.width = _unpack(WORD, fileobj)
            self.height = _unpack(WORD, fileobj)
            self.pixel_data = zlib.decompress(fileobj.read())


class PathChunk(Chunk):
    def __init__(self, size, chunk_type, data):
        super().__init__(size, chunk_type)


class FrameTagsChunk(Chunk):
    def __init__(self, size, chunk_type, data):
        super().__init__(size, chunk_type)
        # TODO: unpack this data.


class PaletteChunk(Chunk):
    def __init__(self, size, chunk_type, data):
        super().__init__(size, chunk_type)
        fileobj = io.BytesIO(data)
        self.palette_size = _unpack(DWORD, fileobj)
        self.first_color_index = _unpack(DWORD, fileobj)
        self.last_color_index = _unpack(DWORD, fileobj)
        _zero = _unpack(BYTE * 8, fileobj)
        self.palette_dict = {}
        if _unpack(WORD, fileobj) == 1:              # color has name
            size = 7
        else:
            size = 6
        for index in range(self.first_color_index, self.last_color_index+1):
            rgba_data = fileobj.read(size)
            # Ignore the palette names, as they aren't needed:
            r, g, b, a = struct.unpack('<BBBB', rgba_data[:4])
            self.palette_dict[index] = r, g, b, a


class UserDataChunk(Chunk):
    def __init__(self, size, chunk_type, data):
        super().__init__(size, chunk_type)
        # TODO: unpack this data.


class DeprecatedChunk(Chunk):
    def __init__(self, size, chunk_type, data):
        super().__init__(size, chunk_type)


#########################################
#   Image Decoder class definition
#########################################

class AsepriteImageDecoder(ImageDecoder):
    def get_file_extensions(self):
        return ['.ase', '.aseprite']

    def get_animation_file_extensions(self):
        return ['.ase', '.aseprite']

    def decode(self, filename, file):
        header, frames, layers, pitch = self._parse_file(filename, file)
        pixel_data = frames[0].get_pixel_array(layers=layers)
        return ImageData(header.width, header.height, 'RGBA', pixel_data, -pitch)

    def decode_animation(self, file, filename):
        header, frames, layers, pitch = self._parse_file(file, filename)
        animation_frames = []
        for frame in frames:
            pixel_data = frame.get_pixel_array(layers=layers)
            image = ImageData(header.width, header.height, 'RGBA', pixel_data, -pitch)
            animation_frames.append(AnimationFrame(image, frame.duration/1000.0))
        return Animation(animation_frames)

    @staticmethod
    def _parse_file(filename, file):
        if not file:
            file = open(filename, 'rb')

        header = AsepriteHeader(file)
        if header.magic_number != '0xa5e0':
            raise ImageDecodeException("Does not appear to be a valid ASEprite file.")

        if header.color_depth not in (8, 16, 32):
            raise ImageDecodeException("Invalid color depth.")

        global PALETTE_INDEX
        PALETTE_INDEX = header.palette_index

        frames = []
        for _ in range(header.num_frames):
            frame_size = _unpack(DWORD, file)
            magic_number = hex(_unpack(WORD, file))
            if magic_number != '0xf1fa':
                raise ImageDecodeException("Malformed frame. File may be corrupted.")
            num_chunks = _unpack(WORD, file)
            duration = _unpack(WORD, file)
            _zero = _unpack(BYTE * 6, file)
            header_size = struct.calcsize(DWORD + WORD * 3 + BYTE * 6)
            data = file.read(frame_size - header_size)
            frames.append(Frame(num_chunks, duration, header, data))

        # Layers chunk is in the first frame:
        layers = frames[0].layers
        pitch = len('RGBA') * header.width

        file.close()

        return header, frames, layers, pitch


def get_decoders():
    return [AsepriteImageDecoder()]


def get_encoders():
    return []
