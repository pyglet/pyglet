from __future__ import annotations

import sys

import pytest


@pytest.mark.skipif(sys.platform != "win32", reason="Windows COM is available only on Windows")
def test_guid_without_arguments_is_a_new_null_guid() -> None:
    from pyglet.libs.win32.com import GUID

    first = GUID()
    second = GUID()

    assert bytes(first) == bytes(16)
    assert first == second
    assert first is not second

    first.Data1 = 1
    assert second.Data1 == 0


@pytest.mark.skipif(sys.platform != "win32", reason="Windows COM is available only on Windows")
def test_guid_copy_is_independent() -> None:
    from pyglet.libs.win32.com import GUID

    original = GUID(1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11)
    copied = original.copy()

    assert copied == original
    assert copied is not original

    copied.Data1 = 99
    copied.Data4[0] = 88
    assert original.Data1 == 1
    assert original.Data4[0] == 4
