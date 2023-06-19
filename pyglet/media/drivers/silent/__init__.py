from . import adaptation


def create_audio_driver():
    return adaptation.SilentDriver()


__all__ = ["create_audio_driver"]
