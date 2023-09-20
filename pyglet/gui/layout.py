import pyglet
from pyglet.gui.widgets import WidgetBase

class LayoutCell:
    """Class representing a single cell in a layout.

    It contains all information about where and how cell 
    and its content should be drawn on screen.
    """
    def __init__(self, style={}, batch=None, group=None):
        self._content = None

        self._batch = batch
        self._group = group
        self._background = None
        self._rect = (0, 0, 1, 1)
        self._style = {}
        self._span = (1, 1)

        self.set_style(style)
        self._set_style_if_none('stretch-content', False)
        self._set_style_if_none('content-alignment', 'center')
        self._set_style_if_none('padding', 0)
    
    @property
    def x(self):
        return self._rect[0]

    @property
    def y(self):
        return self._rect[1]
    
    @property
    def position(self):
        return (self._rect[0], self._rect[1])

    @property
    def width(self):
        return self._rect[2]

    @property
    def height(self):
        return self._rect[3]
    
    @property
    def size(self):
        return (self._rect[2], self._rect[3])

    @property
    def content(self):
        return self._content
    
    @content.setter
    def content(self, value):
        self._content = value
        self.realign()

    def set_style(self, data, value=None):
        if not isinstance(data, str):
            for key, value in data.items():
                self.set_style(key, value)
            return
        
        key = data

        if key == 'background': 
            self._style[key] = value
            self._update_background()

        elif key == 'padding':
            if isinstance(value, int): value = (value, value, value, value)
            self._style['padding-top'] = value[0]
            self._style['padding-right'] = value[1]
            self._style['padding-bottom'] = value[2]
            self._style['padding-left'] = value[3]
            self._style[key] = value
        elif key.startswith('padding'):
            self._style[key] = value
            self._style['padding'] = (
                self.get_style('padding-top') or 0,
                self.get_style('padding-right') or 0,
                self.get_style('padding-bottom') or 0,
                self.get_style('padding-left') or 0
            )

        elif key == 'stretch-content':
            if isinstance(value, bool): value = (value, value)
            self._style['stretch-content-x'] = value[0]
            self._style['stretch-content-y'] = value[1]
            self._style[key] = value
        elif key.startswith('stretch-content'):
            self._style[key] = value
            self._style['stretch_content'] = (
                self.get_style('stretch-content-x') or 0,
                self.get_style('stretch-content-y') or 0
            )

        elif key == 'content-alignment':
            if value == 'center': value = (value, value)
            self._style['content-alignment-x'] = value[0]
            self._style['content-alignment-y'] = value[1]
            self._style[key] = value
        elif key.startswith('content-alignment'):
            self._style[key] = value
            self._style['content_alignment'] = (
                self.get_style('content-alignment-x') or 0,
                self.get_style('content-alignment-y') or 0
            )

        else:
            self._style[key] = value

        self.realign()

    def _set_style_if_none(self, key, value):
        if self.get_style(key) is None: self.set_style(key, value)

    def get_style(self, key):
        return self._style[key] if key in self._style else None
    
    def _update_background(self):
        back_style = self.get_style("background")
        if back_style is None:
            if self._background is not None:
                del self._background
                self._background = None
            return
        
        if isinstance(back_style, tuple):
            if not isinstance(self._background, pyglet.shapes.Rectangle):
                if self._background is not None:
                    del self._background
                self._background = pyglet.shapes.Rectangle(0, 0, 0, 0, back_style, self._batch, self._group)
            self._background.color = back_style
        
        elif isinstance(back_style, pyglet.sprite.Sprite):
            if self._background != back_style and self._background is not None:
                del self._background
            self._background = back_style
    
    def realign(self, new_rect=None):
        if new_rect is not None:
            self._rect = new_rect
            if self._background is not None:
                self._background.width = self.width
                self._background.height = self.height
                self._background.x = self.x
                self._background.y = self.y

        if self._content == None: return

        padding = (
            self.get_style('padding-top') or 0,
            self.get_style('padding-right') or 0,
            self.get_style('padding-bottom') or 0,
            self.get_style('padding-left') or 0
        )
        stretch_content = (
            self.get_style('stretch-content-x') or False,
            self.get_style('stretch-content-y') or False
        )
        content_alignment = (
            self.get_style('content-alignment-x') or 'center',
            self.get_style('content-alignment-y') or 'center'
        )

        if stretch_content[0]:
            self._content.width = self.width - padding[1] - padding[3]
        if stretch_content[1]:
            self._content.height = self.height - padding[0] - padding[2]
        
        content_width = self._content.width or 0
        content_height = self._content.height or 0

        if content_alignment[0] == 'left':
            content_x = self.x
        elif content_alignment[0] == 'center':
            content_x = self.x + self.width / 2 - content_width / 2
        elif content_alignment[0] == 'right':
            content_x = self.x + self.width - content_width
        else:
            raise ValueError('content-alignment-x variable is not set properly: ' + content_alignment[0])
        
        if content_alignment[1] == 'bottom':
            content_y = self.y
        elif content_alignment[1] == 'center':
            content_y = self.y + self.height / 2 - content_height / 2
        elif content_alignment[1] == 'top':
            content_y = self.y + self.height - content_height
        else:
            raise ValueError('content-alignment-y variable is not set properly: ' + content_alignment[1])

        print(self.content, new_rect, stretch_content, content_alignment, (content_x, content_y))
        
        try:
            self._content.position = (content_x, content_y)
        except Exception as e:
            self._content.position = (content_x, content_y, 0)


class _LayoutSpanFiller:
    """Placeholder for empty cells in a span cell."""
    def __init__(self, cell):
        self.cell = cell


class _LayoutCellSequenceData:
    """Class representing a sequence of layout cells: one specific row or column.
    Can parse css-like side value.

    :Attributes:
        margin_after : int
            The margin after this cell sequence. Specified in pixels.
        size_specified : bool
            Whether the size of this cell sequence has been specified.
        size_type : str
            The type of size specified for this cell sequence. Can be 'percent' or 'pixels'.
        size_data : int
            The reference size data for this cell sequence.
        calculated_size : int
            The calculated size of this cell sequence. Controlled by layout based on specified size data.
    """
    def __init__(self, margin=0):
        self.margin_after = margin
        self.size_specified = False
        self.size_type = None
        self.size_data = 0
        self.calculated_size = 0

    def parse_size(self, value):
        if value is None or len(value) == 0:
            self.set_size(None)
        elif isinstance(value, str):
            if value.endswith('%'):
                self.set_size('percent', float(value[0:-1].strip()))
            elif value.endswith('px'):
                self.set_size('pixels', int(value[0:-2].strip()))
            else:
                self.set_size('pixels', int(value))
        elif isinstance(value, int):
            self.set_size('pixels', value)
        else:
            raise Exception("Cannot parse size value " + value)

    def set_size(self, type, value=0):
        if value == 0:
            type = None
        assert type in (None, 'pixels', 'percent'), "Unknown size type: " + type
        self.size_specified = type is not None
        self.size_type = type
        self.size_data = value


class _LayoutGridContent:
    """Content-like class containing all rows, columns and cells,
    so it behaves like any other widget and LayoutCell.realign method is completely compatible to it
    and do not need any rewritings or additions.
    """
    def __init__(self, rows, columns, style, batch, group):
        self._style = style
        self._row_count = self._column_count = 0
        self._cells = [[]]
        self._columns = [_LayoutCellSequenceData()] * 0
        self._rows = [_LayoutCellSequenceData()] * 0

        self._group = group
        self._batch = batch

        self.x = self.y = self.width = self.height = 0

        self.set_layout_dimensions(rows, columns)

    def _new_cell(self):
        return LayoutCell({
                'background': self._style['cell-background'],
                'padding': self._style['cell-padding'],
                'content-alignment': self._style['cell-content-alignment'],
                'stretch-content': self._style['cell-stretch-content']
            }, self._batch, self._group)
    
    @property
    def all_cells(self):
        return [cell for sublist in self._cells for cell in sublist if not isinstance(cell, _LayoutSpanFiller)]

    def set_layout_dimensions(self, new_rows, new_cols):
        assert new_rows > 0, "There should be positive number of rows"
        assert new_cols > 0, "There should be positive number of columns"
        old_rows, old_cols = self._row_count, self._column_count

        new_arr = [[self._new_cell() for _ in range(new_cols)] for _ in range(new_rows)]

        for i in range(min(old_rows, new_rows)):
            for j in range(min(old_cols, new_cols)):
                cell = new_arr[i][j] = self._cells[i][j]
                if isinstance(cell, LayoutCell):
                    cell._span = (
                        min(cell._span[0], new_rows - i),
                        min(cell._span[1], new_cols - j)
                    )

        self._cells = new_arr

        if old_rows != new_rows:
            new_arr = [None] * new_rows
            for i in range(new_rows):
                if i < old_rows:
                    new_arr[i] = self._rows[i]
                else:
                    new_arr[i] = _LayoutCellSequenceData(self._style['cell-margin'])
                    if 'row-size' in self._style:
                        new_arr[i].parse_size(self._style['row-size'])
            self._rows = new_arr

        if old_cols != new_cols:
            new_arr = [None] * new_cols
            for i in range(new_cols):
                if i < old_cols:
                    new_arr[i] = self._columns[i]
                else:
                    new_arr[i] = _LayoutCellSequenceData(self._style['cell-margin'])
                    if 'column-size' in self._style:
                        new_arr[i].parse_size(self._style['column-size'])
            self._columns = new_arr

        self._column_count = new_cols
        self._row_count = new_rows

        self.realign()

    def set_cell_span(self, row, col, rowspan=None, colspan=None):
        if rowspan is None and colspan is None: return
        assert rowspan is None or (rowspan >= 1 and row + rowspan <= self._row_count), f"Invalid rowspan: {rowspan}"
        assert colspan is None or (colspan >= 1 and col + colspan <= self._column_count), f"Invalid colspan: {colspan}"

        cell = self._cells[row][col]

        if rowspan is None: rowspan = cell._span[0]
        if colspan is None: colspan = cell._span[1]
        
        for i in range(row, row + max(rowspan, cell._span[0])):
            for j in range(col, col + max(colspan, cell._span[1])):
                if i == row and j == col:
                    pass
                elif i < row + rowspan and j < col + colspan:
                    self._cells[i][j] = _LayoutSpanFiller(cell)
                else:
                    self._cells[i][j] = self._new_cell()

        cell._span = (rowspan, colspan)
        cell.realign(self._calc_cell_rect(row, col))

    def _calc_cell_rect(self, row, col):
        cell = self._cells[row][col]
        width = height = x = y = 0

        for i in range(col):
            x += self._columns[i].calculated_size + self._columns[i].margin_after
        for i in range(row):
            y += self._rows[i].calculated_size + self._rows[i].margin_after
        for i in range(cell._span[1]):
            if i > 0: width += self._columns[col + i - 1].margin_after
            width += self._columns[col + i].calculated_size
        for i in range(cell._span[0]):
            if i > 0: height += self._rows[row + i - 1].margin_after
            height += self._rows[row + i].calculated_size
        
        return (
            self.x + x, 
            self.y + self.height - y - height, 
            width, 
            height
        )

    def _update_position(self):
        for i in range(self._row_count):
            for j in range(self._column_count):
                cell = self._cells[i][j]
                if isinstance(cell, LayoutCell):
                    print(i, j, self._calc_cell_rect(i, j))
                    cell.realign(self._calc_cell_rect(i, j))

    def _update_sequence_sizes(self, sequence, area_size):
        fixed_size_items = []
        for item in sequence:
            if not item.size_specified: continue

            if item.size_type == 'pixels': 
                item.calculated_size = item.size_data
            elif item.size_type == 'percent':
                item.calculated_size = area_size * item.size_data / 100

            fixed_size_items.append(item.calculated_size)
        
        fixed_items_count = len(sequence) - len(fixed_size_items)
        
        if fixed_items_count > 0:
            fixed_size = (
                sum(fixed_size_items) + 
                sum([ sequence[i].margin_after for i in range(len(sequence) - 1) ])
            )
            left_size = max(area_size - fixed_size, 0)
            item_size = (left_size // fixed_items_count)
            for item in sequence:
                if not item.size_specified: item.calculated_size = item_size

    def on_style_update(self, key, value):
        if key == 'cell-background': 
            for cell in self.all_cells:
                cell.set_style('background', value)

        elif key.startswith('cell-padding') or key.startswith('cell-stretch-content') or key.startswith('cell-content-alignment'): 
            for cell in self.all_cells:
                cell.set_style(key[5:], value)
            self.realign()

        elif key == 'cell-margin':
            if not isinstance(value, tuple) and not isinstance(value, list):
                 self._style['margin'] = value = (value, value)
            self._style['cell-margin-x'] = value[0]
            self._style['cell-margin-y'] = value[1]
            for row in self._rows: row.margin_after = value[1]
            for column in self._columns: column.margin_after = value[0]
            self.realign()

        elif key == 'cell-margin-y':
            for row in self._rows: row.margin_after = value
            self.realign()

        elif key == 'cell-margin-x':
            for column in self._columns: column.margin_after = value
            self.realign()

        elif key == 'row-size':
            for row in self._rows: row.parse_size(value)
            self.realign()

        elif key == 'column-size':
            for column in self._columns: column.parse_size(value)
            self.realign()

    def realign(self):
        self._update_sequence_sizes(self._columns, self.width)
        self._update_sequence_sizes(self._rows, self.height)
        self._update_position()

    @property
    def position(self, value):
        return (self.x, self.y)

    @position.setter
    def position(self, value):
        self.x, self.y = value[0], value[1]
        self.realign()
        

class Layout(LayoutCell):
    """Class representing a layout container that contains multiple widgets.

    Layout contains information about the size and position of its cells
    and can be used to create complex UI layouts.
    Layout class automatically handles all resize and reposition events.

    Attention: coords system goes from bottom to top, but layout is working from top to bottom.

    :Supported style values:
        `padding` : (int, int, int, int)
            The padding around the content in the cell. Specified as (top, right, bottom, left).
            Also you can specify each one separately, for example 'padding-top'.
        `cell-margin` : int
            The default margin between cells in the layout. Specified in pixels.
        `background` : (int, int, int, int) or Sprite
            The background of the layout, in RGBA format or already uploaded sprite
            which will be realigned accordingly
        `cell-background` : (int, int, int, int) or Sprite
            The default cell background, in RGBA format.
        `row-size` : int or str
            Default row size of the layout. Can be specidied as int which will be counted as pixels.
            Also you can specify css-like value '50%' or '50px'.
            Each row with None row-size will be resized to fill all available space of layout.
        `column-size` : int or str
            Default column size of the layout. Can be specidied as int which will be counted as pixels.
            Also you can specify css-like value '50%' or '50px'.
            Each column with None row-size will be resized to fill all available space of layout.
        `content-alignment` : (str, str)
            The alignment of the content within the cell. Specified as (horizontal, vertical).
            Horizontal aligment value can be one of these: `left`, `center`, `right`.
            Vertical aligment value can be one of these: `top`, `center`, `bottom`.
            Also can be specified separately.
        `cell-stretch-content` : (bool, bool)
            Whether the cell should stretch its content in the layout. Specified as (horizontal, vertical).
    """
    def __init__(self, x, y, width, height, rows, columns, style={}, batch=None, group=None):
        """Create a layout.

        :Parameters:
            `x` : int
                X coordinate of the layout.
            `y` : int
                Y coordinate of the layout.
            `rows` : int
                The number of rows in the layout.
            `columns` : int
                The number of columns in the layout.
            `style` : dict
                Style that will be applied to layout and its content. Can be changed later.
            `batch` : `~pyglet.graphics.Batch`
                Optional batch to add the layout decorations (but not cells content).
            `group` : `~pyglet.graphics.Group`
                Optional parent group of the layout decorations.
        """
        super().__init__(style, batch, group)

        self._set_style_if_none('cell-margin', 1)
        self._set_style_if_none('cell-background', None)
        self._set_style_if_none('cell-stretch-content', False)
        self._set_style_if_none('cell-content-alignment', 'center')
        self._set_style_if_none('cell-padding', 0)
        self.set_style('stretch-content', True)

        self._cell_group = pyglet.graphics.Group(order=1, parent=group)
        self._content = _LayoutGridContent(rows, columns, self._style, 
                                          batch=self._batch, group=self._cell_group)
        
        self.realign((x, y, width, height))

    @property
    def columns(self):
        return self._content._column_count

    @columns.setter
    def columns(self, value):
        return self._content.set_layout_dimensions(self.rows, value)

    @property
    def rows(self):
        return self._content._row_count

    @rows.setter
    def rows(self, value):
        return self._content.set_layout_dimensions(value, self.columns)
    
    def cell(self, row, col) -> LayoutCell:
        self._assert_cell_index(row, col)
        cell = self._content._cells[row][col]
        return cell if not isinstance(cell, _LayoutSpanFiller) else None
    
    def _assert_cell_index(self, row, col):
        assert row >= 0 or row < self.rows, f"Invalid row index: {row}"
        assert col >= 0 or col < self.columns, f"Invalid column index: {col}"

    def set_style(self, data, value=None):
        super(Layout, self).set_style(data, value)
        if isinstance(data, str) and self.content:
            self.content.on_style_update(data, value)
    
    def set_column_size(self, index, value):
        self._content._columns[index].parse_size(value)
        self._content.realign()
    
    def set_row_size(self, index, value):
        self._content._rows[index].parse_size(value)
        self.realign()

    def set_column_margin(self, index, value):
        self._content._columns[index].margin_after = value
        self.realign()

    def set_row_margin(self, index, value):
        self._content._rows[index].margin_after = value
        self.realign()

    def set_cell_span(self, row, col, rowspan=None, colspan=None):
        self._assert_cell_index(row, col)
        self.content.set_cell_span(row, col, rowspan, colspan)
    
    def draw(self):
        if self._batch is not None:
            self._batch.draw()
        
        for row in range(self.rows):
            for col in range(self.columns):
                cell = self.cell(row, col)
                if isinstance(cell, LayoutCell) and cell.content is not None and cell.content._batch != self._batch:
                    cell.content.draw()

    @LayoutCell.x.setter
    def x(self, value):
        self.realign((value, self.y, self.width, self.height))

    @LayoutCell.y.setter
    def y(self, value):
        self.realign((self.x, value, self.width, self.height))
    
    @LayoutCell.position.setter
    def position(self, value):
        self.realign((value[0], value[1], self.width, self.height))

    @LayoutCell.width.setter
    def width(self, value):
        self.realign((self.x, self.y, value, self.height))

    @LayoutCell.height.setter
    def height(self, value):
        self.realign((self.x, self.y, self.width, value))
    
    @LayoutCell.size.setter
    def size(self, value):
        self.realign((self.x, self.y, value[0], value[1]))

    def realign(self, new_rect=None):
        super().realign(new_rect)
        
        if self.content is not None:
            self.content.realign()


class HBox(Layout):
    def __init__(self, x, y, width, height, style={}, batch=None, group=None):
        super().__init__(x, y, width, height, 1, 1, style, batch, group)

    def add(self, widget):
        if self.cell(0).content is not None:
            self.columns = self.columns + 1
        self.cell(self.columns - 1).content = widget
        self.realign()
    
    def cell(self, index, cl=0):
        return super().cell(0, index)


class VBox(Layout):
    def __init__(self, x, y, width, height, style={}, batch=None, group=None):
        super().__init__(x, y, width, height, 1, 1, style, batch, group)

    def add(self, widget):
        if self.cell(0).content is not None:
            self.rows = self.rows + 1
        self.cell(self.rows - 1).content = widget
        self.realign()
    
    def cell(self, index, rw=0):
        return super().cell(index, 0)