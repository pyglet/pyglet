import io

import pytest

from pyglet import image
from pyglet.image.codecs import ImageEncodeException
from pyglet.image.codecs.png import PNGImageDecoder, PNGImageEncoder


class RecordingEncoder:
    def __init__(self, fail):
        self.fail = fail
        self.stream = None

    def encode(self, picture, filename, stream):
        # Retain the stream so the assertion does not depend on refcounting.
        self.stream = stream
        stream.write(b'encoded image')
        if self.fail:
            raise ImageEncodeException('encoding failed')


@pytest.mark.parametrize('explicit_encoder', [False, True])
@pytest.mark.parametrize('fail', [False, True])
@pytest.mark.parametrize('provided_file', [False, True])
def test_save_closes_only_files_it_opens(tmp_path, monkeypatch, explicit_encoder, fail, provided_file):
    picture = image.SolidColorImagePattern().create_image(1, 1)
    destination = tmp_path / 'image.test'
    stream = io.BytesIO() if provided_file else None
    encoder = RecordingEncoder(fail)
    if not explicit_encoder:
        monkeypatch.setattr(image._codec_registry, 'encode', encoder.encode)
    try:
        kwargs = {'file': stream}
        if explicit_encoder:
            kwargs['encoder'] = encoder
        if fail:
            with pytest.raises(ImageEncodeException, match='encoding failed'):
                picture.save(str(destination), **kwargs)
        else:
            picture.save(str(destination), **kwargs)

        if provided_file:
            assert encoder.stream is stream
            assert not stream.closed
            assert stream.getvalue() == b'encoded image'
            stream.write(b' more data')
        else:
            assert encoder.stream.closed
            assert destination.read_bytes() == b'encoded image'
    finally:
        if encoder.stream is not None:
            encoder.stream.close()


@pytest.mark.parametrize('fail', [False, True])
def test_save_without_filename_keeps_supplied_stream_open(fail):
    picture = image.SolidColorImagePattern().create_image(1, 1)
    encoder = RecordingEncoder(fail)
    with io.BytesIO() as stream:
        if fail:
            with pytest.raises(ImageEncodeException, match='encoding failed'):
                picture.save(file=stream, encoder=encoder)
        else:
            picture.save(file=stream, encoder=encoder)
        assert not stream.closed
        assert stream.getvalue() == b'encoded image'


class RetainingPNGEncoder(PNGImageEncoder):
    def encode(self, picture, filename, stream):
        self.stream = stream
        super().encode(picture, filename, stream)


def test_saved_png_is_readable_before_output_stream_finalization(tmp_path):
    picture = image.SolidColorImagePattern((20, 40, 60, 255)).create_image(1, 1)
    encoder = RetainingPNGEncoder()
    destination = tmp_path / 'image.png'
    try:
        picture.save(str(destination), encoder=encoder)
        assert encoder.stream.closed
        decoded = image.load(str(destination), decoder=PNGImageDecoder())
        assert decoded.width == decoded.height == 1
        assert decoded.get_data('RGBA', 4) == bytes((20, 40, 60, 255))
    finally:
        encoder.stream.close()
