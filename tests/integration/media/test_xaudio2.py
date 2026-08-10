"""Test XAudio2-specific driver behavior using the real Windows audio engine."""

from __future__ import annotations

import threading
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

import pyglet
from pyglet.media.codecs import AudioFormat
from pyglet.media.player import AudioPlayer
from pyglet.media.synthesis import Silence

from ...annotations import Platform, require_platform, skip_if_continuous_integration

try:
    from pyglet.media.drivers import xaudio2
    from pyglet.media.drivers.xaudio2 import interface
except ImportError:
    xaudio2 = interface = None


pytestmark = [skip_if_continuous_integration(), require_platform(Platform.WINDOWS)]


@pytest.fixture
def driver():
    driver = xaudio2.create_audio_driver()
    yield driver
    driver.delete()


@pytest.fixture
def interface_driver():
    driver = interface.XAudio2Driver()
    yield driver
    driver.delete()


def _return_voices(driver, voices) -> None:
    for voice in voices:
        driver.return_voice(voice, deque())
    pyglet.clock.tick()


def test_driver_create_delete() -> None:
    driver = xaudio2.create_audio_driver()
    driver.delete()


def test_critical_error_only_requests_restart(interface_driver) -> None:
    assert not interface_driver._restart_requested.is_set()

    interface_driver._engine_callback.OnCriticalError(-1)

    assert interface_driver._restart_requested.is_set()


def test_source_voice_is_reused_from_pool(interface_driver) -> None:
    audio_format = AudioFormat(2, 16, 48_000)
    player = SimpleNamespace(create_buffer_end_callback=lambda: lambda _context: None)
    voice = interface_driver.get_source_voice(audio_format, player)

    _return_voices(interface_driver, (voice,))
    reused_voice = interface_driver.get_source_voice(audio_format, player)

    try:
        assert reused_voice is voice
    finally:
        _return_voices(interface_driver, (reused_voice,))


def test_concurrent_source_voice_acquisition_has_unique_ownership(interface_driver) -> None:
    audio_format = AudioFormat(2, 16, 48_000)
    start = threading.Barrier(8)

    def acquire_voice():
        player = SimpleNamespace(create_buffer_end_callback=lambda: lambda _context: None)
        start.wait()
        return interface_driver.get_source_voice(audio_format, player)

    with ThreadPoolExecutor(max_workers=8) as executor:
        for _ in range(50):
            futures = [executor.submit(acquire_voice) for _ in range(8)]
            voices = [future.result() for future in futures]

            try:
                assert len(voices) == len(set(voices))
                assert set(voices) == set(interface_driver.active_voices)
            finally:
                _return_voices(interface_driver, voices)

    assert not interface_driver.active_voices
    assert not interface_driver._resetting_voices


def test_source_voice_acquisition_waits_for_pool_transaction(interface_driver) -> None:
    audio_format = AudioFormat(2, 16, 48_000)
    player = SimpleNamespace(create_buffer_end_callback=lambda: lambda _context: None)
    started = threading.Event()

    def acquire_voice():
        started.set()
        return interface_driver.get_source_voice(audio_format, player)

    with ThreadPoolExecutor(max_workers=1) as executor:
        with interface_driver.lock:
            future = executor.submit(acquire_voice)
            assert started.wait(1)
            time.sleep(0.01)
            assert not future.done()

        voice = future.result()

    _return_voices(interface_driver, (voice,))


def test_buffer_end_callback_never_waits_for_player_lock(driver) -> None:
    """XAudio2's callback must hand work to the audio worker without blocking."""
    source = Silence(1.0)
    player = AudioPlayer()
    player.queue(source)
    audio_player = driver.create_audio_player(source, player)
    player._audio_player = audio_player
    callback_finished = threading.Event()

    def invoke_callback() -> None:
        audio_player._xa2_source_voice._callback.OnBufferEnd(None)
        callback_finished.set()

    try:
        # If the callback takes _audio_data_lock, as the previous design did,
        # it cannot finish until this block exits.
        with audio_player._audio_data_lock:
            callback_thread = threading.Thread(target=invoke_callback)
            callback_thread.start()
            assert callback_finished.wait(0.2)

        callback_thread.join()
        audio_player.work()  # Drain the notification on the worker-side path.
    finally:
        player.delete()


def test_engine_reset_replaces_voice_preserves_cursor_and_resumes(driver) -> None:
    source = Silence(2.0)
    player = AudioPlayer()
    player.queue(source)
    audio_player = driver.create_audio_player(source, player)
    player._audio_player = audio_player
    driver._xa2_driver.volume = 0.4
    assert driver._xa2_driver.volume == pytest.approx(0.4)
    player.play()
    time.sleep(0.08)

    try:
        audio_player.work()
        cursor_before_reset = audio_player.get_play_cursor()
        old_engine = driver._xa2_driver._xaudio2
        old_voice = audio_player._xa2_source_voice

        driver._xa2_driver._engine_callback.OnCriticalError(-1)
        driver._xa2_driver._check_state(0)

        assert driver._xa2_driver._xaudio2 is not old_engine
        assert audio_player._xa2_source_voice is not old_voice
        assert audio_player._xa2_source_voice is not None
        assert audio_player._playing
        assert audio_player.get_play_cursor() >= cursor_before_reset
        assert driver._xa2_driver.volume == pytest.approx(0.4)

        time.sleep(0.05)
        audio_player.work()
        assert audio_player.get_play_cursor() > cursor_before_reset
    finally:
        player.delete()
