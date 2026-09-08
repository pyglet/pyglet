import pytest

from ...annotations import skip_if_continuous_integration

pytestmark = skip_if_continuous_integration()

try:
    from pyglet.media.drivers import pulse
    has_pulse = True
except ImportError:
    has_pulse = False

try:
    from pyglet.media.drivers import openal
    has_openal = True
except ImportError:
    has_openal = False

try:
    from pyglet.media.drivers import directsound
    has_directsound = True
except ImportError:
    has_directsound = False


def check_listener_defaults(listener):
    assert listener.volume == 1.0
    assert listener.position == (0, 0, 0)
    assert listener.forward_orientation == (0, 0, -1)
    assert listener.up_orientation == (0, 1, 0)


def check_modifying_values(listener):
    listener.volume = 0.5
    listener.position = (-1, 0, 0)
    listener.forward_orientation = (0, 0, 1)
    listener.up_orientation = (0, -1, 0)
    assert listener.volume == 0.5
    assert listener.position == (-1, 0, 0)
    assert listener.forward_orientation == (0, 0, 1)
    assert listener.up_orientation == (0, -1, 0)


@pytest.mark.skipif(not has_openal, reason="Test requires OpenAL")
def test_openal_listener():
    driver = openal.create_audio_driver()
    listener = driver.get_listener()
    check_listener_defaults(listener=listener)
    check_modifying_values(listener=listener)
    # Need to garbage collect the listener before the driver is deleted
    del listener


@pytest.mark.skipif(not has_pulse, reason="Test requires PulseAudio")
def test_pulse_listener():
    driver = pulse.create_audio_driver()
    listener = driver.get_listener()
    check_listener_defaults(listener=listener)
    check_modifying_values(listener=listener)
    # Need to garbage collect the listener before the driver is deleted
    del listener


@pytest.mark.skipif(not has_directsound, reason="Test requires DirectSound")
def test_directsound_listener():
    driver = directsound.create_audio_driver()
    listener = driver.get_listener()
    check_listener_defaults(listener=listener)
    check_modifying_values(listener=listener)
    # Need to garbage collect the listener before the driver is deleted
    del listener
