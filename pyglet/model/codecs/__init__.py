from __future__ import annotations

from typing import TYPE_CHECKING

from pyglet.util import CodecRegistry, Decoder, Encoder, DecodeException, EncodeException

if TYPE_CHECKING:
    from typing import BinaryIO
    from pyglet.model import Model
    from pyglet.graphics import Batch, Group


registry = CodecRegistry()
add_decoders = registry.add_decoders
add_encoders = registry.add_encoders
get_decoders = registry.get_decoders
get_encoders = registry.get_encoders


class ModelDecodeException(DecodeException):
    pass


class ModelEncodeException(EncodeException):
    pass


class ModelDecoder(Decoder):
    def decode(self, filename: str, file: BinaryIO | None, batch: Batch | None, group: Group | None) -> Model:
        """Decode the given file object and return an instance of `Model`.
        Throws ModelDecodeException if there is an error.  filename
        can be a file type hint.
        """
        raise NotImplementedError()


class ModelEncoder(Encoder):

    def encode(self, model: Model, filename: str, file: BinaryIO | None) -> None:
        """Encode the given model to the given file.  filename
        provides a hint to the file format desired.  options are
        encoder-specific, and unknown options should be ignored or
        issue warnings.
        """
        raise NotImplementedError()


def add_default_codecs() -> None:
    # Add all bundled codecs. These should be listed in order of
    # preference. This is called automatically by pyglet.model.

    try:
        from pyglet.model.codecs import obj
        registry.add_decoders(obj)
    except ImportError:
        pass

    # TODO: complete this decoder, and enable it by default
    # try:
    #     from pyglet.model.codecs import gltf
    #     add_decoders(gltf)
    # except ImportError:
    #     pass
