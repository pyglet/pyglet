"""Paths and persistence notifications for application-created data.

Unlike :mod:`pyglet.resource`, which locates read-only files shipped with an
application, this module provides locations for files created while the
application is running. Files are read and written with the usual Python
filesystem APIs.

=================  ===========================================================
Location           Purpose
=================  ===========================================================
``temporary``      Disposable working files. It may be cleared at any time.
``cache``          Re-creatable files retained between runs, but safe to purge.
``data``           User-created or irreplaceable application content.
``settings``       Preferences, key bindings, and other configuration.
=================  ===========================================================

On desktop platforms cache files live below the application's data directory.
In a browser, data and settings use the IndexedDB-backed ``/data`` mount while
cache uses the Origin Private File System-backed ``/cache`` mount. Both browser
locations require :meth:`Storage.sync` to make writes durable.

Structured settings
-------------------
Named settings sections provide a small dictionary-like API backed by one
human-readable JSON file::

    storage = pyglet.storage.get("my-game")
    window = storage.settings.create(
        "window",
        defaults={"size": [1280, 720], "fullscreen": False},
    )
    window["size"] = [1920, 1080]
    storage.settings.sync()

Defaults fill in missing keys without replacing values that were already
saved. Assign a key to replace one value, or call ``clear`` followed by
``update`` to replace an entire section. Settings values must be JSON
serializable. Use ``storage.settings.path`` or
``storage.settings / "filename"`` for additional files that should live in the
settings directory but do not belong in the JSON document.

Browser persistence is asynchronous internally. :meth:`Storage.sync` returns immediately and
dispatches ``on_sync`` or ``on_sync_error`` when synchronization finishes.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import sys
import tempfile
from collections import deque
from collections.abc import Callable, Iterator, Mapping, MutableMapping
from copy import deepcopy
from pathlib import Path
from typing import Any

from pyglet.event import EventDispatcher
from pyglet.resource import get_data_path, get_settings_path

_VALID_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def _validate_name(name: str, description: str) -> None:
    if not _VALID_NAME.fullmatch(name):
        message = f"{description} must start with a letter or digit and contain only letters, digits, '.', '_', or '-'."
        raise ValueError(message)


def _json_value(value: Any) -> Any:
    """Validate and normalize a value using JSON's actual data model."""
    try:
        return json.loads(json.dumps(value, allow_nan=False))
    except (TypeError, ValueError) as exception:
        raise TypeError("Settings values must be JSON serializable.") from exception


class SettingsSection(MutableMapping[str, Any]):
    """A dictionary-like named section in a :class:`Settings` document."""

    def __init__(self, name: str, data: dict[str, Any]) -> None:
        """Create a view over one section of a settings document."""
        self.name = name
        self._data = data

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        if not isinstance(key, str):
            raise TypeError("Settings keys must be strings.")
        self._data[key] = _json_value(value)

    def __delitem__(self, key: str) -> None:
        del self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"SettingsSection({self.name!r}, {self._data!r})"


class Settings:
    """JSON-backed application settings and their containing directory.

    Use :meth:`create` to obtain named dictionary-like sections. Files that do
    not belong in the JSON document can still be stored beneath ``path``,
    or by using the ``/`` operator directly on this object.
    """

    filename = "settings.json"

    def __init__(self, path: str | os.PathLike[str], sync: Callable[[], bool]) -> None:
        """Load the JSON settings document beneath ``path`` if it exists."""
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        self.file = self.path / self.filename
        self._sync = sync
        self._sections: dict[str, SettingsSection] = {}
        self._data = self._load()

    def _load(self) -> dict[str, Any]:
        if not self.file.exists():
            return {}
        with self.file.open(encoding="utf8") as settings_file:
            data = json.load(settings_file)
        if not isinstance(data, dict):
            message = f"Settings file must contain a JSON object: {self.file}"
            raise ValueError(message)
        return data

    def create(
        self,
        name: str,
        defaults: Mapping[str, Any] | None = None,
    ) -> SettingsSection:
        """Return a named settings section, filling in any missing defaults.

        Existing values are never replaced by defaults, which allows new
        defaults to be added in later application versions without resetting a
        user's choices.
        """
        _validate_name(name, "Settings section name")
        data = self._data.setdefault(name, {})
        if not isinstance(data, dict):
            message = f"Settings section {name!r} is not a JSON object."
            raise TypeError(message)
        if defaults is not None:
            if not isinstance(defaults, Mapping):
                raise TypeError("Settings defaults must be a mapping.")
            for key, value in defaults.items():
                if not isinstance(key, str):
                    raise TypeError("Settings keys must be strings.")
                if key not in data:
                    data[key] = _json_value(deepcopy(value))

        section = self._sections.get(name)
        if section is None:
            section = SettingsSection(name, data)
            self._sections[name] = section
        return section

    def remove(self, name: str) -> None:
        """Remove a settings section.

        Raises:
            KeyError:
                If the section does not exist.
        """
        del self._data[name]
        self._sections.pop(name, None)

    def sync(self) -> bool:
        """Write all sections to JSON and request platform persistence."""
        return self._sync()

    def save(self) -> None:
        """Write all settings sections to the JSON file."""
        temporary = self.file.with_suffix(self.file.suffix + ".tmp")
        with temporary.open("w", encoding="utf8") as settings_file:
            json.dump(self._data, settings_file, indent=2, sort_keys=True, allow_nan=False)
            settings_file.write("\n")
        temporary.replace(self.file)

    def __truediv__(self, child: str | os.PathLike[str]) -> Path:
        return self.path / child

    def __fspath__(self) -> str:
        return os.fspath(self.path)

    def __repr__(self) -> str:
        return f"Settings({str(self.path)!r})"


class _ImmediateSyncBackend:
    persistent = True

    def sync(self, completed: Callable[[], None], _failed: Callable[[Exception], None]) -> None:
        completed()


class _BrowserSyncBackend:
    """Serialize asynchronous browser filesystem synchronization."""

    persistent = True

    def __init__(self) -> None:
        self._active = False
        self._task: Any | None = None
        self._queue: deque[tuple[Callable[[], None], Callable[[Exception], None]]] = deque()

    def sync(self, completed: Callable[[], None], failed: Callable[[Exception], None]) -> None:
        self._queue.append((completed, failed))
        if not self._active:
            self._start_next()

    def _start_next(self) -> None:
        if not self._queue:
            return

        self._active = True
        completed, failed = self._queue.popleft()
        try:
            from pyglet.libs.emscripten.filesystem import sync_storage  # noqa: PLC0415

            task = asyncio.create_task(sync_storage())
            self._task = task
            task.add_done_callback(lambda result: self._finished_task(result, completed, failed))
        except Exception as exception:  # noqa: BLE001 - browser bridges can raise JavaScript implementation errors.
            self._finish(failed, exception)

    def _finished_task(
        self,
        task: Any,
        completed: Callable[[], None],
        failed: Callable[[Exception], None],
    ) -> None:
        try:
            task.result()
        except Exception as exception:  # noqa: BLE001 - preserve browser errors for the application.
            self._finish(failed, exception)
        else:
            self._finish(completed)

    def _finish(self, callback: Callable[..., None], *args: object) -> None:
        self._task = None
        try:
            callback(*args)
        finally:
            self._active = False
            self._start_next()


class Storage(EventDispatcher):
    """Filesystem locations belonging to one application or component.

    Applications will normally obtain one instance with :func:`get`. Multiple
    named instances are supported so reusable libraries, editors with separate
    projects, and test environments can avoid sharing settings or saved data.
    Repeated calls to ``get`` with the same name return the same instance.

    Args:
        name:
            Stable application or component identifier. It may contain ASCII
            letters, digits, dots, underscores, and hyphens, but no path
            separators.

    Events:
        on_sync:
            Dispatched after all synchronization requests made so far have
            completed successfully.
        on_sync_error(error):
            Dispatched when persistent storage could not be synchronized.
    """

    def __init__(self, name: str, *, _backend: Any | None = None) -> None:
        """Create storage paths for ``name`` using the current platform."""
        super().__init__()
        _validate_name(name, "Storage name")

        self.name = name
        self.temporary = Path(tempfile.gettempdir()) / name
        self.data = Path(get_data_path(name))
        settings_path = Path(get_settings_path(name))
        if sys.platform == "emscripten" and settings_path == self.data:
            settings_path = self.data / "settings"
        self.cache = Path("/cache") / name if sys.platform == "emscripten" else self.data / "cache"

        self.temporary.mkdir(parents=True, exist_ok=True)
        self.data.mkdir(parents=True, exist_ok=True)
        settings_path.mkdir(parents=True, exist_ok=True)
        self.cache.mkdir(parents=True, exist_ok=True)

        if _backend is not None:
            self._backend = _backend
        elif sys.platform == "emscripten":
            self._backend = _get_browser_sync_backend()
        else:
            self._backend = _ImmediateSyncBackend()

        self._syncing = False
        self._sync_requested = False
        self.settings = Settings(settings_path, self.sync)

    @property
    def syncing(self) -> bool:
        """Whether a persistent-storage synchronization is in progress."""
        return self._syncing

    @property
    def persistent(self) -> bool:
        """Whether the backend is intended to survive application restarts."""
        return self._backend.persistent

    def sync(self) -> bool:
        """Request that pending writes be committed to persistent storage.

        This method never needs to be awaited. On desktop systems completion
        is immediate. In a browser, the host's ``pyglet_emscripten`` module
        asynchronously synchronizes both the data and cache filesystems.

        If synchronization is already active, the request is coalesced into a
        single follow-up pass. This prevents overlapping saves while ensuring
        that writes made during the active pass are included before ``on_sync``
        is dispatched.
        """
        self.settings.save()
        if self._syncing:
            self._sync_requested = True
            return False

        self._start_sync()
        return True

    def _start_sync(self) -> None:
        self._syncing = True
        self._backend.sync(self._sync_completed, self._sync_failed)

    def _sync_completed(self) -> None:
        if self._sync_requested:
            self._sync_requested = False
            self._start_sync()
            return

        self._syncing = False
        self.dispatch_event("on_sync")

    def _sync_failed(self, error: Exception) -> None:
        self._sync_requested = False
        self._syncing = False
        self.dispatch_event("on_sync_error", error)

    def on_sync(self) -> None:
        """Default handler for successful synchronization."""

    def on_sync_error(self, error: Exception) -> None:
        """Default handler for synchronization failure."""


Storage.register_event_type("on_sync")
Storage.register_event_type("on_sync_error")

_storages: dict[str, Storage] = {}
_browser_sync_backend: _BrowserSyncBackend | None = None


def _get_browser_sync_backend() -> _BrowserSyncBackend:
    global _browser_sync_backend  # noqa: PLW0603
    if _browser_sync_backend is None:
        _browser_sync_backend = _BrowserSyncBackend()
    return _browser_sync_backend


def get(name: str) -> Storage:
    """Return the shared storage object for an application or component.

    Most applications should call this once with a stable identifier and use
    the returned object throughout their lifetime. The name is required so
    saved data remains in the same location if the executable or entry-point
    filename changes.

    Multiple names are allowed primarily for reusable components that must not
    write into their host application's namespace, applications that manage
    independently stored projects or profiles, and isolated tests. Calling
    this function repeatedly with the same name does not create additional
    storage areas; it returns the existing :class:`Storage` instance.
    """
    try:
        return _storages[name]
    except KeyError:
        storage = Storage(name)
        _storages[name] = storage
        return storage
