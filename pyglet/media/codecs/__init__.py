import os.path


_decoders = []              # List of registered MediaDecoders
_encoders = []              # List of registered MediaEncoders
_decoder_extensions = {}    # Map str -> list of matching MediaDecoders
_encoder_extensions = {}    # Map str -> list of matching MediaEncoders


class MediaDecodeException(Exception):
    exception_priority = 10


class MediaEncodeException(Exception):
    pass


class MediaDecoder(object):
    def get_file_extensions(self):
        """Return a list of accepted file extensions, e.g. ['.wav', '.ogg']
        Lower-case only.
        """
        return []

    def decode(self, file, filename, streaming=True):
        """Read the given file object and return an instance of `Source`
        or `StreamingSource`. 
        Throws MediaDecodeException if there is an error.  `filename`
        can be a file type hint.
        """
        raise NotImplementedError()


# class MediaEncoder(object):
#     def get_file_extensions(self):
#         """Return a list of accepted file extensions, e.g. ['.wav', '.ogg']
#         Lower-case only.
#         """
#         return []
# 
#     def encode(self, media, file, filename):
#         """Encode the given source to the given file.  `filename`
#         provides a hint to the file format desired.  options are
#         encoder-specific, and unknown options should be ignored or
#         issue warnings.
#         """
#         raise NotImplementedError()


def get_decoders(filename=None):
    """Get an ordered list of decoders to attempt.  filename can be used
     as a hint for the filetype.
    """
    decoders = []
    if filename:
        extension = os.path.splitext(filename)[1].lower()
        decoders += _decoder_extensions.get(extension, [])
    decoders += [e for e in _decoders if e not in decoders]
    return decoders


# def get_encoders(filename=None):
#     """Get an ordered list of encoders to attempt.  filename can be used
#     as a hint for the filetype.
#     """
#     encoders = []
#     if filename:
#         extension = os.path.splitext(filename)[1].lower()
#         encoders += _encoder_extensions.get(extension, [])
#     encoders += [e for e in _encoders if e not in encoders]
#     return encoders


def add_decoders(module):
    """Add a decoder module.  The module must define `get_decoders`.  Once
    added, the appropriate decoders defined in the codec will be returned by
    pyglet.media.codecs.get_decoders.
    """
    for decoder in module.get_decoders():
        _decoders.append(decoder)
        for extension in decoder.get_file_extensions():
            if extension not in _decoder_extensions:
                _decoder_extensions[extension] = []
            _decoder_extensions[extension].append(decoder)


# def add_encoders(module):
#     """Add an encoder module.  The module must define `get_encoders`.  Once
#     added, the appropriate encoders defined in the codec will be returned by
#     pyglet.media.codecs.get_encoders.
#     """
#     for encoder in module.get_encoders():
#         _encoders.append(encoder)
#         for extension in encoder.get_file_extensions():
#             if extension not in _encoder_extensions:
#                 _encoder_extensions[extension] = []
#             _encoder_extensions[extension].append(encoder)


def add_default_media_codecs():
    # Add the codecs we know about.  These should be listed in order of
    # preference.  This is called automatically by pyglet.media.

    try:
        from pyglet.media.codecs import wave
        add_decoders(wave)
    except ImportError:
        pass
