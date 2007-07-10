import os, sys

from wydget import event, widgets, layouts
from wydget.dialogs import base

if sys.platform == 'darwin':
    default_dir = os.path.expanduser('~/Desktop')
elif sys.platform in ('win32', 'cygwin'):
    default_dir = 'c:/'
else:
    default_dir = os.path.expanduser('~/Desktop')

class FileOpenDialog(base.Dialog):
    id = '-file-dialog'
    name = 'file-dialog'
    classes = ('dialog', )

    def __init__(self, parent, path=default_dir, callback=None, **kw):
        kw['border'] = 'black'
        kw['bgcolor'] = 'white'
        kw['padding'] = 2
        kw['width'] = 300
        super(FileOpenDialog, self).__init__(parent, **kw)
        self.callback = callback

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
        layouts.Horizontal(f, padding=10, halign='right').layout()

        layouts.Vertical(self, padding=2).layout()

        self.x = parent.width/2 - self.width/2
        self.y = parent.height/2 - self.height/2

        self.selected_file = None
        self.selected_widget = None

    def openPath(self, path):
        self.listing.clearOptions()
        self.path.text = path
        self.path.cursor_position = -1
        if path != '/':
            self.listing.addOption('..')
        for entry in os.listdir(path):
            # XXX real filtering please
            if entry.startswith('.'): continue
            if os.path.isdir(os.path.join(path, entry)):
                entry += '/'
            self.listing.addOption(entry)

    def on_ok(self):
        if self.callback is not None:
            self.callback(self.selected_file)

    def on_cancel(self):
        if self.callback is not None:
            self.callback()


@event.default('.-file-open-dialog option')
def on_click(widget, x, y, buttons, modifiers, click_count):
    # XXX ugh
    sel = widget.parent.parent.parent
    if widget.text == '..':
        sel.selected_widget = None
        sel.openPath(os.path.split(sel.path.text)[0])
    elif widget.text[-1] == '/':
        sel.selected_widget = None
        sel.openPath(os.path.join(sel.path.text, widget.text))
    else:
        file = os.path.join(sel.path.text, widget.text)
        if click_count > 1:
            sel.selected_file = file
            sel.on_ok()
            sel.close()
        elif sel.selected_file == file:
            sel.selected_widget = None
        else:
            sel.selected_file = file
            sel.selected_widget = widget
    return event.EVENT_HANDLED

@event.default('.-file-open-dialog-ok')
def on_click(widget, *args):
    widget.parent.parent.on_ok()
    widget.parent.parent.close()
    return event.EVENT_HANDLED

@event.default('.-file-open-dialog-cancel')
def on_click(widget, *args):
    widget.parent.parent.on_cancel()
    widget.parent.parent.close()
    return event.EVENT_HANDLED

@event.default('.-file-open-path')
def on_change(widget, value):
    if os.path.isdir(value):
        widget.parent.openPath(value)
    return event.EVENT_HANDLED


