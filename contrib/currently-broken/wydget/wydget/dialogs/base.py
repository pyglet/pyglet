
from wydget import widgets, event

class Dialog(widgets.Frame):
    def __init__(self, parent, x=0, y=0, z=0, width=None, height=None,
            classes=(), border='black', bgcolor='white', padding=2, **kw):
        if 'dialog' not in classes:
            classes = ('dialog', ) + classes
        super(Dialog, self).__init__(parent, x, y, z, width, height,
            padding=padding, border=border, classes=classes,
            bgcolor=bgcolor, **kw)

    def resize(self):
        if not super(Dialog, self).resize():
            return False
        # position dialog to center of parent
        new_x = self.parent.width//2 - self.width//2
        if new_x != self._x: self.x = new_x
        new_y = self.parent.height//2 - self.height//2
        if new_y != self._y: self.y = new_y
        return True

    def run(self):
        '''Invoke to position the dialog in the middle of the parent
        (presumably the window) and make the dialog become modal.
        '''
        self.setModal()


@event.default('.dialog > .title')
def on_drag(widget, x, y, dx, dy, buttons, modifiers):
    dialog = widget.parent
    dialog.x += dx; dialog.y += dy
    return event.EVENT_HANDLED
