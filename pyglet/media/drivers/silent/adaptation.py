from pyglet.media.drivers.base import AbstractAudioDriver, AbstractAudioPlayer
from pyglet.media.drivers.listener import AbstractListener


class SilentAudioPlayer(AbstractAudioPlayer):

    def delete(self):
        pass

    def play(self):
        pass

    def stop(self):
        pass

    def clear(self):
        pass

    def write(self, audio_data, length):
        pass

    def get_time(self):
        return 0

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

    def prefill_audio(self):
        pass


class SilentDriver(AbstractAudioDriver):

    def create_audio_player(self, source, player):
        return SilentAudioPlayer(source, player)

    def get_listener(self):
        return SilentListener()

    def delete(self):
        pass


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
