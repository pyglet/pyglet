"""
Interactively test the Player in pyglet.media for playing back sounds.
"""
import pytest

import pyglet
pyglet.options['debug_media'] = False
from pyglet.media.player import Player
from pyglet.media import synthesis
from pyglet.media.codecs.base import StaticSource


@pytest.mark.requires_user_validation
def test_playback(event_loop, test_data):
    """Test playing back sound files."""
    player = Player()
    player.on_player_eos = event_loop.interrupt_event_loop
    player.play()

    sound = test_data.get_file('media', 'alert.wav')
    source = pyglet.media.load(sound, streaming=False)
    player.queue(source)
    event_loop.run_event_loop()

    event_loop.ask_question('Did you hear the alert sound playing?', screenshot=False)

    sound2 = test_data.get_file('media', 'receive.wav')
    source2 = pyglet.media.load(sound2, streaming=False)
    player.queue(source2)
    player.play()
    event_loop.run_event_loop()

    event_loop.ask_question('Did you hear the receive sound playing?', screenshot=False)


@pytest.mark.requires_user_validation
def test_playback_fire_and_forget(event_loop, test_data):
    """Test playing back sound files using fire and forget."""
    sound = test_data.get_file('media', 'alert.wav')
    source = pyglet.media.load(sound, streaming=False)
    player = source.play()
    player.on_player_eos = event_loop.interrupt_event_loop
    event_loop.run_event_loop()

    event_loop.ask_question('Did you hear the alert sound playing?', screenshot=False)


@pytest.mark.requires_user_validation
def test_play_queue(event_loop):
    """Test playing a single sound on the queue."""
    source = synthesis.WhiteNoise(1.0)
    player = Player()
    player.on_player_eos = event_loop.interrupt_event_loop
    player.play()
    player.queue(source)
    event_loop.run_event_loop()

    event_loop.ask_question('Did you hear white noise for 1 second?', screenshot=False)

@pytest.mark.requires_user_validation
def test_queue_play(event_loop):
    """Test putting a single sound on the queue and then starting the player."""
    source = synthesis.WhiteNoise(1.0)
    player = Player()
    player.on_player_eos = event_loop.interrupt_event_loop
    player.queue(source)
    player.play()
    event_loop.run_event_loop()

    event_loop.ask_question('Did you hear white noise for 1 second?', screenshot=False)

@pytest.mark.requires_user_validation
def test_pause_queue(event_loop):
    """Test the queue is not played when player is paused."""
    source = synthesis.WhiteNoise(1.0)
    player = Player()
    player.pause()
    player.queue(source)

    # Run for the duration of the sound
    event_loop.run_event_loop(1.0)

    event_loop.ask_question('Is it silent?', screenshot=False)

@pytest.mark.requires_user_validation
def test_pause_sound(event_loop):
    """Test that a playing sound can be paused."""
    source = synthesis.WhiteNoise(60.0)
    player = Player()
    player.queue(source)
    player.play()

    event_loop.run_event_loop(1.0)
    player.pause()
    event_loop.ask_question('Did you hear white noise for 1 second and is it now silent?',
                            screenshot=False)

    player.play()
    event_loop.ask_question('Do you hear white noise again?', screenshot=False)

    player.delete()
    event_loop.ask_question('Is it silent again?', screenshot=False)

@pytest.mark.requires_user_validation
def test_next_on_end_of_stream(event_loop):
    """Test that multiple items on the queue are played after each other."""
    source1 = synthesis.WhiteNoise(1.0)
    source2 = synthesis.Sine(1.0)
    player = Player()
    player.on_player_eos = event_loop.interrupt_event_loop
    player.queue(source1)
    player.queue(source2)
    player.play()

    event_loop.run_event_loop()
    event_loop.ask_question('Did you hear white noise for 1 second and then a tone at 440 Hz'
                            '(A above middle C)?', screenshot=False)

@pytest.mark.requires_user_validation
def test_static_source_wrapping(event_loop):
    """Test that a sound can be recursively wrappend inside a static source."""
    source = synthesis.WhiteNoise(1.0)
    source = StaticSource(source)
    source = StaticSource(source)
    player = Player()
    player.on_player_eos = event_loop.interrupt_event_loop
    player.queue(source)
    player.play()

    event_loop.run_event_loop()
    event_loop.ask_question('Did you hear white noise for 1 seconds?', screenshot=False)

