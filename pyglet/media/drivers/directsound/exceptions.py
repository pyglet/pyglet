from pyglet.media.exceptions import MediaException


class DirectSoundException(MediaException):
    pass


class DirectSoundNativeError(DirectSoundException):
    def __init__(self, hresult):
        self.hresult = hresult

    def __repr__(self):
        return "{}: Error {}".format(self.__class__.__name__, self.hresult)
