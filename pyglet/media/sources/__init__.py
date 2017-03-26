"""Sources for media playback."""

# Collect public interface
from .loader import load, have_ffmpeg
from .base import AudioFormat, VideoFormat, AudioData, SourceInfo
from .base import Source, StreamingSource, StaticSource, SourceGroup