#!/usr/bin/env python

'''
'''

# Regex'd from /usr/include/X11/X.h

__docformat__ = 'restructuredtext'
__version__ = '$Id$'


ParentRelative = 1L
CopyFromParent = 0L
PointerWindow = 0L
InputFocus = 1L
PointerRoot = 1L
AnyPropertyType = 0L
AnyKey = 0L
AnyButton = 0L
AllTemporary = 0L
CurrentTime = 0L
NoSymbol = 0L

# EVENT DEFINITIONS 

# Input Event Masks. Used as event-mask window attribute and as arguments
# to Grab requests.  Not to be confused with event names.

NoEventMask = 0L
KeyPressMask = (1L<<0)
KeyReleaseMask = (1L<<1)
ButtonPressMask = (1L<<2)
ButtonReleaseMask = (1L<<3)
EnterWindowMask = (1L<<4)
LeaveWindowMask = (1L<<5)
PointerMotionMask = (1L<<6)
PointerMotionHintMask = (1L<<7)
Button1MotionMask = (1L<<8)
Button2MotionMask = (1L<<9)
Button3MotionMask = (1L<<10)
Button4MotionMask = (1L<<11)
Button5MotionMask = (1L<<12)
ButtonMotionMask = (1L<<13)
KeymapStateMask = (1L<<14)
ExposureMask = (1L<<15)
VisibilityChangeMask = (1L<<16)
StructureNotifyMask = (1L<<17)
ResizeRedirectMask = (1L<<18)
SubstructureNotifyMask = (1L<<19)
SubstructureRedirectMask = (1L<<20)
FocusChangeMask = (1L<<21)
PropertyChangeMask = (1L<<22)
ColormapChangeMask = (1L<<23)
OwnerGrabButtonMask = (1L<<24)

# Event names.  Used in "type" field in XEvent structures.  Not to be
# confused with event masks above.  They start from 2 because 0 and 1
# are reserved in the protocol for errors and replies.

KeyPress = 2
KeyRelease = 3
ButtonPress = 4
ButtonRelease = 5
MotionNotify = 6
EnterNotify = 7
LeaveNotify = 8
FocusIn = 9
FocusOut = 10
KeymapNotify = 11
Expose = 12
GraphicsExpose = 13
NoExpose = 14
VisibilityNotify = 15
CreateNotify = 16
DestroyNotify = 17
UnmapNotify = 18
MapNotify = 19
MapRequest = 20
ReparentNotify = 21
ConfigureNotify = 22
ConfigureRequest = 23
GravityNotify = 24
ResizeRequest = 25
CirculateNotify = 26
CirculateRequest = 27
PropertyNotify = 28
SelectionClear = 29
SelectionRequest = 30
SelectionNotify = 31
ColormapNotify = 32
ClientMessage = 33
MappingNotify = 34
LASTEvent = 35

# Key masks. Used as modifiers to GrabButton and GrabKey, results of
# QueryPointer, state in various key-, mouse-, and button-related events.

ShiftMask = (1<<0)
LockMask = (1<<1)
ControlMask = (1<<2)
Mod1Mask = (1<<3)
Mod2Mask = (1<<4)
Mod3Mask = (1<<5)
Mod4Mask = (1<<6)
Mod5Mask = (1<<7)

# modifier names.  Used to build a SetModifierMapping request or
# to read a GetModifierMapping request.  These correspond to the
# masks defined above.
ShiftMapIndex = 0
LockMapIndex = 1
ControlMapIndex = 2
Mod1MapIndex = 3
Mod2MapIndex = 4
Mod3MapIndex = 5
Mod4MapIndex = 6
Mod5MapIndex = 7

# button masks.  Used in same manner as Key masks above. Not to be confused
# with button names below. 

Button1Mask = (1<<8)
Button2Mask = (1<<9)
Button3Mask = (1<<10)
Button4Mask = (1<<11)
Button5Mask = (1<<12)

AnyModifier = (1<<15)


# button names. Used as arguments to GrabButton and as detail in ButtonPress
# and ButtonRelease events.  Not to be confused with button masks above.
# Note that 0 is already defined above as "AnyButton".  

Button1 = 1
Button2 = 2
Button3 = 3
Button4 = 4
Button5 = 5

# Notify modes 

NotifyNormal = 0
NotifyGrab = 1
NotifyUngrab = 2
NotifyWhileGrabbed = 3

NotifyHint = 1
               
# Notify detail 

NotifyAncestor = 0
NotifyVirtual = 1
NotifyInferior = 2
NotifyNonlinear = 3
NotifyNonlinearVirtual = 4
NotifyPointer = 5
NotifyPointerRoot = 6
NotifyDetailNone = 7

# Visibility notify 

VisibilityUnobscured = 0
VisibilityPartiallyObscured = 1
VisibilityFullyObscured = 2

# Circulation request 

PlaceOnTop = 0
PlaceOnBottom = 1

# protocol families 

FamilyInternet = 0
FamilyDECnet = 1
FamilyChaos = 2
FamilyInternet6 = 6

# authentication families not tied to a specific protocol 
FamilyServerInterpreted = 5

# Property notification 

PropertyNewValue = 0
PropertyDelete = 1

# Color Map notification 

ColormapUninstalled = 0
ColormapInstalled = 1

# GrabPointer, GrabButton, GrabKeyboard, GrabKey Modes 

GrabModeSync = 0
GrabModeAsync = 1

# GrabPointer, GrabKeyboard reply status 

GrabSuccess = 0
AlreadyGrabbed = 1
GrabInvalidTime = 2
GrabNotViewable = 3
GrabFrozen = 4

# AllowEvents modes 

AsyncPointer = 0
SyncPointer = 1
ReplayPointer = 2
AsyncKeyboard = 3
SyncKeyboard = 4
ReplayKeyboard = 5
AsyncBoth = 6
SyncBoth = 7

# Used in SetInputFocus, GetInputFocus 

RevertToNone = 0
RevertToPointerRoot = PointerRoot
RevertToParent = 2

#***************************************************************
# ERROR CODES 
#***************************************************************

Success = 0
BadRequest = 1
BadValue = 2
BadWindow = 3
BadPixmap = 4
BadAtom = 5
BadCursor = 6
BadFont = 7
BadMatch = 8
BadDrawable = 9
BadAccess = 10
BadAlloc = 11
BadColor = 12
BadGC = 13
BadIDChoice = 14
BadName = 15
BadLength = 16
BadImplementation = 17

FirstExtensionError = 128
LastExtensionError = 255

#***************************************************************
# WINDOW DEFINITIONS 
#***************************************************************

# Window classes used by CreateWindow 
# Note that CopyFromParent is already defined as 0 above 

InputOutput = 1
InputOnly = 2

# Window attributes for CreateWindow and ChangeWindowAttributes 

CWBackPixmap = (1L<<0)
CWBackPixel = (1L<<1)
CWBorderPixmap = (1L<<2)
CWBorderPixel = (1L<<3)
CWBitGravity = (1L<<4)
CWWinGravity = (1L<<5)
CWBackingStore = (1L<<6)
CWBackingPlanes = (1L<<7)
CWBackingPixel = (1L<<8)
CWOverrideRedirect = (1L<<9)
CWSaveUnder = (1L<<10)
CWEventMask = (1L<<11)
CWDontPropagate = (1L<<12)
CWColormap = (1L<<13)
CWCursor = (1L<<14)

# ConfigureWindow structure 

CWX = (1<<0)
CWY = (1<<1)
CWWidth = (1<<2)
CWHeight = (1<<3)
CWBorderWidth = (1<<4)
CWSibling = (1<<5)
CWStackMode = (1<<6)


# Bit Gravity 

ForgetGravity = 0
NorthWestGravity = 1
NorthGravity = 2
NorthEastGravity = 3
WestGravity = 4
CenterGravity = 5
EastGravity = 6
SouthWestGravity = 7
SouthGravity = 8
SouthEastGravity = 9
StaticGravity = 10

# Window gravity + bit gravity above 

UnmapGravity = 0

# Used in CreateWindow for backing-store hint 

NotUseful = 0
WhenMapped = 1
Always = 2

# Used in GetWindowAttributes reply 

IsUnmapped = 0
IsUnviewable = 1
IsViewable = 2

# Used in ChangeSaveSet 

SetModeInsert = 0
SetModeDelete = 1

# Used in ChangeCloseDownMode 

DestroyAll = 0
RetainPermanent = 1
RetainTemporary = 2

# Window stacking method (in configureWindow) 

Above = 0
Below = 1
TopIf = 2
BottomIf = 3
Opposite = 4

# Circulation direction 

RaiseLowest = 0
LowerHighest = 1

# Property modes 

PropModeReplace = 0
PropModePrepend = 1
PropModeAppend = 2

#***************************************************************
# GRAPHICS DEFINITIONS
#***************************************************************

# graphics functions, as in GC.alu 

GXclear = 0x0
GXand = 0x1
GXandReverse = 0x2
GXcopy = 0x3
GXandInverted = 0x4
GXnoop = 0x5
GXxor = 0x6
GXor = 0x7
GXnor = 0x8
GXequiv = 0x9
GXinvert = 0xa
GXorReverse = 0xb
GXcopyInverted = 0xc
GXorInverted = 0xd
GXnand = 0xe
GXset = 0xf

# LineStyle 

LineSolid = 0
LineOnOffDash = 1
LineDoubleDash = 2

# capStyle 

CapNotLast = 0
CapButt = 1
CapRound = 2
CapProjecting = 3

# joinStyle 

JoinMiter = 0
JoinRound = 1
JoinBevel = 2

# fillStyle 

FillSolid = 0
FillTiled = 1
FillStippled = 2
FillOpaqueStippled = 3

# fillRule 

EvenOddRule = 0
WindingRule = 1

# subwindow mode 

ClipByChildren = 0
IncludeInferiors = 1

# SetClipRectangles ordering 

Unsorted = 0
YSorted = 1
YXSorted = 2
YXBanded = 3

# CoordinateMode for drawing routines 

CoordModeOrigin = 0
CoordModePrevious = 1

# Polygon shapes 

Complex = 0
Nonconvex = 1
Convex = 2

# Arc modes for PolyFillArc 

ArcChord = 0
ArcPieSlice = 1

# GC components: masks used in CreateGC, CopyGC, ChangeGC, OR'ed into
# GC.stateChanges 

GCFunction = (1L<<0)
GCPlaneMask = (1L<<1)
GCForeground = (1L<<2)
GCBackground = (1L<<3)
GCLineWidth = (1L<<4)
GCLineStyle = (1L<<5)
GCCapStyle = (1L<<6)
GCJoinStyle = (1L<<7)
GCFillStyle = (1L<<8)
GCFillRule = (1L<<9)
GCTile = (1L<<10)
GCStipple = (1L<<11)
GCTileStipXOrigin = (1L<<12)
GCTileStipYOrigin = (1L<<13)
GCFont = (1L<<14)
GCSubwindowMode = (1L<<15)
GCGraphicsExposures = (1L<<16)
GCClipXOrigin = (1L<<17)
GCClipYOrigin = (1L<<18)
GCClipMask = (1L<<19)
GCDashOffset = (1L<<20)
GCDashList = (1L<<21)
GCArcMode = (1L<<22)

GCLastBit = 22
#***************************************************************
# FONTS 
#***************************************************************

# used in QueryFont -- draw direction 

FontLeftToRight = 0
FontRightToLeft = 1

FontChange = 255

#***************************************************************
#  IMAGING 
#***************************************************************

# ImageFormat -- PutImage, GetImage 

XYBitmap = 0
XYPixmap = 1
ZPixmap = 2

#***************************************************************
#  COLOR MAP STUFF 
#***************************************************************

# For CreateColormap 

AllocNone = 0
AllocAll = 1


# Flags used in StoreNamedColor, StoreColors 

DoRed = (1<<0)
DoGreen = (1<<1)
DoBlue = (1<<2)

#***************************************************************
# CURSOR STUFF
#***************************************************************

# QueryBestSize Class 

CursorShape = 0
TileShape = 1
StippleShape = 2

#*************************************************************** 
# KEYBOARD/POINTER STUFF
#***************************************************************

AutoRepeatModeOff = 0
AutoRepeatModeOn = 1
AutoRepeatModeDefault = 2

LedModeOff = 0
LedModeOn = 1

# masks for ChangeKeyboardControl 

KBKeyClickPercent = (1L<<0)
KBBellPercent = (1L<<1)
KBBellPitch = (1L<<2)
KBBellDuration = (1L<<3)
KBLed = (1L<<4)
KBLedMode = (1L<<5)
KBKey = (1L<<6)
KBAutoRepeatMode = (1L<<7)

MappingSuccess = 0
MappingBusy = 1
MappingFailed = 2

MappingModifier = 0
MappingKeyboard = 1
MappingPointer = 2

#***************************************************************
# SCREEN SAVER STUFF 
#***************************************************************

DontPreferBlanking = 0
PreferBlanking = 1
DefaultBlanking = 2

DisableScreenSaver = 0
DisableScreenInterval = 0

DontAllowExposures = 0
AllowExposures = 1
DefaultExposures = 2

# for ForceScreenSaver 

ScreenSaverReset = 0
ScreenSaverActive = 1

#***************************************************************
# HOSTS AND CONNECTIONS
#***************************************************************

# for ChangeHosts 

HostInsert = 0
HostDelete = 1

# for ChangeAccessControl 

EnableAccess = 1
DisableAccess = 0

# Display classes  used in opening the connection 
# Note that the statically allocated ones are even numbered and the
# dynamically changeable ones are odd numbered 

StaticGray = 0
GrayScale = 1
StaticColor = 2
PseudoColor = 3
TrueColor = 4
DirectColor = 5


# Byte order  used in imageByteOrder and bitmapBitOrder 

LSBFirst = 0
MSBFirst = 1


#***************************************************************
# Motif window manager hints
#***************************************************************

PROP_MWM_HINTS_ELEMENTS = 4 

MWM_HINTS_FUNCTIONS = (1 << 0)
MWM_HINTS_DECORATIONS = (1 << 1)

# bit definitions for functions 
MWM_FUNC_ALL       = (1 << 0)
MWM_FUNC_RESIZE    = (1 << 1)
MWM_FUNC_MOVE      = (1 << 2)
MWM_FUNC_MINIMIZE  = (1 << 3)
MWM_FUNC_MAXIMIZE  = (1 << 4)
MWM_FUNC_CLOSE     = (1 << 5)

# bit definitions for decorations 
MWM_DECOR_ALL      = (1 << 0)
MWM_DECOR_BORDER   = (1 << 1)
MWM_DECOR_RESIZEH  = (1 << 2)
MWM_DECOR_TITLE    = (1 << 3)
MWM_DECOR_MENU     = (1 << 4)
MWM_DECOR_MINIMIZE = (1 << 5)
MWM_DECOR_MAXIMIZE = (1 << 6)
