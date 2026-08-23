"""Browser implementations of pyglet's file dialogs."""
from __future__ import annotations

import asyncio
from typing import Any

import js  # noqa: F821

from pyglet.libs.emscripten.files import import_files
from pyglet.libs.emscripten.proxies import ProxyRegistry
from pyglet.window.dialog.base import FileOpenDialogBase, FileSaveDialogBase


def _accept_types(filetypes: list[tuple[str, str]] | None) -> str:
    """Convert pyglet's file patterns into an HTML ``accept`` attribute."""
    if not filetypes:
        return ""

    patterns: list[str] = []
    for _, extensions in filetypes:
        for pattern in extensions.replace(";", " ").split():
            normalized = pattern[1:] if pattern.startswith("*") else pattern
            if normalized.startswith("."):
                patterns.append(normalized)
    return ",".join(patterns)


class EmscriptenFileOpenDialog(FileOpenDialogBase):
    """Open a browser file picker and import its selection into the VFS."""

    def open(self) -> None:
        input_element = js.document.createElement("input")
        input_element.type = "file"
        input_element.multiple = self.multiple
        input_element.accept = _accept_types(self.filetypes)
        input_element.style.display = "none"
        js.document.body.appendChild(input_element)
        proxies = ProxyRegistry()

        def cleanup() -> None:
            input_element.remove()
            proxies.destroy()

        async def changed() -> None:
            try:
                self.dispatch_event("on_dialog_open", await import_files([
                    input_element.files.item(index) for index in range(input_element.files.length)
                ]))
            finally:
                cleanup()

        def change(_event: Any) -> None:
            self._task = asyncio.create_task(changed())

        def cancel(_event: Any) -> None:
            try:
                self.dispatch_event("on_dialog_open", [])
            finally:
                cleanup()

        proxies.add_event_listener(input_element, "change", change)
        proxies.add_event_listener(input_element, "cancel", cancel)
        # This must happen in the calling input event to retain browser user activation.
        input_element.click()


class EmscriptenFileSaveDialog(FileSaveDialogBase):
    """A browser cannot provide the writable OS path required by this API."""

    def open(self) -> None:
        raise NotImplementedError(
            "FileSaveDialog is not supported in browsers; use a browser download "
            "or a File System Access API integration instead.",
        )
