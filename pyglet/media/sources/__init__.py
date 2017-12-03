"""Sources for media playback."""

# Collect public interface
from .loader import load, have_ffmpeg
from .base import AudioFormat, VideoFormat, AudioData, SourceInfo
from .base import Source, StreamingSource, StaticSource
# help the docs figure out where these are supposed to live (they live here)
__all__ = [
  'load',
  'have_ffmpeg',
  'AudioFormat',
  'VideoFormat',
  'AudioData',
  'SourceInfo',
  'Source',
  'StreamingSource',
  'StaticSource',
]