import pyglet
import pyglet.text.layout


def test_incrementallayout_get_position_on_line_before_start_of_text():
    single_line_text = "This is a single line of text."
    document = pyglet.text.document.UnformattedDocument(single_line_text)
    font = document.get_font()
    layout = pyglet.text.layout.IncrementalTextLayout(document,
                                                                  height = font.ascent - font.descent,
                                                                  width = 200,
                                                                  multiline=False)
    layout.x = 100
    layout.y = 100

    assert layout.get_position_on_line(0, 100) == 0
    assert layout.get_position_on_line(0, 90) == 0
    assert layout.get_position_on_line(0, 80) == 0
    assert layout.get_position_on_line(0, 70) == 0
    assert layout.get_position_on_line(0, 60) == 0
    assert layout.get_position_on_line(0, 50) == 0
