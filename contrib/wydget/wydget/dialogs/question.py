from wydget import event
from wydget import widgets
from wydget.dialogs import base

class QuestionDialog(base.Dialog):
    id = '-question-dialog'
    name = 'question-dialog'
    classes = ('dialog', )

    def __init__(self, parent, text, callback=None, cancel=True,
            font_size=None, **kw):
        super(QuestionDialog, self).__init__(parent, **kw)
        self.callback = callback

        label = widgets.Label(self, text, font_size=font_size)
        ok = widgets.TextButton(self, 'Ok', border='black', padding=2,
            classes=('-question-dialog-ok', ), font_size=font_size)
        ok.gainFocus()
        self.height = label.height + 10 + ok.height
        label.y = ok.height + 10
        if cancel:
            cancel = widgets.TextButton(self, 'Cancel', border='black',
                classes=('-question-dialog-cancel', ), padding=2,
                font_size=font_size)
            self.width = max(label.width, ok.width + 10 + cancel.width)
            cancel.x = ok.width + 10
        else:
            self.width = max(label.width, ok.width + 10)

        self.x = parent.width/2 - self.width/2
        self.y = parent.height/2 - self.height/2

        self.layout.layout()

    def on_ok(self):
        if self.callback is not None:
            self.callback(True)

    def on_cancel(self):
        if self.callback is not None:
            self.callback(False)

@event.default('.-question-dialog-ok')
def on_click(widget, *args):
    widget.parent.on_ok()
    widget.parent.close()
    return event.EVENT_HANDLED

@event.default('.-question-dialog-cancel')
def on_click(widget, *args):
    widget.parent.on_cancel()
    widget.parent.close()
    return event.EVENT_HANDLED

