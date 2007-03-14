#!/usr/bin/env python

'''Key constants for pyglet.window.

Usage::

    from pyglet.window import Window
    from pyglet.window import key

    window = Window()

    @event(window)
    def on_key_press(symbol, modifiers):
        # Symbolic names:
        if symbol == key.RETURN:

        # Alphabet keys:
        elif symbol == key.Z:

        # Number keys:
        elif symbol == key._1:

        # Number keypad keys:
        elif symbol == key.NUM_1:

        # Modifiers:
        if modifiers & key.key.MOD_CTRL:

'''

__docformat__ = 'restructuredtext'
__version__ = '$Id$'

# Modifier mask constants
MOD_SHIFT       = 1 << 0
MOD_CTRL        = 1 << 1
MOD_ALT         = 1 << 2
MOD_CAPSLOCK    = 1 << 3
MOD_NUMLOCK     = 1 << 4
MOD_WINDOWS     = 1 << 5
MOD_COMMAND     = 1 << 6
MOD_OPTION      = 1 << 7

# Key symbol constants

# ASCII commands
BACKSPACE     = 0xff08
TAB           = 0xff09
LINEFEED      = 0xff0a
CLEAR         = 0xff0b
RETURN        = 0xff0d
ENTER         = 0xff0d      # synonym
PAUSE         = 0xff13
SCROLLLOCK    = 0xff14
SYSREQ        = 0xff15
ESCAPE        = 0xff1b
SPACE         = 0xff20

# Cursor control and motion
HOME          = 0xff50
LEFT          = 0xff51
UP            = 0xff52
RIGHT         = 0xff53
DOWN          = 0xff54
PAGEUP        = 0xff55
PAGEDOWN      = 0xff56
END           = 0xff57
BEGIN         = 0xff58

# Misc functions
DELETE        = 0xffff
SELECT        = 0xff60
PRINT         = 0xff61
EXECUTE       = 0xff62
INSERT        = 0xff63
UNDO          = 0xff65
REDO          = 0xff66
MENU          = 0xff67
FIND          = 0xff68
CANCEL        = 0xff69
HELP          = 0xff6a
BREAK         = 0xff6b
MODESWITCH    = 0xff7e
SCRIPTSWITCH  = 0xff7e

# Number pad
NUMLOCK       = 0xff7f
NUM_SPACE     = 0xff80
NUM_TAB       = 0xff89
NUM_ENTER     = 0xff8d
NUM_F1        = 0xff91
NUM_F2        = 0xff92
NUM_F3        = 0xff93
NUM_F4        = 0xff94
NUM_HOME      = 0xff95
NUM_LEFT      = 0xff96
NUM_UP        = 0xff97
NUM_RIGHT     = 0xff98
NUM_DOWN      = 0xff99
NUM_PRIOR     = 0xff9a
NUM_PAGE_UP   = 0xff9a
NUM_NEXT      = 0xff9b
NUM_PAGE_DOWN = 0xff9b
NUM_END       = 0xff9c
NUM_BEGIN     = 0xff9d
NUM_INSERT    = 0xff9e
NUM_DELETE    = 0xff9f
NUM_EQUAL     = 0xffbd
NUM_MULTIPLY  = 0xffaa
NUM_ADD       = 0xffab
NUM_SEPARATOR = 0xffac
NUM_SUBTRACT  = 0xffad
NUM_DECIMAL   = 0xffae
NUM_DIVIDE    = 0xffaf

NUM_0         = 0xffb0
NUM_1         = 0xffb1
NUM_2         = 0xffb2
NUM_3         = 0xffb3
NUM_4         = 0xffb4
NUM_5         = 0xffb5
NUM_6         = 0xffb6
NUM_7         = 0xffb7
NUM_8         = 0xffb8
NUM_9         = 0xffb9

# Function keys
F1            = 0xffbe
F2            = 0xffbf
F3            = 0xffc0
F4            = 0xffc1
F5            = 0xffc2
F6            = 0xffc3
F7            = 0xffc4
F8            = 0xffc5
F9            = 0xffc6
F10           = 0xffc7
F11           = 0xffc8
F12           = 0xffc9
F13           = 0xffca
F14           = 0xffcb
F15           = 0xffcc
F16           = 0xffcd

# Modifiers
LSHIFT        = 0xffe1
RSHIFT        = 0xffe2
LCTRL         = 0xffe3
RCTRL         = 0xffe4
CAPSLOCK      = 0xffe5
LMETA         = 0xffe7
RMETA         = 0xffe8
LALT          = 0xffe9
RALT          = 0xffea
LWINDOWS      = 0xffeb
RWINDOWS      = 0xffec
LCOMMAND      = 0xffed
RCOMMAND      = 0xffee
LOPTION       = 0xffd0
ROPTION       = 0xffd1

# Latin-1
SPACE         = 0x020
EXCLAMATION   = 0x021
DOUBLEQUOTE   = 0x022
HASH          = 0x023
POUND         = 0x023  # synonym
DOLLAR        = 0x024
PERCENT       = 0x025
AMPERSAND     = 0x026
APOSTROPHE    = 0x027
PARENLEFT     = 0x028
PARENRIGHT    = 0x029
ASTERISK      = 0x02a
PLUS          = 0x02b
COMMA         = 0x02c
MINUS         = 0x02d
PERIOD        = 0x02e
SLASH         = 0x02f
_0            = 0x030
_1            = 0x031
_2            = 0x032
_3            = 0x033
_4            = 0x034
_5            = 0x035
_6            = 0x036
_7            = 0x037
_8            = 0x038
_9            = 0x039
COLON         = 0x03a
SEMICOLON     = 0x03b
LESS          = 0x03c
EQUAL         = 0x03d
GREATER       = 0x03e
QUESTION      = 0x03f
AT            = 0x040
BRACKETLEFT   = 0x05b
BACKSLASH     = 0x05c
BRACKETRIGHT  = 0x05d
ASCIICIRCUM   = 0x05e
UNDERSCORE    = 0x05f
GRAVE         = 0x060
QUOTELEFT     = 0x060
A             = 0x061
B             = 0x062
C             = 0x063
D             = 0x064
E             = 0x065
F             = 0x066
G             = 0x067
H             = 0x068
I             = 0x069
J             = 0x06a
K             = 0x06b
L             = 0x06c
M             = 0x06d
N             = 0x06e
O             = 0x06f
P             = 0x070
Q             = 0x071
R             = 0x072
S             = 0x073
T             = 0x074
U             = 0x075
V             = 0x076
W             = 0x077
X             = 0x078
Y             = 0x079
Z             = 0x07a
BRACELEFT     = 0x07b
BAR           = 0x07c
BRACERIGHT    = 0x07d
ASCIITILDE    = 0x07e

# The rest of Latin-1, from X11/keysymdef.h... what to keep?
NOBREAKSPACE = 0x0a0
EXCLAMDOWN = 0x0a1
CENT = 0x0a2
STERLING = 0x0a3
CURRENCY = 0x0a4
YEN = 0x0a5
BROKENBAR = 0x0a6
SECTION = 0x0a7
DIAERESIS = 0x0a8
COPYRIGHT = 0x0a9
ORDFEMININE = 0x0aa
GUILLEMOTLEFT = 0x0ab
NOTSIGN = 0x0ac
HYPHEN = 0x0ad
REGISTERED = 0x0ae
MACRON = 0x0af
DEGREE = 0x0b0
PLUSMINUS = 0x0b1
TWOSUPERIOR = 0x0b2
THREESUPERIOR = 0x0b3
ACUTE = 0x0b4
MU = 0x0b5
PARAGRAPH = 0x0b6
PERIODCENTERED = 0x0b7
CEDILLA = 0x0b8
ONESUPERIOR = 0x0b9
MASCULINE = 0x0ba
GUILLEMOTRIGHT = 0x0bb
ONEQUARTER = 0x0bc
ONEHALF = 0x0bd
THREEQUARTERS = 0x0be
QUESTIONDOWN = 0x0bf
AGRAVE = 0x0c0
AACUTE = 0x0c1
ACIRCUMFLEX = 0x0c2
ATILDE = 0x0c3
ADIAERESIS = 0x0c4
ARING = 0x0c5
AE = 0x0c6
CCEDILLA = 0x0c7
EGRAVE = 0x0c8
EACUTE = 0x0c9
ECIRCUMFLEX = 0x0ca
EDIAERESIS = 0x0cb
IGRAVE = 0x0cc
IACUTE = 0x0cd
ICIRCUMFLEX = 0x0ce
IDIAERESIS = 0x0cf
ETH = 0x0d0
ETH = 0x0d0
NTILDE = 0x0d1
OGRAVE = 0x0d2
OACUTE = 0x0d3
OCIRCUMFLEX = 0x0d4
OTILDE = 0x0d5
ODIAERESIS = 0x0d6
MULTIPLY = 0x0d7
OOBLIQUE = 0x0d8
OSLASH = OOBLIQUE
UGRAVE = 0x0d9
UACUTE = 0x0da
UCIRCUMFLEX = 0x0db
UDIAERESIS = 0x0dc
YACUTE = 0x0dd
THORN = 0x0de
THORN = 0x0de
SSHARP = 0x0df
AGRAVE = 0x0e0
AACUTE = 0x0e1
ACIRCUMFLEX = 0x0e2
ATILDE = 0x0e3
ADIAERESIS = 0x0e4
ARING = 0x0e5
AE = 0x0e6
CCEDILLA = 0x0e7
EGRAVE = 0x0e8
EACUTE = 0x0e9
ECIRCUMFLEX = 0x0ea
EDIAERESIS = 0x0eb
IGRAVE = 0x0ec
IACUTE = 0x0ed
ICIRCUMFLEX = 0x0ee
IDIAERESIS = 0x0ef
ETH = 0x0f0
NTILDE = 0x0f1
OGRAVE = 0x0f2
OACUTE = 0x0f3
OCIRCUMFLEX = 0x0f4
OTILDE = 0x0f5
ODIAERESIS = 0x0f6
DIVISION = 0x0f7
OSLASH = 0x0f8
OOBLIQUE = OSLASH
UGRAVE = 0x0f9
UACUTE = 0x0fa
UCIRCUMFLEX = 0x0fb
UDIAERESIS = 0x0fc
YACUTE = 0x0fd
THORN = 0x0fe
YDIAERESIS = 0x0ff

_key_names = {}
for name, value in locals().items():
    if name[:2] != '__' and name.upper() == name:
        _key_names[value] = name
