from __future__ import annotations

from typing import TYPE_CHECKING

from pyglet.util import CodecRegistry, Decoder, Encoder, DecodeException, EncodeException

if TYPE_CHECKING:
    from typing import BinaryIO
    from pyglet.model import Model, Scene


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
    def decode(self, filename: str, file: BinaryIO | None) -> Scene:
        """Decode the given file object and return a Scene instance.

        Throws ModelDecodeException if there is an error. If passing
        a ``file`` object, ``filename`` should be provided as a hint
        to the file type.
        """
        raise NotImplementedError()


class ModelEncoder(Encoder):

    def encode(self, model: Model, filename: str, file: BinaryIO | None) -> None:
        """Encode the given model to the given file."""
        raise NotImplementedError()


def add_default_codecs() -> None:
    # Add all bundled codecs.

    try:
        from pyglet.model.codecs import obj
        registry.add_decoders(obj)
    except ImportError:
        pass

    try:
        from pyglet.model.codecs import gltf
        registry.add_decoders(gltf)
    except ImportError:
        pass
