from __future__ import annotations

import json

import pytest

import pyglet.storage as storage_module
from pyglet.storage import Storage


class DeferredBackend:
    persistent = True

    def __init__(self):
        self.operations = []

    def sync(self, completed, failed):
        self.operations.append((completed, failed))


class ImmediateBackend:
    persistent = True

    @staticmethod
    def sync(completed, _failed):
        completed()


@pytest.fixture
def storage_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(storage_module.tempfile, "gettempdir", lambda: str(tmp_path / "temporary"))
    monkeypatch.setattr(storage_module, "get_data_path", lambda name: str(tmp_path / "data" / name))
    monkeypatch.setattr(storage_module, "get_settings_path", lambda name: str(tmp_path / "settings" / name))
    return tmp_path


def test_storage_creates_platform_directories(storage_paths):
    storage = Storage("example-game")

    assert storage.temporary == storage_paths / "temporary" / "example-game"
    assert storage.data == storage_paths / "data" / "example-game"
    assert storage.settings.path == storage_paths / "settings" / "example-game"
    expected_cache = (
        storage_paths / "data" / "example-game" / "cache"
        if storage_module.sys.platform != "emscripten"
        else storage_module.Path("/cache/example-game")
    )
    assert storage.cache == expected_cache
    assert storage.temporary.is_dir()
    assert storage.data.is_dir()
    assert storage.settings.path.is_dir()
    assert storage.cache.is_dir()


def test_settings_create_applies_defaults_without_overwriting_values(storage_paths):
    storage = Storage("example-game")
    window = storage.settings.create("window", {"size": (800, 600), "fullscreen": False})

    assert window["size"] == [800, 600]
    window["fullscreen"] = True
    same_window = storage.settings.create("window", {"fullscreen": False, "vsync": True})

    assert same_window is window
    assert dict(window) == {"size": [800, 600], "fullscreen": True, "vsync": True}


def test_settings_sync_writes_all_sections_to_one_json_file(storage_paths):
    storage = Storage("example-game", _backend=ImmediateBackend())
    storage.settings.create("window", {"size": [100, 100]})
    storage.settings.create("audio")["volume"] = 0.5

    assert storage.settings.sync() is True
    assert json.loads(storage.settings.file.read_text(encoding="utf8")) == {
        "audio": {"volume": 0.5},
        "window": {"size": [100, 100]},
    }


def test_settings_are_loaded_by_a_new_storage_instance(storage_paths):
    first = Storage("example-game")
    first.settings.create("window")["size"] = [1280, 720]
    first.settings.sync()

    second = Storage("example-game")

    assert second.settings.create("window")["size"] == [1280, 720]


def test_settings_directory_still_accepts_regular_files(storage_paths):
    storage = Storage("example-game")
    custom_file = storage.settings / "controls.ini"

    custom_file.write_text("jump=space", encoding="utf8")

    assert custom_file.parent == storage.settings.path
    assert custom_file.read_text(encoding="utf8") == "jump=space"


def test_settings_reject_non_json_values(storage_paths):
    storage = Storage("example-game")
    window = storage.settings.create("window")

    with pytest.raises(TypeError, match="JSON serializable"):
        window["callback"] = object()


def test_settings_reject_invalid_section_names(storage_paths):
    storage = Storage("example-game")

    with pytest.raises(ValueError, match="Settings section name"):
        storage.settings.create("../window")


@pytest.mark.parametrize("name", ["", ".", "../game", "game/save", r"game\save"])
def test_storage_rejects_names_that_can_escape_the_namespace(name):
    with pytest.raises(ValueError, match="Storage name"):
        Storage(name)


def test_get_returns_one_dispatcher_per_name(monkeypatch, storage_paths):
    monkeypatch.setattr(storage_module, "_storages", {})

    first = storage_module.get("example-game")
    second = storage_module.get("example-game")
    other = storage_module.get("example-editor")

    assert first is second
    assert first is not other


def test_desktop_sync_dispatches_immediately(storage_paths):
    storage = Storage("example-game", _backend=ImmediateBackend())
    completions = []
    storage.set_handler("on_sync", lambda: completions.append(True))

    assert storage.sync() is True
    assert completions == [True]
    assert storage.syncing is False


def test_overlapping_sync_requests_are_coalesced(storage_paths):
    backend = DeferredBackend()
    storage = Storage("example-game", _backend=backend)
    completions = []
    storage.set_handler("on_sync", lambda: completions.append(True))

    assert storage.sync() is True
    assert storage.sync() is False
    assert storage.sync() is False
    assert len(backend.operations) == 1

    backend.operations[0][0]()
    assert storage.syncing is True
    assert completions == []
    assert len(backend.operations) == 2

    backend.operations[1][0]()
    assert storage.syncing is False
    assert completions == [True]


def test_sync_error_clears_queued_work(storage_paths):
    backend = DeferredBackend()
    storage = Storage("example-game", _backend=backend)
    failures = []
    storage.set_handler("on_sync_error", failures.append)

    storage.sync()
    storage.sync()
    error = RuntimeError("quota exceeded")
    backend.operations[0][1](error)

    assert failures == [error]
    assert storage.syncing is False
    assert len(backend.operations) == 1
