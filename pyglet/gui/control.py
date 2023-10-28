from typing import Callable, Union, Tuple, Dict, TYPE_CHECKING, TypeVar, Optional

if TYPE_CHECKING:
    from pyglet.shapes import ShapeBase
    from pyglet.window import Window
    from pyglet.text import Label
    from pyglet.sprite import Sprite
    from pyglet.gui.widgets import WidgetBase

    Repositionable = Union[ShapeBase, Label, Sprite, WidgetBase]  # just for typing
else:
    Repositionable = TypeVar("Repositionable")  # for type checking

Num = Union[int, float]

PotitionTuple = Union[Tuple[Num, Num], Tuple[Num, Num, Num]]

CallBackFunc = Callable[[Repositionable, int, int, Window], None]
CalculateFunc = Callable[[Repositionable, int, int, Window], PotitionTuple]

CallBack = Union[CallBackFunc, CalculateFunc]
IndexType = Union[int, str]

class RePositionFrame:
    """ A Frame Like Object that allows for repositioning of widgets
    you can give A function and A widget/shape to let it reposition itself
    when the function is called
    
    >>> import pyglet
    >>> window = pyglet.window.Window(resizable=True)
    >>> reposition_frame = pyglet.gui.frame.RePositionFrame(window)
    >>> label = pyglet.text.Label("Hello World", x=0, y=0)
    >>> b_label = pyglet.text.Label("Hello World with call back", x=0, y=0)
    >>> def callback(obj, width, height, window):
    >>>    obj.x = width/3
    >>>    obj.y = height/3
    >>>    obj.text = f"Hello World with call back, width: {width}, height: {height}"
    >>> reposition_frame.add_calculate_func(label, lambda obj, width, height, window: (width/2, height/2, 0))
    >>> reposition_frame.add_callback_func(b_label, callback)
    >>> @window.event
    >>> def on_draw():
    >>>     window.clear()
    >>>     label.draw()
    >>>     b_label.draw()
    >>> pyglet.app.run()
    
    """

    def __init__(self, window):
        window.push_handlers(self)
        self.window = window
        self.callback_dict: Dict[IndexType, Tuple[Repositionable, CallBackFunc]] = {}
        self.calculate_dict: Dict[IndexType, Tuple[Repositionable, CalculateFunc]] = {}

    def add_callback_func(self, obj: Repositionable, func: CallBackFunc, index: Optional[IndexType] = None) -> IndexType:
        """ Add A callback function to the frame
        
        :param obj: The object that will be repositioned
        :param func: The function that will be called
        :param index: The index of the object
        """
        if index is None:
            index = hash(obj)
        self.callback_dict[index] = (obj, func)
        return index

    def add_calculate_func(self, obj: Repositionable, func: CalculateFunc, index: Optional[IndexType] = None) -> IndexType:
        """ Add A calculate function to the frame
        
        :param obj: The object that will be repositioned
        :param func: The function that will be called
        :param index: The index of the object
        """
        if index is None:
            index = hash(obj)
        self.calculate_dict[index] = (obj, func)
        return index

    def remove_callback_func(self, index: IndexType):
        if index in self.callback_dict:
            self.callback_dict.pop(index)

    def remove_calculate_func(self, index: IndexType):
        if index in self.calculate_dict:
            self.calculate_dict.pop(index)

    def on_resize(self, width: int, height: int):
        """ Call all the functions when the window is resized """
        for _, (obj, func) in self.callback_dict.items():
            func(obj, width, height, self.window)

        for _, (obj, func) in self.calculate_dict.items():
            obj.position = func(obj, width, height, self.window)


class GridFrame(RePositionFrame):
    """ A TKinker grid like frame that allows for repositioning of widgets
    and also allow you to auto place the widgets in a grid like fashion
    """
    
    # WIP
