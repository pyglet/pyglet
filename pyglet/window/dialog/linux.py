"""Loads a file dialog utilizing TKinter.

Linux does not have any unified dialog API or utility across distros.

While many support a GTK or KDialog, it's not guaranteed. Because of this, TKinter is utilized
as the main caller. When Tkinter cannot create a system dialog, it will create a custom
created file explorer, thus guaranteeing a dialog on any Linux system.

This is done in a separate process as Tk has its own event loop.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor as _ProcessPoolExecutor
from pathlib import Path

import pyglet
from pyglet.window.dialog.base import FileOpenDialogBase, FileSaveDialogBase


class _TkFileDialogBackend:

    executor = _ProcessPoolExecutor(max_workers=1)
    _dialog = None

    @staticmethod
    def _open_dialog(dialog):
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        try:
            return dialog.show()
        finally:
            root.destroy()

    def open(self):
        future = self.executor.submit(self._open_dialog, self._dialog)
        future.add_done_callback(self._dispatch_event)

    def _dispatch_event(self, future):
        raise NotImplementedError

class TkFileOpenDialog(_TkFileDialogBackend, FileOpenDialogBase):
    def __init__(
        self, title: str="Open File", initial_dir: str | Path=Path.cwd(), initial_file: str | None=None,
            filetypes: list[tuple[str, str]] | None=None, multiple: bool=False) -> None:
        super().__init__(title, initial_dir, initial_file, filetypes, multiple)
        from tkinter import filedialog
        self._dialog = filedialog.Open(title=title,
                                       initialdir=initial_dir,
                                       initialfile=initial_file,
                                       filetypes=filetypes or (),
                                       multiple=multiple)

    def _dispatch_event(self, future):
        pyglet.app.platform_event_loop.post_event(self, "on_dialog_open", future.result())


class TkFileSaveDialog(_TkFileDialogBackend, FileSaveDialogBase):
    def __init__(self, title="Save As", initial_dir=Path.cwd(), initial_file=None, filetypes=None, default_ext=""):
        super().__init__(title, initial_dir, initial_file, filetypes, default_ext)
        from tkinter import filedialog

        self._dialog = filedialog.SaveAs(
            title=title,
            initialdir=initial_dir,
            initialfile=initial_file or (),
            filetypes=filetypes or (),
            defaultextension=default_ext,
        )

    def _dispatch_event(self, future):
        pyglet.app.platform_event_loop.post_event(self, "on_dialog_save", future.result())