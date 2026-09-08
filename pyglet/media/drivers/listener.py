from abc import ABCMeta, abstractmethod


class AbstractListener(metaclass=ABCMeta):
    """The listener properties for positional audio.

    You can obtain the singleton instance of this class by calling
    :meth:`AbstractAudioDriver.get_listener`.
    """

    _volume = 1.0
    _position = (0, 0, 0)
    _forward_orientation = (0, 0, -1)
    _up_orientation = (0, 1, 0)

    @abstractmethod
    def _set_volume(self, volume):
        pass

    volume = property(lambda self: self._volume,
                      lambda self, volume: self._set_volume(volume),
                      doc="""The master volume for sound playback.

        All sound volumes are multiplied by this master volume before being
        played.  A value of 0 will silence playback (but still consume
        resources).  The nominal volume is 1.0.

        :type: float
        """)

    @abstractmethod
    def _set_position(self, position):
        pass

    position = property(lambda self: self._position,
                        lambda self, position: self._set_position(position),
                        doc="""The position of the listener in 3D space.

        The position is given as a tuple of floats (x, y, z).  The unit
        defaults to meters, but can be modified with the listener
        properties.

        :type: 3-tuple of float
        """)

    @abstractmethod
    def _set_forward_orientation(self, orientation):
        pass

    forward_orientation = property(lambda self: self._forward_orientation,
                               lambda self, o: self._set_forward_orientation(o),
                               doc="""A vector giving the direction the
        listener is facing.

        The orientation is given as a tuple of floats (x, y, z), and has
        no unit.  The forward orientation should be orthogonal to the
        up orientation.

        :type: 3-tuple of float
        """)

    @abstractmethod
    def _set_up_orientation(self, orientation):
        pass

    up_orientation = property(lambda self: self._up_orientation,
                              lambda self, o: self._set_up_orientation(o),
                              doc="""A vector giving the "up" orientation
        of the listener.

        The orientation is given as a tuple of floats (x, y, z), and has
        no unit.  The up orientation should be orthogonal to the
        forward orientation.

        :type: 3-tuple of float
        """)

