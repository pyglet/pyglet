"""Browser implementations of pyglet's file dialogs."""
from __future__ import annotations

import asyncio
from typing import Any

import js  # noqa: F821
from pyodide.ffi import create_proxy  # noqa: F821

from pyglet.window.dialog.base import FileOpenDialogBase, FileSaveDialogBase
from pyglet.window.emscripten.files import import_files


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

        def cleanup() -> None:
            input_element.removeEventListener("change", change_proxy)
            input_element.removeEventListener("cancel", cancel_proxy)
            input_element.remove()
            change_proxy.destroy()
            cancel_proxy.destroy()

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

        change_proxy = create_proxy(change)
        cancel_proxy = create_proxy(cancel)
        input_element.addEventListener("change", change_proxy)
        input_element.addEventListener("cancel", cancel_proxy)
        # This must happen in the calling input event to retain browser user activation.
        input_element.click()


class EmscriptenFileSaveDialog(FileSaveDialogBase):
    """A browser cannot provide the writable OS path required by this API."""

    def open(self) -> None:
        raise NotImplementedError(
            "FileSaveDialog is not supported in browsers; use a browser download "
            "or a File System Access API integration instead.",
        )
