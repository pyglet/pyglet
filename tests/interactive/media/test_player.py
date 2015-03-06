from time import sleep

import pyglet
from pyglet.media.player import Player
from pyglet.media.sources import procedural
from pyglet.media.sources.base import StaticSource

from tests.interactive.interactive_test_base import InteractiveTestCase, requires_user_validation

#pyglet.options['debug_media'] = True


@requires_user_validation
class SoundMediaPlayerTestCase(InteractiveTestCase):
    """
    Interactively test the Player in pyglet.media for playing back sounds.
    """

    def test_play_queue(self):
        """Test playing a single sound on the queue."""
        source = procedural.WhiteNoise(1.0)
        player = Player()
        player.play()
        player.queue(source)

        # Pause for the duration of the sound
        sleep(1.0)

        self.user_verify('Did you hear white noise for 1 second?', take_screenshot=False)

    def test_queue_play(self):
        """Test putting a single sound on the queue and then starting the player."""
        source = procedural.WhiteNoise(1.0)
        player = Player()
        player.queue(source)
        player.play()

        # Pause for the duration of the sound
        sleep(1.0)

        self.user_verify('Did you hear white noise for 1 second?', take_screenshot=False)

    def test_pause_queue(self):
        """Test the queue is not played when player is paused."""
        source = procedural.WhiteNoise(1.0)
        player = Player()
        player.pause()
        player.queue(source)

        # Pause for the duration of the sound
        sleep(1.0)

        self.user_verify('Did you not hear any sound?', take_screenshot=False)

    def test_pause_sound(self):
        """Test that a playing sound can be paused."""
        source = procedural.WhiteNoise(60.0)
        player = Player()
        player.queue(source)
        player.play()

        sleep(1.0)
        player.pause()

        self.user_verify('Did you hear white noise for 1 second and is it now silent?', take_screenshot=False)

        player.play()

        self.user_verify('Do you hear white noise again?', take_screenshot=False)

    def test_next_on_end_of_stream(self):
        """Test that multiple items on the queue are played after each other."""
        source1 = procedural.WhiteNoise(1.0)
        source2 = procedural.Sine(1.0)
        player = Player()
        player.queue(source1)
        player.queue(source2)
        player.play()

        sleep(2.0)
        self.user_verify('Did you hear white noise for 1 second and then a tone at 440 Hz (A above middle C)?')

    def test_static_source_wrapping(self):
        """Test that a sound can be recursively wrappend inside a static source."""
        source = procedural.WhiteNoise(1.0)
        source = StaticSource(source)
        source = StaticSource(source)
        player = Player()
        player.queue(source)
        player.play()

        sleep(1.0)

        self.user_verify('Did you hear white noise for 1 second?', take_screenshot=False)

