import os, sys

from wydget import event, widgets, layouts
from wydget.dialogs import base

if sys.platform == 'darwin':
    default_dir = os.path.expanduser('~/Desktop')
elif sys.platform in ('win32', 'cygwin'):
    default_dir = 'c:/'
else:
    default_dir = os.path.expanduser('~/Desktop')

class FileOpen(base.Dialog):
    id = '-file-dialog'
    name = 'file-dialog'
    classes = ('dialog', )

    def __init__(self, parent, path=default_dir, callback=None, **kw):
        kw['border'] = 'black'
        kw['bgcolor'] = 'white'
        kw['padding'] = 2
        kw['width'] = 300
        super(FileOpen, self).__init__(parent, **kw)
        self.callback = callback

        self.layout = layouts.Vertical(self, halign='left', padding=2)

        label = widgets.Label(self, 'Select File to Open',
            classes=('title',), bgcolor="aaa", padding=2, width="100%",
            halign="center")

        self.path = widgets.TextInput(self, width="100%",
            classes=('-file-open-path',))

        self.listing = widgets.Selection(self, scrollable=True,
            width="100%", is_exclusive=True, size=20,
            classes=('-file-open-dialog',))

        self.openPath(os.path.abspath(path))

        f = widgets.Frame(self, width=296, is_transparent=True)
        ok = widgets.TextButton(f, text='Ok', border="black",
            classes=('-file-open-dialog-ok', ))
        cancel = widgets.TextButton(f, text='Cancel', border="black",
            classes=('-file-open-dialog-cancel', ))
        f.layout = layouts.Horizontal(f, padding=10, halign='right')

        self.selected_file = None
        self.selected_widget = None

    def addOption(self, label):
        FileOption(self.listing.contents, text=label)

    def openPath(self, path):
        self.current_path = path
        self.listing.clearOptions()
        self.path.text = path
        self.path.cursor_position = -1
        if path != '/':
            self.addOption('..')
        for entry in os.listdir(path):
            # XXX real filtering please
            if entry.startswith('.'): continue
            if os.path.isdir(os.path.join(path, entry)):
                entry += '/'
            self.addOption(entry)

    def on_ok(self):
        if self.callback is not None:
            self.callback(self.selected_file)

    def on_cancel(self):
        if self.callback is not None:
            self.callback()

class FileOption(widgets.Option):
    name = 'file-option'

@event.default('file-option')
def on_click(widget, x, y, buttons, modifiers, click_count):
    # copy from regular Option on_click
    widget.is_active = not widget.is_active
    select = widget.getParent('selection')
    if select.scrollable: f = select.contents
    else: f = select
    if widget.is_active and select.is_exclusive:
        for child in f.children:
            if child is not widget:
                child.is_active = None
    widget.getGUI().dispatch_event(select, 'on_change', select.value)

    # now the custom file dialog behaviour
    dialog = widget.getParent('file-dialog')
    if widget.text == '..':
        dialog.selected_widget = None
        path = dialog.current_path
        if path[-1] == '/': path = path[:-1]
        dialog.openPath(os.path.split(path)[0])
    elif widget.text[-1] == '/':
        dialog.selected_widget = None
        dialog.openPath(os.path.join(dialog.current_path, widget.text))
    else:
        file = os.path.join(dialog.current_path, widget.text)
        if click_count > 1:
            dialog.selected_file = file
            dialog.on_ok()
            dialog.delete()
        elif dialog.selected_file == file:
            dialog.selected_widget = None
        else:
            dialog.selected_file = file
            dialog.selected_widget = widget
    return event.EVENT_HANDLED

@event.default('.-file-open-dialog-ok')
def on_click(widget, *args):
    d = widget.getParent('file-dialog')
    d.on_ok()
    d.delete()
    return event.EVENT_HANDLED

@event.default('.-file-open-dialog-cancel')
def on_click(widget, *args):
    d = widget.getParent('file-dialog')
    d.on_cancel()
    d.delete()
    return event.EVENT_HANDLED

@event.default('.-file-open-path')
def on_change(widget, value):
    value = os.path.expanduser(os.path.expandvars(value))
    if os.path.isdir(value):
        widget.parent.openPath(value)
    return event.EVENT_HANDLED


