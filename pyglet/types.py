"""Holds type aliases used throughout the codebase."""
from typing import Union

__all__ = [
    "Buffer"
]

# This Union alias exists with this name for multiple reasons:
# 1. We can't use typing_extensions.Buffer because pyglet bans runtime
#    Python dependencies.
# 2. We can't use the official Buffer type from PEP-688 until 3.12
#    becomes pyglet's minimum version. This is 2027 according to the
#    current release schedule.
# 3. typing.ByteString is deprecated as of 3.9
Buffer = Union[bytes, bytearray, memoryview]
