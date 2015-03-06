"""Sources for media playback."""

# Collect public interface
from .loader import load, have_avbin
from .base import AudioFormat, VideoFormat, AudioData, SourceInfo, Source, StreamingSource, \
        StaticSource, SourceGroup

