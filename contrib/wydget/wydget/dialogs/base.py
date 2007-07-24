
from wydget import widgets, event

class Dialog(widgets.Frame):
    def __init__(self, parent, x=0, y=0, z=0, width=None, height=None,
            classes=(), border='black', bgcolor='white', padding=2, **kw):
        if 'dialog' not in classes:
            classes = ('dialog', ) + classes
        super(Dialog, self).__init__(parent, x, y, z, width, height,
            border=border, classes=classes, bgcolor=bgcolor, **kw)

    def run(self):
        '''Invoke to make this dialog become modal.
        '''
        self.getGUI().setModal(self)

    def close(self):
        '''Invoke to make this dialog stop being modal and clean itself up.
        '''
        self.getGUI().setModal(None)
        self.delete()


@event.default('.dialog > .title')
def on_drag(widget, x, y, dx, dy, buttons, modifiers):
    dialog = widget.parent
    dialog.x += dx; dialog.y += dy
    return event.EVENT_HANDLED
