import pytest
from pyglet.libs.darwin.coreaudio import err_str_db, kAudioFileFileNotFoundError
from tests.annotations import require_platform, Platform


@require_platform(Platform.OSX)
def test_coreaudio__try_to_add_key_and_value_to_err_str_db__type_error_raised():
    with pytest.raises(TypeError):
        err_str_db["some_key"] = "some_value"


@require_platform(Platform.OSX)
def test_coreaudio__try_to_change_key_and_value_in_err_str_db__type_error_raised():
    with pytest.raises(TypeError):
        err_str_db[kAudioFileFileNotFoundError] = "some_value"
