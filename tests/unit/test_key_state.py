"""Keyboard state tracking without initializing a window backend."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from types import ModuleType


@pytest.fixture
def key(monkeypatch: pytest.MonkeyPatch) -> ModuleType:
    path = Path(__file__).resolve().parents[2] / 'pyglet' / 'window' / 'key.py'
    spec = spec_from_file_location('_test_window_key', path)
    assert spec is not None
    assert spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, 'compat_platform', 'linux')
    return module


@pytest.mark.parametrize(('symbol_name', 'mask_names'), [
    ('LSHIFT', ('MOD_SHIFT',)),
    ('RCTRL', ('MOD_CTRL',)),
    ('LALT', ('MOD_ALT',)),
    ('RWINDOWS', ('MOD_WINDOWS',)),
    ('LCOMMAND', ('MOD_COMMAND',)),
    ('ROPTION', ('MOD_ALT', 'MOD_OPTION')),
    ('FUNCTION', ('MOD_FUNCTION',)),
])
def test_modifier_transition_with_pre_transition_mask(
    key: ModuleType, symbol_name: str, mask_names: tuple[str, ...],
) -> None:
    keys = key.KeyStateHandler()
    symbol = getattr(key, symbol_name)
    mask = sum(getattr(key, name) for name in mask_names)

    keys.on_key_press(symbol, 0)
    assert keys[symbol]
    assert keys.modifiers == mask

    keys.on_key_release(symbol, mask)
    assert not keys[symbol]
    assert keys.modifiers == 0


def test_either_shift_keeps_modifier_active(key: ModuleType) -> None:
    keys = key.KeyStateHandler()
    keys.on_key_press(key.LSHIFT, 0)
    keys.on_key_press(key.RSHIFT, key.MOD_SHIFT)
    keys.on_key_press(key.LCTRL, key.MOD_SHIFT)
    keys.on_key_release(key.LSHIFT, key.MOD_SHIFT | key.MOD_CTRL)
    assert keys.modifiers == key.MOD_SHIFT | key.MOD_CTRL

    keys.on_key_press(key.A, key.MOD_CTRL)
    assert keys.modifiers == key.MOD_SHIFT | key.MOD_CTRL

    keys.on_key_release(key.RSHIFT, key.MOD_CTRL)
    assert keys.modifiers == key.MOD_CTRL


def test_lock_flags_follow_event_mask(key: ModuleType) -> None:
    keys = key.KeyStateHandler()
    keys.on_key_press(key.CAPSLOCK, key.MOD_CAPSLOCK)
    keys.on_key_release(key.CAPSLOCK, key.MOD_CAPSLOCK)
    assert not keys[key.CAPSLOCK]
    assert keys.modifiers == key.MOD_CAPSLOCK

    keys.on_key_press(key.A, key.MOD_NUMLOCK)
    assert keys.modifiers == key.MOD_NUMLOCK


def test_browser_uses_post_transition_mask(key: ModuleType, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(key, 'compat_platform', 'emscripten')
    keys = key.KeyStateHandler()
    keys.on_key_press(key.LSHIFT, key.MOD_SHIFT)
    keys.on_key_release(key.LSHIFT, key.MOD_SHIFT)
    assert keys.modifiers == key.MOD_SHIFT

    keys.on_key_release(key.LSHIFT, 0)
    assert keys.modifiers == 0


@pytest.mark.parametrize('reset', ['clear', 'on_deactivate'])
def test_reset_clears_keys_and_modifiers(key: ModuleType, reset: str) -> None:
    keys = key.KeyStateHandler()
    keys.on_key_press(key.LSHIFT, key.MOD_CAPSLOCK)
    keys.on_key_press(key.SPACE, key.MOD_SHIFT | key.MOD_CAPSLOCK)
    getattr(keys, reset)()

    assert not keys[key.SPACE]
    assert not keys[key.LSHIFT]
    assert keys.modifiers == 0

    keys.on_key_press(key.LCTRL, 0)
    assert keys[key.LCTRL]
    assert keys.modifiers == key.MOD_CTRL
