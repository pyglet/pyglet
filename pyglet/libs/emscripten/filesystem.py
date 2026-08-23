"""Persistent filesystem helpers for Pyodide browser hosts.

The host page registers a ``pyglet_emscripten`` JavaScript module before
importing this module. It supplies the IDBFS operations used for application
data and the OPFS operations used for caches. Custom browser launchers can use
the sibling ``pyglet_emscripten.js`` module to install this bridge.
"""
from __future__ import annotations

from importlib import import_module
from pathlib import PurePosixPath
from typing import Any


def _mount_path(path: str) -> str:
    path = str(PurePosixPath(path))
    if not path.startswith("/"):
        raise ValueError("IDBFS mount paths must be absolute.")
    return path


def _bridge() -> Any:
    try:
        return import_module("pyglet_emscripten")
    except ImportError as exc:
        raise RuntimeError(
            "The browser host has not registered the 'pyglet_emscripten' JavaScript module.",
        ) from exc


async def mount_idbfs(path: str = "/data") -> None:
    """Mount and hydrate an IndexedDB-backed directory.

    Call this once during application startup, before reading persistent
    settings or data from ``path``.
    """
    await _bridge().mount_idbfs(_mount_path(path))


async def sync_idbfs() -> None:
    """Persist changes made under every mounted IDBFS directory."""
    await _bridge().sync_idbfs()


async def mount_opfs(path: str = "/cache") -> None:
    """Mount an Origin Private File System directory for persistent caches."""
    await _bridge().mount_opfs(_mount_path(path))


async def sync_opfs() -> None:
    """Persist changes made under every mounted OPFS directory."""
    await _bridge().sync_opfs()


async def sync_storage() -> None:
    """Persist pyglet's IDBFS data and OPFS cache mounts."""
    await sync_idbfs()
    await sync_opfs()


def unmount_idbfs(path: str = "/data") -> None:
    """Unmount an IndexedDB-backed directory after syncing its changes."""
    _bridge().unmount_idbfs(_mount_path(path))
