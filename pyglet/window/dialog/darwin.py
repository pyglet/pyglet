from __future__ import annotations

from pathlib import Path

from pyglet.libs.darwin import ObjCClass, ns_to_py, nsstr_to_py, AutoReleasePool, pystr_to_ns, py_to_ns
from pyglet.libs.darwin.cocoapy.runtime import get_callback_block, ObjCBlock
from pyglet.window.dialog.base import FileOpenDialogBase, FileSaveDialogBase

NSOpenPanel = ObjCClass('NSOpenPanel')
NSSavePanel = ObjCClass('NSSavePanel')
NSURL = ObjCClass('NSURL')


class MacOSFileOpenDialog(FileOpenDialogBase):
    _cb_block: ObjCBlock | None = None
    def __init__(
        self, title: str="Open File", initial_dir: str | Path=Path.cwd(), initial_file: str | None=None,
            filetypes: list[tuple[str, str]] | None=None, multiple: bool=False) -> None:
        super().__init__(title, initial_dir, initial_file, filetypes, multiple)
        self.blocking = False

    def _dispatch_event(self, files):
        self.dispatch_event("on_dialog_open", files)

    def open(self):
        """Initial_file is not supported on Mac."""
        with AutoReleasePool():
            url = Path(self.initial_dir).as_posix()
            nsurl_path = NSURL.fileURLWithPath_(pystr_to_ns(url))
            panel = NSOpenPanel.openPanel()
            panel.setAllowsMultipleSelection_(self.multiple)
            panel.setDirectoryURL_(nsurl_path)
            panel.setMessage_(pystr_to_ns(self.title))

            if self.filetypes:
                allowed = []
                for name, exts in self.filetypes:
                    for ext in exts.split(" "):
                        strip_endings = ext.lstrip("*").lstrip(".")
                        allowed.append(pystr_to_ns(strip_endings))  # mac wants extension without "."
                panel.setAllowedFileTypes_(py_to_ns(allowed))

            if self.blocking:
                result = panel.runModal()

                if result == 1:
                    files = [nsstr_to_py(_url.path()) for _url in ns_to_py(panel.URLs())]
                else:
                    files = []
                self._dispatch_event(files)
            else:
                if MacOSFileOpenDialog._cb_block is not None:
                    raise Exception("An existing dialog is already open.")

                def handler(_result: int):
                    try:
                        if _result == 1:
                            files = [nsstr_to_py(_url.path()) for _url in ns_to_py(panel.URLs())]
                        else:
                            files = []
                        self._dispatch_event(files)
                    finally:
                        MacOSFileOpenDialog._cb_block = None

                MacOSFileOpenDialog._cb_block = get_callback_block(handler, encoding=[b"v", b"l"])
                panel.beginWithCompletionHandler_(MacOSFileOpenDialog._cb_block)


class MacOSFileSaveDialog(FileSaveDialogBase):
    _cb_block = None
    def __init__(self, title="Save As", initial_dir=Path.cwd(), initial_file=None, filetypes=None, default_ext=""):
        super().__init__(title, initial_dir, initial_file, filetypes, default_ext)
        self.blocking = False

    def open(self):
        """Initial_file is not supported on Mac."""
        with AutoReleasePool():
            url = Path(self.initial_dir).as_posix()
            nsurl_path = NSURL.fileURLWithPath_(pystr_to_ns(url))
            panel = NSSavePanel.savePanel()
            panel.setDirectoryURL_(nsurl_path)
            panel.setMessage_(pystr_to_ns(self.title))
            if self.initial_file:
                panel.setNameFieldStringValue_(pystr_to_ns(self.initial_file))

            if self.filetypes:
                allowed = []
                for name, exts in self.filetypes:
                    for ext in exts.split(" "):
                        strip_endings = ext.lstrip("*").lstrip(".")
                        allowed.append(pystr_to_ns(strip_endings))  # mac wants extension without "."
                panel.setAllowedFileTypes_(py_to_ns(allowed))
            else:
                panel.setAllowedFileTypes_(py_to_ns([pystr_to_ns(self.default_ext)]))
            panel.setAllowsOtherFileTypes_(True)
            panel.setShowsContentTypes_(True)
            if self.blocking:
                result = panel.runModal()

                if result == 1:
                    self._dispatch_event(nsstr_to_py(panel.URL().path()))
                else:  # cancelled
                    self._dispatch_event("")
            else:
                if MacOSFileSaveDialog._cb_block is not None:
                    raise Exception("An existing dialog is already open.")

                def handler(_result: int):
                    try:
                        if _result == 1:
                            self._dispatch_event(nsstr_to_py(panel.URL().path()))
                        else:  # cancelled
                            self._dispatch_event([])
                    finally:
                        MacOSFileSaveDialog._cb_block = None

                MacOSFileSaveDialog._cb_block = get_callback_block(handler, encoding=[b"v", b"l"])
                panel.beginWithCompletionHandler_(MacOSFileSaveDialog._cb_block)

    def _dispatch_event(self, filename: str):
        self.dispatch_event("on_dialog_save", filename)