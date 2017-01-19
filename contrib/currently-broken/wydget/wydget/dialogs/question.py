from wydget import event
from wydget import widgets
from wydget import layouts
from wydget.dialogs import base

class Question(base.Dialog):
    id = '-question-dialog'
    name = 'question-dialog'
    classes = ('dialog', )

    def __init__(self, parent, text, callback=None, cancel=True,
            font_size=None, padding=10, **kw):
        super(Question, self).__init__(parent, padding=padding, **kw)
        self.callback = callback

        self.layout = layouts.Vertical(self, padding=10)

        widgets.Label(self, text, font_size=font_size)

        buttons = widgets.Frame(self, width='100%')
        buttons.layout = layouts.Horizontal(buttons, padding=10,
            halign='center')
        self.ok = widgets.TextButton(buttons, 'Ok', border='black',
            padding=2, classes=('-question-dialog-ok', ),
            font_size=font_size)
        if cancel:
            widgets.TextButton(buttons, 'Cancel', border='black',
                classes=('-question-dialog-cancel', ), padding=2,
                font_size=font_size)

    def run(self):
        super(Question, self).run()
        self.ok.gainFocus()

    def on_ok(self):
        if self.callback is not None:
            self.callback(True)

    def on_cancel(self):
        if self.callback is not None:
            self.callback(False)

def Message(*args, **kw):
    kw['cancel'] = False
    return Question(*args, **kw)

@event.default('.-question-dialog-ok')
def on_click(widget, *args):
    dialog = widget.getParent('question-dialog')
    dialog.on_ok()
    dialog.delete()
    return event.EVENT_HANDLED

@event.default('.-question-dialog-cancel')
def on_click(widget, *args):
    dialog = widget.getParent('question-dialog')
    dialog.on_cancel()
    dialog.delete()
    return event.EVENT_HANDLED

