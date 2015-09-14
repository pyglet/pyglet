import pytest

import pyglet
from pyglet.media.player import Player

#pyglet.options['debug_media'] = True


@pytest.mark.only_interactive
def test_playback(interactive, test_data):
    """Test playing back sound files."""
    player = Player()
    player.play()

    sound = test_data.get_file('media', 'alert.wav')
    source = pyglet.media.load(sound, streaming=False)
    player.queue(source)

    interactive.ask_question('Can you hear the sound playing?')

    sound2 = test_data.get_file('media', 'receive.wav')
    source2 = pyglet.media.load(sound2, streaming=False)
    player.queue(source2)
    player.next_source()

    interactive.ask_question('Can you hear the second sound playing?')


@pytest.mark.only_interactive
def test_playback_fire_and_forget(interactive, test_data):
    """Test playing back sound files using fire and forget."""
    sound = test_data.get_file('media', 'alert.wav')
    source = pyglet.media.load(sound, streaming=False)
    source.play()

    interactive.ask_question('Can you hear the sound playing?')

