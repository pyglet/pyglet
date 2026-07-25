from . import adaptation


def create_audio_driver():
    return adaptation.JSAudioDriver()


__all__ = ["create_audio_driver"]
