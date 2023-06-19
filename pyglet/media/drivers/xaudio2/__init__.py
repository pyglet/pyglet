from . import adaptation


def create_audio_driver():
    return adaptation.XAudio2Driver()


__all__ = ["create_audio_driver"]
