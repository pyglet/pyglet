import pytest
from pyglet.libs.darwin.coreaudio import err_str_db, kAudioFileFileNotFoundError
from tests.annotations import require_platform, Platform


@require_platform(Platform.OSX)
@pytest.mark.parametrize("key", ["some_key", kAudioFileFileNotFoundError])
def test_coreaudio__try_to_change_key_and_value_of_err_str_db__type_error_raised(key: str):
    with pytest.raises(TypeError):
        err_str_db[key] = "some_value"
