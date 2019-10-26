import re
import struct

from concurrent.futures import ProcessPoolExecutor

from pyglet.media.exceptions import MediaDecodeException
from pyglet.media.codecs.base import StreamingSource, AudioData, AudioFormat, StaticSource
from pyglet.media.codecs import MediaDecoder


# This module uses code from Project Nayuki:
# https://www.nayuki.io/page/simple-flac-implementation


class FLACDecodeException(MediaDecodeException):
    pass


FIXED_PREDICTION_COEFFICIENTS = ((), (1,), (2, -1), (3, -3, 1), (4, -6, 4, -1))


def _initializer(filename, numchannels, sample_size):
    """Function to open a copy of the file locally in each Process."""
    global _file
    global _numchannels
    global _sample_size
    _file = open(filename, 'rb')
    _numchannels = numchannels
    _sample_size = sample_size


def decode_frame(offset):
    try:
        # Read a ton of header fields, and ignore most of them
        numchannels = _numchannels
        sample_size = _sample_size
        _file.seek(offset)
        inp = BitInputStream(_file)

        temp = inp.read_byte()
        if temp == -1:
            return False
        sync = temp << 6 | inp.read_uint(6)
        if sync != 0x3FFE:
            raise FLACDecodeException("Sync code expected")

        inp.read_uint(1)
        inp.read_uint(1)
        blocksizecode = inp.read_uint(4)
        sampleratecode = inp.read_uint(4)
        chanasgn = inp.read_uint(4)
        inp.read_uint(3)
        inp.read_uint(1)

        temp = inp.read_uint(8)
        while temp >= 0b11000000:
            inp.read_uint(8)
            temp = (temp << 1) & 0xFF

        if blocksizecode == 1:
            blocksize = 192
        elif 2 <= blocksizecode <= 5:
            blocksize = 576 << blocksizecode - 2
        elif blocksizecode == 6:
            blocksize = inp.read_uint(8) + 1
        elif blocksizecode == 7:
            blocksize = inp.read_uint(16) + 1
        elif 8 <= blocksizecode <= 15:
            blocksize = 256 << (blocksizecode - 8)
        else:
            raise FLACDecodeException("Invalid Blocksize")

        if sampleratecode == 12:
            inp.read_uint(8)
        elif sampleratecode in (13, 14):
            inp.read_uint(16)

        crc8 = inp.read_byte()

        # Decode each channel's subframe, then skip footer
        if 0 <= chanasgn <= 7:
            samples = [decode_subframe(inp, blocksize, sample_size) for _ in range(chanasgn + 1)]
        elif 8 <= chanasgn <= 10:
            temp0 = decode_subframe(inp, blocksize, sample_size + (1 if (chanasgn == 9) else 0))
            temp1 = decode_subframe(inp, blocksize, sample_size + (0 if (chanasgn == 9) else 1))
            if chanasgn == 8:
                for i in range(blocksize):
                    temp1[i] = temp0[i] - temp1[i]
            elif chanasgn == 9:
                for i in range(blocksize):
                    temp0[i] += temp1[i]
            elif chanasgn == 10:
                for i in range(blocksize):
                    side = temp1[i]
                    right = temp0[i] - (side >> 1)
                    temp1[i] = right
                    temp0[i] = right + side
            samples = [temp0, temp1]
        else:
            raise FLACDecodeException("Reserved channel assignment")

        inp.align_to_byte()
        inp.read_byte()
        inp.read_byte()

        # Write the decoded samples
        fmt = str(blocksize * numchannels) + 'h'
        if sample_size == 8:
            return struct.pack(fmt, *(samples[i][j] + 128 for j in range(blocksize) for i in range(numchannels)))
        else:
            return struct.pack(fmt, *(samples[i][j] for j in range(blocksize) for i in range(numchannels)))
    except:
        return b""


def decode_subframe(inp, blocksize, sampledepth):
    inp.read_uint(1)
    subframe_type = inp.read_uint(6)
    shift = inp.read_uint(1)
    if shift == 1:
        while inp.read_uint(1) == 0:
            shift += 1
    sampledepth -= shift

    if subframe_type == 0:  # Constant coding
        result = [inp.read_signed_int(sampledepth)] * blocksize
    elif subframe_type == 1:  # Verbatim coding
        result = [inp.read_signed_int(sampledepth) for _ in range(blocksize)]
    elif 8 <= subframe_type <= 12:
        result = decode_fixed_prediction_subframe(inp, subframe_type - 8, blocksize, sampledepth)
    elif 32 <= subframe_type <= 63:
        result = decode_linear_predictive_coding_subframe(inp, subframe_type - 31, blocksize, sampledepth)
    else:
        raise FLACDecodeException("Reserved subframe type")
    return [(v << shift) for v in result]


def decode_fixed_prediction_subframe(inp, predorder, blocksize, sampledepth):
    result = [inp.read_signed_int(sampledepth) for _ in range(predorder)]
    decode_residuals(inp, blocksize, result)
    restore_linear_prediction(result, FIXED_PREDICTION_COEFFICIENTS[predorder], 0)
    return result


def decode_linear_predictive_coding_subframe(inp, lpcorder, blocksize, sampledepth):
    result = [inp.read_signed_int(sampledepth) for _ in range(lpcorder)]
    precision = inp.read_uint(4) + 1
    shift = inp.read_signed_int(5)
    coefs = [inp.read_signed_int(precision) for _ in range(lpcorder)]
    decode_residuals(inp, blocksize, result)
    restore_linear_prediction(result, coefs, shift)
    return result


def decode_residuals(inp, blocksize, result):
    method = inp.read_uint(2)
    if method >= 2:
        raise FLACDecodeException("Reserved residual coding method")
    parambits = [4, 5][method]
    escapeparam = [0xF, 0x1F][method]

    partitionorder = inp.read_uint(4)
    numpartitions = 1 << partitionorder
    if blocksize % numpartitions != 0:
        raise FLACDecodeException("Block size not divisible by number of Rice partitions")

    for i in range(numpartitions):
        count = blocksize >> partitionorder
        if i == 0:
            count -= len(result)
        param = inp.read_uint(parambits)
        if param < escapeparam:
            result.extend(inp.read_rice_signed_int(param) for _ in range(count))
        else:
            numbits = inp.read_uint(5)
            result.extend(inp.read_signed_int(numbits) for _ in range(count))


def restore_linear_prediction(result, coefs, shift):
    for i in range(len(coefs), len(result)):
        result[i] += sum((result[i - 1 - j] * c) for (j, c) in enumerate(coefs)) >> shift


class BitInputStream:
    __slots__ = 'inp', 'bitbuffer', 'bitbufferlen'

    def __init__(self, inp):
        self.inp = inp
        self.bitbuffer = 0
        self.bitbufferlen = 0

    def align_to_byte(self):
        self.bitbufferlen -= self.bitbufferlen % 8

    def read_byte(self):
        if self.bitbufferlen >= 8:
            return self.read_uint(8)
        else:
            result = self.inp.read(1)
            if len(result) == 0:
                return -1
            return result[0]

    def read_uint(self, n):
        bitbuffer = self.bitbuffer
        bitbufferlen = self.bitbufferlen

        while bitbufferlen < n:
            temp = self.inp.read(1)
            if len(temp) == 0:
                raise EOFError()
            temp = temp[0]
            bitbuffer = (bitbuffer << 8) | temp
            bitbufferlen += 8
        bitbufferlen -= n
        result = (bitbuffer >> bitbufferlen) & ((1 << n) - 1)
        bitbuffer &= (1 << bitbufferlen) - 1

        self.bitbuffer = bitbuffer
        self.bitbufferlen = bitbufferlen
        return result

    def read_signed_int(self, n):
        temp = self.read_uint(n)
        temp -= (temp >> (n - 1)) << n
        return temp

    def read_rice_signed_int(self, param):
        read_uint = self.read_uint
        val = 0
        while read_uint(1) == 0:
            val += 1
        val = (val << param) | read_uint(param)
        return (val >> 1) ^ -(val & 1)

    def close(self):
        self.inp.close()


def _find_frame_indicies(data):
    magic1 = struct.pack('BB', int('11111111', 2), int('11111000', 2))
    magic2 = struct.pack('BB', int('11111111', 2), int('11111001', 2))
    indices1 = [m.start() for m in re.finditer(magic1, data)]
    indices2 = [m.start() for m in re.finditer(magic2, data)]
    indices = indices1 + indices2
    indices.sort()
    return indices


#########################################
#   Source class:
#########################################
class FLACSource(StreamingSource):
    def __init__(self, filename, file=None):
        if file is None:
            file = open(filename, 'rb')

        self.frame_indices = _find_frame_indicies(file.read())
        self.frame_index = 0
        file.seek(0)
        self._file = BitInputStream(file)
        self._filename = filename

        if file.read(4) != b'fLaC':
            raise FLACDecodeException("Does not appear to be a FLAC file.")

        samplerate = numchannels = bits_per_sample = numsamples = None

        last = False
        while not last:
            last = self._file.read_uint(1) != 0
            block_type = self._file.read_uint(7)
            length = self._file.read_uint(24)
            if block_type == 0:  # Stream info block
                min_block_size = self._file.read_uint(16)  # in samples
                max_block_size = self._file.read_uint(16)  # in samples
                min_frame_size = self._file.read_uint(24)  # in bytes,  0 == unknown
                max_frame_size = self._file.read_uint(24)  # in bytes,  0 == unknown
                samplerate = self._file.read_uint(20)
                numchannels = self._file.read_uint(3) + 1
                bits_per_sample = self._file.read_uint(5) + 1
                numsamples = self._file.read_uint(36)
                self._file.read_uint(128)
            else:   # Skip other metadata blocks
                for i in range(length):
                    self._file.read_byte()

        for offset in self.frame_indices:
            if offset < self._file.inp.tell():
                self.frame_indices.remove(offset)

        if not samplerate:
            raise FLACDecodeException("Stream info metadata block absent")
        if bits_per_sample % 8 != 0:
            raise FLACDecodeException("Sample depth {} not supported".format(bits_per_sample))

        self._numsamples = numsamples
        self._duration = float(numsamples) / samplerate / 60
        self.audio_format = AudioFormat(numchannels, bits_per_sample, samplerate)

        self.executor = ProcessPoolExecutor(max_workers=3, initializer=_initializer,
                                            initargs=(filename, numchannels, bits_per_sample))

    def __del__(self):
        self._file.close()

    def get_audio_data(self, num_bytes, compensation_time=0.0):

        data = b''

        while not data and (self.frame_index <= len(self.frame_indices)):
            offset = self.frame_indices[self.frame_index]
            future = self.executor.submit(decode_frame, offset)
            data += future.result()
            self.frame_index += 1

        if not data:
            return None

        return AudioData(data, len(data), timestamp=0.1, duration=0.5, events=[])

    def save(self, filename="output.wav"):
        with open(filename, 'wb') as out:
            numsamples = self._numsamples
            numchannels = self.audio_format.channels
            samplerate = self.audio_format.sample_rate
            sample_size = self.audio_format.sample_size

            # Start writing WAV file headers
            sampledatalen = numsamples * numchannels * (sample_size // 8)

            out.write(b"RIFF")
            out.write(struct.pack("<I", sampledatalen + 36))
            out.write(b"WAVE")
            out.write(b"fmt ")
            out.write(struct.pack("<IHHIIHH",
                                  16,
                                  0x0001,
                                  numchannels,
                                  samplerate,
                                  samplerate * numchannels * (sample_size // 8),
                                  numchannels * (sample_size // 8),
                                  sample_size))
            out.write(b"data")
            out.write(struct.pack("<I", sampledatalen))

            import time
            start = time.time()
            futures = [self.executor.submit(decode_frame, offset) for offset in self.frame_indices]
            print("elapsed future making", time.time() - start)

            while futures:
                data = futures.pop(0).result()
                out.write(data)

    def seek(self, timestamp):
        pass


#########################################
#   Decoder class:
#########################################
class FLACDecoder(MediaDecoder):

    def get_file_extensions(self):
        return '.flac',

    def decode(self, file, filename, streaming=True):
        if streaming:
            return FLACSource(filename, file)
        else:
            return StaticSource(FLACSource(filename, file))


def get_decoders():
    return [FLACDecoder()]


def get_encoders():
    return []
