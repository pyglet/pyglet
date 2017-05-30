import os.path


_decoders = []              # List of registered ModelDecoders
_encoders = []              # List of registered ModelEncoders
_decoder_extensions = {}    # Map str -> list of matching ModelDecoders
_encoder_extensions = {}    # Map str -> list of matching ModelEncoders


class ModelDecodeException(Exception):
    exception_priority = 10


class ModelEncodeException(Exception):
    pass


class ModelDecoder(object):
    def get_file_extensions(self):
        """Return a list of accepted file extensions, e.g. ['.obj', '.gox']
        Lower-case only.
        """
        return []

    def decode(self, file, filename):
        """Decode the given file object and return an instance of `Model`.
        Throws ModelDecodeException if there is an error.  filename
        can be a file type hint.
        """
        raise NotImplementedError()


class ModelEncoder(object):
    def get_file_extensions(self):
        """Return a list of accepted file extensions, e.g. ['.obj', '.gox']
        Lower-case only.
        """
        return []

    def encode(self, model, file, filename):
        """Encode the given model to the given file.  filename
        provides a hint to the file format desired.  options are
        encoder-specific, and unknown options should be ignored or
        issue warnings.
        """
        raise NotImplementedError()


def get_encoders(filename=None):
    """Get an ordered list of encoders to attempt.  filename can be used
    as a hint for the filetype.
    """
    encoders = []
    if filename:
        extension = os.path.splitext(filename)[1].lower()
        encoders += _encoder_extensions.get(extension, [])
    encoders += [e for e in _encoders if e not in encoders]
    return encoders


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


def add_decoders(module):
    """Add a decoder module.  The module must define `get_decoders`.  Once
    added, the appropriate decoders defined in the codec will be returned by
    pyglet.model.codecs.get_decoders.
    """
    for decoder in module.get_decoders():
        _decoders.append(decoder)
        for extension in decoder.get_file_extensions():
            if extension not in _decoder_extensions:
                _decoder_extensions[extension] = []
            _decoder_extensions[extension].append(decoder)


def add_encoders(module):
    """Add an encoder module.  The module must define `get_encoders`.  Once
    added, the appropriate encoders defined in the codec will be returned by
    pyglet.model.codecs.get_encoders.
    """
    for encoder in module.get_encoders():
        _encoders.append(encoder)
        for extension in encoder.get_file_extensions():
            if extension not in _encoder_extensions:
                _encoder_extensions[extension] = []
            _encoder_extensions[extension].append(encoder)


def add_default_model_codecs():
    # Add the codecs we know about.  These should be listed in order of
    # preference.  This is called automatically by pyglet.model.

    try:
        from pyglet.model.codecs import obj
        add_decoders(obj)
    except ImportError:
        pass
