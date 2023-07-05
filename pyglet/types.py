"""Holds type aliases used throughout the codebase."""
import ctypes
from typing import Union

__all__ = [
    "Buffer"
]

# This Union alias has the given name & members for multiple reasons:
# 1. We can't use typing_extensions.Buffer because pyglet bans runtime
#    Python dependencies.
# 2. We can't use the official Buffer type from PEP-688 until 3.12
#    becomes pyglet's minimum version. This is 2027 according to the
#    current release schedule.
# 3. typing.ByteString is deprecated as of 3.9
# 4. ctypes.Array is useful for integrating with other data sources but
#    will not be recognized without explicit inclusion due to lack of
#    buffer protocol support.
Buffer = Union[bytes, bytearray, memoryview, ctypes.Array]
