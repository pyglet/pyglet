from ctypes import memmove, byref, c_uint32, sizeof, cast, c_void_p, create_string_buffer, POINTER, c_char, \
    c_long

from pyglet.libs.darwin import cf, CFSTR
from pyglet.libs.darwin.coreaudio import kCFURLPOSIXPathStyle, AudioStreamBasicDescription, ca, ExtAudioFileRef, \
    kExtAudioFileProperty_FileDataFormat, kAudioFormatLinearPCM, kAudioFormatFlagIsSignedInteger, \
    kAudioFormatFlagIsPacked, kExtAudioFileProperty_ClientDataFormat, AudioFile_ReadProc, \
    AudioFile_GetSizeProc, AudioBufferList, kExtAudioFileProperty_FileLengthFrames, AudioFileID, err_check
from pyglet.media import StreamingSource, StaticSource
from pyglet.media.codecs import AudioFormat, MediaDecoder, AudioData


class MemoryFileObject:

    def __init__(self, file):
        self.file = file

        if not getattr(self.file, 'seek', None) or not getattr(self.file, 'tell', None):
            raise Exception("File object does not support seeking.")

        # Seek to end of file to get the filesize.
        self.file.seek(0, 2)
        self.file_size = self.file.tell()
        self.file.seek(0)  # Put cursor back at the beginning.
        self.data = []

        def read_data_cb(ref, offset, requested_length, buffer, actual_count):
            self.file.seek(offset)
            data = self.file.read(requested_length)
            data_size = len(data)
            memmove(buffer, data, data_size)
            actual_count.contents.value = data_size  # Actual read.
            return 0

        def getsize_cb(ref):
            return self.file_size

        self.getsize_func = AudioFile_GetSizeProc(getsize_cb)
        self.read_func = AudioFile_ReadProc(read_data_cb)


class CoreAudioSource(StreamingSource):
    def __init__(self, filename, file=None):
        self._bl = None
        self._file = file
        self._deleted = False
        self._file_obj = None
        self._audfile = None
        self._audref = None

        audref = ExtAudioFileRef()
        if file is None:
            fn_str = CFSTR(filename)
            url_ref = cf.CFURLCreateWithFileSystemPath(None, fn_str, kCFURLPOSIXPathStyle, False)

            err_check(ca.ExtAudioFileOpenURL(url_ref, byref(audref)))
            cf.CFRelease(fn_str)
        else:
            self.file_obj = MemoryFileObject(file)

            self._audfile = AudioFileID()

            err_check(ca.AudioFileOpenWithCallbacks(
                None, self.file_obj.read_func, None, self.file_obj.getsize_func, None,
                0,
                byref(self._audfile))
            )

            err_check(ca.ExtAudioFileWrapAudioFileID(self._audfile, False, byref(audref)))

        self._audref = audref

        format_info = AudioStreamBasicDescription()
        size = c_uint32(sizeof(format_info))
        err_check(ca.ExtAudioFileGetProperty(self._audref,
                                             kExtAudioFileProperty_FileDataFormat,
                                             byref(size),
                                             byref(format_info)))

        self.convert_desc = self.convert_format(format_info)

        err_check(ca.ExtAudioFileSetProperty(
            self._audref,
            kExtAudioFileProperty_ClientDataFormat,
            sizeof(self.convert_desc),
            byref(self.convert_desc)
        ))

        length = c_long()
        size = c_uint32(sizeof(format_info))
        # File length.
        err_check(ca.ExtAudioFileGetProperty(
            self._audref,
            kExtAudioFileProperty_FileLengthFrames,
            byref(size),
            byref(length)
        ))

        self.audio_format = AudioFormat(channels=self.convert_desc.mChannelsPerFrame,
                                        sample_size=self.convert_desc.mBitsPerChannel,
                                        sample_rate=int(self.convert_desc.mSampleRate))

        self._num_frames = length.value
        self._bytes_per_frame = self.convert_desc.mBytesPerFrame
        self._duration = self._num_frames / self.convert_desc.mSampleRate
        self._duration_per_frame = self._duration / self._num_frames

    @staticmethod
    def convert_format(original_desc, bitdepth=16):
        adesc = AudioStreamBasicDescription()
        adesc.mSampleRate = original_desc.mSampleRate
        adesc.mFormatID = kAudioFormatLinearPCM
        adesc.mFormatFlags = kAudioFormatFlagIsSignedInteger | kAudioFormatFlagIsPacked
        adesc.mChannelsPerFrame = original_desc.mChannelsPerFrame
        adesc.mBitsPerChannel = bitdepth
        adesc.mBytesPerPacket = original_desc.mChannelsPerFrame * adesc.mBitsPerChannel // 8
        adesc.mFramesPerPacket = 1
        adesc.mBytesPerFrame = adesc.mBytesPerPacket
        return adesc

    def __del__(self):
        if self._file:
            self._file.close()
            self._file = None

        if self._audfile:
            err_check(ca.AudioFileClose(self._audfile))
            self._audfile = None

        if self._audref:
            err_check(ca.ExtAudioFileDispose(self._audref))
            self._audref = None

    def get_audio_data(self, num_bytes, compensation_time=0.0):
        num_frames = c_uint32(num_bytes // self.convert_desc.mBytesPerFrame)

        if not self._bl:
            buffer = create_string_buffer(num_bytes)
            self._bl = AudioBufferList()
            self._bl.mNumberBuffers = 1
            self._bl.mBuffers[0].mNumberChannels = self.convert_desc.mChannelsPerFrame
            self._bl.mBuffers[0].mDataByteSize = num_bytes
            self._bl.mBuffers[0].mData = cast(buffer, c_void_p)

        while True:
            ca.ExtAudioFileRead(self._audref, byref(num_frames), byref(self._bl))

            size = self._bl.mBuffers[0].mDataByteSize
            if not size:
                break

            data = cast(self._bl.mBuffers[0].mData, POINTER(c_char))
            slice = data[:size]
            return AudioData(slice, size, 0.0, size / self.audio_format.sample_rate, [])

        return None

    def seek(self, timestamp):
        self._bl = None  # invalidate buffer list.
        timestamp = max(0.0, min(timestamp, self._duration))
        position = int(timestamp / self._duration_per_frame)
        ca.ExtAudioFileSeek(self._audref, position)


#########################################
#   Decoder class:
#########################################

class CoreAudioDecoder(MediaDecoder):

    def get_file_extensions(self):
        return '.aac', '.ac3', '.aif', '.aiff', '.aifc', '.caf', '.mp3', '.mp4', '.m4a', '.snd', '.au', '.sd2', '.wav'

    def decode(self, filename, file, streaming=True):
        if streaming:
            return CoreAudioSource(filename, file)
        else:
            return StaticSource(CoreAudioSource(filename, file))


def get_decoders():
    return [CoreAudioDecoder()]


def get_encoders():
    return []
