import os
import pyglet
from pyglet.media.player import Player

from tests.interactive.interactive_test_base import InteractiveTestCase, only_interactive

#pyglet.options['debug_media'] = True


@only_interactive
class PlayerTest(InteractiveTestCase):
    def test_playback(self):
        player = Player()
        player.play()

        sound = self.get_test_data_file('media', 'alert.wav')
        source = pyglet.media.load(sound, streaming= False)
        player.queue(source)

        self.user_verify('Can you hear the sound playing?', take_screenshot=False)

        sound2 = self.get_test_data_file('media', 'receive.wav')
        source2 = pyglet.media.load(sound2, streaming=False)
        player.queue(source2)
        player.next_source()

        self.user_verify('Can you hear the second sound playing?', take_screenshot=False)


