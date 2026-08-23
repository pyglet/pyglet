from __future__ import annotations
# ruff: noqa: SLF001

import argparse
import json
import subprocess
from types import SimpleNamespace

import pytest

import pyglet
import pyglet.info as info
from pyglet.enums import GraphicsAPI


def test_parse_version() -> None:
    assert info._parse_version("3.1") == (3, 1)


@pytest.mark.parametrize("value", ["3", "three.one", "3.1.2"])
def test_parse_version_rejects_invalid_value(value: str) -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        info._parse_version(value)


def test_parse_graphics_worker_output_uses_prefixed_result() -> None:
    expected = {"backend": "gles3", "success": True}
    output = "native library noise\n" + info._GRAPHICS_WORKER_PREFIX + json.dumps(expected) + "\n"

    assert info._parse_graphics_worker_output(output) == expected


def test_parse_graphics_worker_output_rejects_invalid_json() -> None:
    assert info._parse_graphics_worker_output(info._GRAPHICS_WORKER_PREFIX + "not-json") is None


def test_run_graphics_probe_sets_backend_in_clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "backend": "gles3",
        "requested_version": [3, 1],
        "success": True,
        "actual_api": "gles3",
        "actual_version": [3, 1],
    }

    def fake_run(command, **kwargs):
        assert command[-3:] == ("--graphics-worker", "gles3", "3.1")
        assert kwargs["env"]["PYGLET_BACKEND"] == "gles3"
        assert kwargs["env"]["PYGLET_DEBUG_API"] == "false"
        return SimpleNamespace(
            stdout=info._GRAPHICS_WORKER_PREFIX + json.dumps(payload),
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(info.subprocess, "run", fake_run)

    assert info._run_graphics_probe(GraphicsAPI.OPENGL_ES_3, (3, 1)) == payload


def test_run_graphics_probe_uses_default_version_request(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {"backend": "opengl", "requested_version": None, "success": True}

    def fake_run(command, **_kwargs):
        assert command[-3:] == ("--graphics-worker", "opengl", "default")
        return SimpleNamespace(stdout=info._GRAPHICS_WORKER_PREFIX + json.dumps(payload), stderr="", returncode=0)

    monkeypatch.setattr(info.subprocess, "run", fake_run)

    assert info._run_graphics_probe(GraphicsAPI.OPENGL, None) == payload


def test_run_graphics_probe_reports_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(*_args, **_kwargs):
        raise subprocess.TimeoutExpired("probe", 15)

    monkeypatch.setattr(info.subprocess, "run", fake_run)

    result = info._run_graphics_probe(GraphicsAPI.OPENGL, (3, 3))

    assert result["success"] is False
    assert result["error_type"] == "TimeoutExpired"


def test_graphics_api_family_distinguishes_desktop_and_es() -> None:
    assert info._graphics_api_family(GraphicsAPI.OPENGL) == "desktop"
    assert info._graphics_api_family(GraphicsAPI.OPENGL_2) == "desktop"
    assert info._graphics_api_family(GraphicsAPI.OPENGL_ES_3) == "es"
    assert info._graphics_api_family(GraphicsAPI.OPENGL_ES_2) == "es"


def test_graphics_probe_covers_supported_legacy_and_gles3_versions() -> None:
    assert (GraphicsAPI.OPENGL, None) in info._GRAPHICS_PROBES
    assert (GraphicsAPI.OPENGL, (3, 3)) in info._GRAPHICS_PROBES
    assert (GraphicsAPI.OPENGL_2, (2, 0)) in info._GRAPHICS_PROBES
    assert (GraphicsAPI.OPENGL_2, (2, 1)) in info._GRAPHICS_PROBES
    assert (GraphicsAPI.OPENGL_ES_3, (3, 0)) in info._GRAPHICS_PROBES
    assert (GraphicsAPI.OPENGL_ES_3, (3, 1)) in info._GRAPHICS_PROBES
    assert (GraphicsAPI.OPENGL_ES_3, (3, 2)) in info._GRAPHICS_PROBES


def test_gles31_is_preferred_to_legacy_desktop_gl() -> None:
    gles3 = {"backend": "gles3", "requested_version": [3, 1]}
    gl2 = {"backend": "gl2", "requested_version": [2, 1]}

    assert info._graphics_probe_priority(gles3) > info._graphics_probe_priority(gl2)


def test_default_desktop_request_is_preferred_to_explicit_desktop_minimum() -> None:
    default = {"backend": "opengl", "requested_version": None}
    minimum = {"backend": "opengl", "requested_version": [3, 3]}

    assert info._graphics_probe_priority(default) > info._graphics_probe_priority(minimum)


def test_failed_diagnostic_context_is_created_once_and_reported(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    attempts = 0

    def fail_to_create_window(**_kwargs):
        nonlocal attempts
        attempts += 1
        raise RuntimeError("context rejected")

    requested = SimpleNamespace(major_version=3, minor_version=3)
    config = SimpleNamespace(**{str(pyglet.options.backend): requested})
    monkeypatch.setattr(pyglet.window, "Window", fail_to_create_window)
    monkeypatch.setattr(info, "_first_heading", True)

    info.dump_window_and_backend(config)

    output = capsys.readouterr().out
    assert attempts == 1
    assert "status: context creation failed" in output
    assert "requested version: 3.3" in output
    assert "RuntimeError: context rejected" in output
    assert "Traceback" not in output
    assert "status: unavailable because diagnostic context creation failed" in output
