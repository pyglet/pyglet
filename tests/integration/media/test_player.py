from __future__ import print_function

import gc
import inspect
import Queue
from tests import mock
import threading
import time
import unittest

import pyglet
#pyglet.options['debug_media'] = True

import pyglet.app  # Will be patched
from pyglet.media import Player
from pyglet.media.sources.procedural import Silence


# TODO: Move to utility module
class EventForwarder(threading.Thread):
    def __init__(self):
        super(EventForwarder, self).__init__()
        self.queue = Queue.Queue()

    def run(self):
        while True:
            destination, event_type, args = self.queue.get()
            if not destination:
                break
            else:
                destination.dispatch_event(event_type, *args)

    def post_event(self, destination, event_type, *args):
        self.queue.put((destination, event_type, args))

    def stop(self):
        self.queue.put((None, None, None))
        self.join()


class PlayerTestCase(unittest.TestCase):
    """Integration tests for the high-level media player.

    Uses the automatically selected driver for the current platform only."""
    def setUp(self):
        self.forwarder = EventForwarder()
        self.forwarder.start()

        self.event_loop_patch = mock.patch('pyglet.app.platform_event_loop',
                                           self.forwarder)
        self.event_loop_patch.start()

    def tearDown(self):
        self.event_loop_patch.stop()
        self.forwarder.stop()

    def test_unreferenced_cleanup(self):
        """Test that the player gets cleaned up if there are no references left to it
        and playback of contained sources has finished."""
        silence = Silence(.1)
        player = Player()
        player_id = id(player)

        @player.event
        def on_player_eos():
            on_player_eos.called = True
        on_player_eos.called = False

        player.queue(silence)
        player.play()
        player = None

        while not on_player_eos.called:
            time.sleep(.1)

        gc.collect()

        for obj in gc.get_objects():
            if isinstance(obj, Player) and id(obj) == player_id:
                self.fail('Player should be cleaned up')
        self.assertListEqual([], gc.garbage, msg='Should not find garbage')

