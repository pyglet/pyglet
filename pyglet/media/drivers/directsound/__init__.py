from . import adaptation
from .exceptions import DirectSoundException, DirectSoundNativeError


def create_audio_driver():
    return adaptation.DirectSoundDriver()


__all__ = ["create_audio_driver", "DirectSoundException", "DirectSoundNativeError"]
