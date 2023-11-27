from pyglet.media.drivers.base import AbstractAudioDriver, AbstractAudioPlayer, MediaEvent
from pyglet.media.drivers.listener import AbstractListener
from pyglet.media.player_worker_thread import PlayerWorkerThread


class SilentDriver(AbstractAudioDriver):
    def __init__(self) -> None:
        super().__init__()
        self.worker = PlayerWorkerThread()
        self.worker.start()

    def create_audio_player(self, source, player):
        return SilentAudioPlayer(self, source, player)

    def get_listener(self):
        return SilentListener()

    def delete(self):
        if self.worker is not None:
            self.worker.stop()
            self.worker = None


class SilentListener(AbstractListener):

    def _set_volume(self, volume):
        pass

    def _set_position(self, position):
        pass

    def _set_forward_orientation(self, orientation):
        pass

    def _set_up_orientation(self, orientation):
        pass

    def _set_orientation(self):
        pass


class SilentAudioPlayer(AbstractAudioPlayer):
    def __init__(self, driver, source, player):
        super().__init__(source, player)

        self.driver = driver

        self._pseudo_play_cursor = 0
        self._pseudo_write_cursor = 0

        self._exhausted = False
        self._dispatched_on_eos = False

    def delete(self):
        if self.driver.worker is not None:
            self.driver.worker.remove(self)

    def play(self):
        self.driver.worker.add(self)

    def stop(self):
        self.driver.worker.remove(self)

    def prefill_audio(self):
        self.work()

    def _update_play_cursor(self):
        corrected_time = self.player.time - self.player.last_seek_time
        pc = self.source.audio_format.timestamp_to_bytes_aligned(corrected_time)
        assert pc >= self._pseudo_play_cursor
        self._pseudo_play_cursor = min(self._pseudo_write_cursor, pc)

    def work(self):
        self._update_play_cursor()
        self.dispatch_media_events(self._pseudo_play_cursor)

        if not self._exhausted:
            remaining = max(0, self._pseudo_write_cursor - self._pseudo_play_cursor)
            if remaining > self._buffered_data_comfortable_limit:
                return

            data = self._get_and_compensate_audio_data(
                self.source.audio_format.align(self._buffered_data_ideal_size - remaining),
                self._pseudo_play_cursor)

            if data is None:
                self._exhausted = True
                self._update_play_cursor()
            else:
                self.append_events(self._pseudo_write_cursor, data.events)

                # The silent player always cheats itself to be 100% accurate, compensation is
                # effectless and actually throws off audio syncing as well as accurate
                # on_eos dispatching. Undo it here.
                self._pseudo_write_cursor += data.length - self._compensated_bytes
                self._compensated_bytes = 0
                return

        if (
            self._pseudo_play_cursor >= self._pseudo_write_cursor and
            self._exhausted and
            not self._dispatched_on_eos
        ):
            self._dispatched_on_eos = True
            MediaEvent('on_eos').sync_dispatch_to_player(self.player)

    def clear(self):
        super().clear()
        self._pseudo_play_cursor = 0
        self._pseudo_write_cursor = 0
        self._exhausted = False
        self._dispatched_on_eos = False

    def get_play_cursor(self):
        return self._pseudo_play_cursor

    def set_volume(self, volume):
        pass

    def set_position(self, position):
        pass

    def set_min_distance(self, min_distance):
        pass

    def set_max_distance(self, max_distance):
        pass

    def set_pitch(self, pitch):
        pass

    def set_cone_orientation(self, cone_orientation):
        pass

    def set_cone_inner_angle(self, cone_inner_angle):
        pass

    def set_cone_outer_angle(self, cone_outer_angle):
        pass

    def set_cone_outer_gain(self, cone_outer_gain):
        pass
