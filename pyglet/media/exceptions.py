
class MediaException(Exception):
    pass


class MediaFormatException(MediaException):
    pass


class CannotSeekException(MediaException):
    pass
