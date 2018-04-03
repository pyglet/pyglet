import pyglet

from ...annotations import Platform, require_platform, skip_platform

if pyglet.compat_platform in Platform.LINUX:
    from pyglet.media.drivers import pulse
elif pyglet.compat_platform in Platform.OSX:
    # TODO: test OpenAL for Linux and Windows also, if available.
    from pyglet.media.drivers import openal
elif pyglet.compat_platform in Platform.WINDOWS:
    from pyglet.media.drivers import directsound


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


@skip_platform(Platform.WINDOWS + Platform.LINUX)
def test_openal_listener():
    driver = openal.create_audio_driver()
    listener = driver.get_listener()
    check_listener_defaults(listener=listener)
    check_modifying_values(listener=listener)


@require_platform(Platform.LINUX)
def test_pulse_listener():
    driver = pulse.create_audio_driver()
    listener = driver.get_listener()
    check_listener_defaults(listener=listener)
    check_modifying_values(listener=listener)


@require_platform(Platform.WINDOWS)
def test_directsound_listener():
    driver = directsound.create_audio_driver()
    listener = driver.get_listener()
    check_listener_defaults(listener=listener)
    check_modifying_values(listener=listener)
