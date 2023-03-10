from ctypes import c_void_p, c_int, c_bool, Structure, c_uint32, util, cdll, c_uint, c_double, POINTER, c_int64, \
    CFUNCTYPE

from pyglet.libs.darwin import CFURLRef

lib = util.find_library('CoreAudio')

if lib is None:
    lib = '/System/Library/Frameworks/CoreAudio.framework/CoreAudio'

ca = cdll.LoadLibrary(lib)


class AudioStreamPacketDescription(Structure):
    _fields_ = [
        ('mStartOffset', c_int64),
        ('mVariableFramesInPacket', c_uint32),
        ('mDataByteSize', c_uint32)
    ]


class AudioStreamBasicDescription(Structure):
    _fields_ = [
        ('mSampleRate', c_double),
        ('mFormatID', c_uint32),
        ('mFormatFlags', c_uint32),
        ('mBytesPerPacket', c_uint32),
        ('mFramesPerPacket', c_uint32),
        ('mBytesPerFrame', c_uint32),
        ('mChannelsPerFrame', c_uint32),
        ('mBitsPerChannel', c_uint32),
        ('mReserved', c_uint32)
    ]

    def __repr__(self):
        return f"AudioStreamBasicDescription(sample_rate={self.mSampleRate}, channels={self.mChannelsPerFrame}, " \
               f"fmt={self.mFormatID}, bytes_per_packet={self.mBytesPerPacket}, bits={self.mBitsPerChannel}, " \
               f"frames_per_packet={self.mFramesPerPacket}, bytes_per_frame={self.mBytesPerFrame})"


class AudioBuffer(Structure):
    _fields_ = [
        ("mNumberChannels", c_uint),
        ("mDataByteSize", c_uint),
        ("mData", c_void_p),
    ]


class AudioBufferList(Structure):
    _fields_ = [
        ("mNumberBuffers", c_uint),
        ("mBuffers", AudioBuffer * 1),
    ]


kCFURLPOSIXPathStyle = 0
ExtAudioFilePropertyID = c_uint32
OSStatus = c_int

ExtAudioFileRef = c_void_p

ca.ExtAudioFileOpenURL.restype = c_int
ca.ExtAudioFileOpenURL.argtypes = [CFURLRef, ExtAudioFileRef]

ca.ExtAudioFileGetProperty.restype = c_int
ca.ExtAudioFileGetProperty.argtypes = [ExtAudioFileRef, ExtAudioFilePropertyID, POINTER(c_uint32), c_void_p]

ca.ExtAudioFileSetProperty.restype = c_int
ca.ExtAudioFileSetProperty.argtypes = [ExtAudioFileRef, ExtAudioFilePropertyID, c_uint32, c_void_p]

ca.ExtAudioFileOpenURL.restype = OSStatus
ca.ExtAudioFileOpenURL.argtypes = [CFURLRef, ExtAudioFileRef]

AudioFileTypeID = c_uint32
AudioFileID = c_void_p

AudioFile_ReadProc = CFUNCTYPE(c_int, c_void_p, c_int64, c_uint32, c_void_p, POINTER(c_uint32))
AudioFile_GetSizeProc = CFUNCTYPE(c_int64, c_void_p)

ca.AudioFileOpenWithCallbacks.restype = OSStatus
ca.AudioFileOpenWithCallbacks.argtypes = [c_void_p, AudioFile_ReadProc, c_void_p, AudioFile_GetSizeProc, c_void_p,
                                          AudioFileTypeID, POINTER(AudioFileID)]

ca.ExtAudioFileWrapAudioFileID.restype = OSStatus
ca.ExtAudioFileWrapAudioFileID.argtypes = [AudioFileID, c_bool, POINTER(ExtAudioFileRef)]

ca.ExtAudioFileRead.restype = OSStatus
ca.ExtAudioFileRead.argtypes = [ExtAudioFileRef, POINTER(c_uint32), POINTER(AudioBufferList)]

ca.ExtAudioFileSeek.restype = OSStatus
ca.ExtAudioFileSeek.argtypes = [ExtAudioFileRef, c_int64]

ca.ExtAudioFileDispose.restype = OSStatus
ca.ExtAudioFileDispose.argtypes = [ExtAudioFileRef]

ca.AudioFileClose.restype = OSStatus
ca.AudioFileClose.argtypes = [AudioFileID]

kCFAllocatorDefault = None


def c_literal(literal):
    """Example 'xyz' -> 7895418.
    Used for some CoreAudio constants."""
    num = 0
    for idx, char in enumerate(literal):
        num |= ord(char) << (len(literal) - idx - 1) * 8
    return num


kAudioFilePropertyMagicCookieData = c_literal('mgic')
kExtAudioFileProperty_FileDataFormat = c_literal('ffmt')
kExtAudioFileProperty_ClientDataFormat = c_literal('cfmt')
kExtAudioFileProperty_FileLengthFrames = c_literal('#frm')
kAudioFormatLinearPCM = c_literal('lpcm')

kAudioFormatFlagIsFloat = 1 << 0
kAudioFormatFlagIsBigEndian = 1 << 1
kAudioFormatFlagIsSignedInteger = 1 << 2
kAudioFormatFlagIsPacked = 1 << 3
kAudioFormatFlagsNativeEndian = 0
kAudioFormatFlagsCanonical = kAudioFormatFlagIsFloat | kAudioFormatFlagsNativeEndian | kAudioFormatFlagIsPacked
kAudioQueueProperty_MagicCookie = c_literal('aqmc')

# ERRORS:
kAudio_UnimplementedError = -4
kAudio_FileNotFoundError = -43
kAudio_ParamError = -50
kAudio_MemFullError = -108

kAudioFileUnspecifiedError = c_literal('wht?')  # 0x7768743F, 2003334207
kAudioFileUnsupportedFileTypeError = c_literal('typ?')  # 0x7479703F, 1954115647
kAudioFileUnsupportedDataFormatError = c_literal('fmt?')  # 0x666D743F, 1718449215
kAudioFileUnsupportedPropertyError = c_literal('pty?')  # 0x7074793F, 1886681407
kAudioFileBadPropertySizeError = c_literal('!siz')  # 0x2173697A,  561211770
kAudioFilePermissionsError = c_literal('prm?')  # 0x70726D3F, 1886547263
kAudioFileNotOptimizedError = c_literal('optm')  # 0x6F70746D, 1869640813
# file format specific error codes
kAudioFileInvalidChunkError = c_literal('chk?')  # 0x63686B3F, 1667787583
kAudioFileDoesNotAllow64BitDataSizeError = c_literal('off?')  # 0x6F66663F, 1868981823
kAudioFileInvalidPacketOffsetError = c_literal('pck?')  # 0x70636B3F, 1885563711
kAudioFileInvalidFileError = c_literal('dta?')  # 0x6474613F, 1685348671
kAudioFileOperationNotSupportedError = c_literal('op?')  # 0x6F703F3F
# general file error codes
kAudioFileNotOpenError = -38
kAudioFileEndOfFileError = -39
kAudioFilePositionError = -40
kAudioFileFileNotFoundError = -43

err_str_db = {
    kAudioFileUnspecifiedError: "An unspecified error has occurred.",
    kAudioFileUnsupportedFileTypeError: "The file type is not supported.",
    kAudioFileUnsupportedDataFormatError: "The data format is not supported by this file type.",
    kAudioFileUnsupportedPropertyError: "The property is not supported.",
    kAudioFileBadPropertySizeError: "The size of the property data was not correct.",
    kAudioFilePermissionsError: "The operation violated the file permissions.",
    kAudioFileNotOptimizedError: "The chunks following the audio data chunk are preventing the extension of the audio data chunk. To write more data, you must optimize the file.",
    kAudioFileInvalidChunkError: "Either the chunk does not exist in the file or it is not supported by the file.",
    kAudioFileDoesNotAllow64BitDataSizeError: "The file offset was too large for the file type. The AIFF and WAVE file format types have 32-bit file size limits.",
    kAudioFileInvalidPacketOffsetError: "A packet offset was past the end of the file, or not at the end of the file when a VBR format was written, or a corrupt packet size was read when the packet table was built.",
    kAudioFileInvalidFileError: "The file is malformed, or otherwise not a valid instance of an audio file of its type.",
    kAudioFileOperationNotSupportedError: "The operation cannot be performed.",
    kAudioFileNotOpenError: "The file is closed.",
    kAudioFileEndOfFileError: "End of file.",
    kAudioFilePositionError: "Invalid file position.",
    kAudioFileFileNotFoundError: "File not found.",
}


def err_check(err):
    if err != 0:
        raise Exception(err, err_str_db.get(err, "Unknown Error"))
