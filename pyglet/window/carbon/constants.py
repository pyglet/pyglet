#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

# CFString.h
kCFStringEncodingMacRoman = 0
kCFStringEncodingWindowsLatin1 = 0x0500
kCFStringEncodingISOLatin1 = 0x0201
kCFStringEncodingNextStepLatin = 0x0B01
kCFStringEncodingASCII = 0x0600
kCFStringEncodingUnicode = 0x0100
kCFStringEncodingUTF8 = 0x08000100
kCFStringEncodingNonLossyASCII = 0x0BFF

# MacTypes.h
noErr = 0

# CarbonEventsCore.h
eventLoopTimedOutErr = -9875

# MacWindows.h
kAlertWindowClass = 1
kMovableAlertWindowClass = 2
kModalWindowClass = 3
kMovableModalWindowClass = 4
kFloatingWindowClass = 5
kDocumentWindowClass = 6
kUtilityWindowClass = 8
kHelpWindowClass = 10
kSheetWindowClass = 11
kToolbarWindowClass = 12
kPlainWindowClass = 13
kSheetAlertWindowClass = 15
kAltPlainWindowClass = 16
kSimpleWindowClass = 18  # no window frame
kDrawerWindowClass = 20

kWindowNoAttributes = 0x0
kWindowCloseBoxAttribute = 0x1
kWindowHorizontalZoomAttribute = 0x2
kWindowVerticalZoomAttribute = 0x4
kWindowFullZoomAttribute = kWindowHorizontalZoomAttribute | \
    kWindowVerticalZoomAttribute
kWindowCollapseBoxAttribute = 0x8
kWindowResizableAttribute = 0x10 
kWindowSideTitlebarAttribute = 0x20
kWindowToolbarAttribute = 0x40
kWindowMetalAttribute = 1 << 8
kWindowDoesNotCycleAttribute = 1 << 15
kWindowNoupdatesAttribute = 1 << 16
kWindowNoActivatesAttribute = 1 << 17
kWindowOpaqueForEventsAttribute = 1 << 18
kWindowCompositingAttribute = 1 << 19
kWindowNoShadowAttribute = 1 << 21
kWindowHideOnSuspendAttribute = 1 << 24
kWindowAsyncDragAttribute = 1 << 23
kWindowStandardHandlerAttribute = 1 << 25
kWindowHideOnFullScreenAttribute = 1 << 26
kWindowInWindowMenuAttribute = 1 << 27
kWindowLiveResizeAttribute = 1 << 28
kWindowIgnoreClicksAttribute = 1 << 29
kWindowNoConstrainAttribute = 1 << 31
kWindowStandardDocumentAttributes = kWindowCloseBoxAttribute | \
                                    kWindowFullZoomAttribute | \
                                    kWindowCollapseBoxAttribute | \
                                    kWindowResizableAttribute
kWindowStandardFloatingAttributes = kWindowCloseBoxAttribute | \
                                    kWindowCollapseBoxAttribute

kWindowCenterOnMainScreen = 1
kWindowCenterOnParentWindow = 2
kWindowCenterOnParentWindowScreen = 3
kWindowCascadeOnMainScreen = 4
kWindowCascadeOnParentWindow = 5
kWindowCascadeonParentWindowScreen = 6
kWindowCascadeStartAtParentWindowScreen = 10
kWindowAlertPositionOnMainScreen = 7
kWindowAlertPositionOnParentWindow = 8
kWindowAlertPositionOnParentWindowScreen = 9


kWindowTitleBarRgn            = 0
kWindowTitleTextRgn           = 1
kWindowCloseBoxRgn            = 2
kWindowZoomBoxRgn             = 3
kWindowDragRgn                = 5
kWindowGrowRgn                = 6
kWindowCollapseBoxRgn         = 7
kWindowTitleProxyIconRgn      = 8
kWindowStructureRgn           = 32
kWindowContentRgn             = 33
kWindowUpdateRgn              = 34
kWindowOpaqueRgn              = 35
kWindowGlobalPortRgn          = 40
kWindowToolbarButtonRgn       = 41

def _name(name):
    return ord(name[0]) << 24 | \
           ord(name[1]) << 16 | \
           ord(name[2]) << 8 | \
           ord(name[3])

# AEDataModel.h

typeBoolean = _name('bool')
typeChar = _name('TEXT')
typeSInt16 = _name('shor')
typeSInt32 = _name('long')
typeUInt32 = _name('magn')
typeSInt64 = _name('comp')
typeIEEE32BitFloatingPoint = _name('sing')
typeIEEE64BitFloatingPoint = _name('doub')
type128BitFloatingPoint = _name('ldbl')
typeDecimalStruct = _name('decm')

# AERegistry.h
typeUnicodeText = _name('utxt')
typeStyledUnicodeText = _name('sutx')
typeUTF8Text = _name('utf8')
typeEncodedString = _name('encs')
typeCString = _name('cstr')
typePString = _name('pstr')
typeEventRef = _name('evrf')

# CarbonEvents.h

kEventParamWindowRef          = _name('wind')
kEventParamGrafPort           = _name('graf')
kEventParamMenuRef            = _name('menu')
kEventParamEventRef           = _name('evnt')
kEventParamControlRef         = _name('ctrl')
kEventParamRgnHandle          = _name('rgnh')
kEventParamEnabled            = _name('enab')
kEventParamDimensions         = _name('dims')
kEventParamBounds             = _name('boun')
kEventParamAvailableBounds    = _name('avlb')
#kEventParamAEEventID          = keyAEEventID
#kEventParamAEEventClass       = keyAEEventClass
kEventParamCGContextRef       = _name('cntx')
kEventParamDeviceDepth        = _name('devd')
kEventParamDeviceColor        = _name('devc')
kEventParamMutableArray       = _name('marr')
kEventParamResult             = _name('ansr')
kEventParamMinimumSize        = _name('mnsz')
kEventParamMaximumSize        = _name('mxsz')
kEventParamAttributes         = _name('attr')
kEventParamReason             = _name('why?')
kEventParamTransactionID      = _name('trns')
kEventParamGDevice            = _name('gdev')
kEventParamIndex              = _name('indx')
kEventParamUserData           = _name('usrd')
kEventParamShape              = _name('shap')
typeWindowRef                 = _name('wind')
typeGrafPtr                   = _name('graf')
typeGWorldPtr                 = _name('gwld')
typeMenuRef                   = _name('menu')
typeControlRef                = _name('ctrl')
typeCollection                = _name('cltn')
typeQDRgnHandle               = _name('rgnh')
typeOSStatus                  = _name('osst')
typeCFIndex                   = _name('cfix')
typeCGContextRef              = _name('cntx')
typeHIPoint                   = _name('hipt')
typeHISize                    = _name('hisz')
typeHIRect                    = _name('hirc')
typeHIShapeRef                = _name('shap')
typeVoidPtr                   = _name('void')
typeGDHandle                  = _name('gdev') 

kEventClassMouse = _name('mous')
kEventClassKeyboard = _name('keyb')
kEventClassTextInput = _name('text')
kEventClassApplication = _name('appl')
kEventClassAppleEvent = _name('eppc')
kEventClassMenu = _name('menu')
kEventClassWindow = _name('wind')
kEventClassControl = _name('cntl')
kEventClassCommand = _name('cmds')
kEventClassTablet = _name('tblt')
kEventClassVolume = _name('vol ')
kEventClassAppearance = _name('appm')
kEventClassService = _name('serv')
kEventClassToolbar = _name('tbar')
kEventClassToolbarItem = _name('tbit')
kEventClassToolbarItemView = _name('tbiv')
kEventClassAccessibility = _name('acce')
kEventClassSystem = _name('macs')
kEventClassInk = _name('ink ')
kEventClassTSMDocumentAccess = _name('tdac')

# Keyboard
kEventRawKeyDown                = 1
kEventRawKeyRepeat              = 2
kEventRawKeyUp                  = 3
kEventRawKeyModifiersChanged    = 4
kEventHotKeyPressed             = 5
kEventHotKeyReleased            = 6

kEventParamKeyCode = _name('kcod')
kEventParamKeyMacCharCodes = _name('kchr')
kEventParamKeyModifiers = _name('kmod')
kEventParamKeyUnicodes = _name('kuni')
kEventParamKeyboardType = _name('kbdt')
typeEventHotKeyID = _name('hkid')

activeFlagBit                 = 0
btnStateBit                   = 7
cmdKeyBit                     = 8
shiftKeyBit                   = 9
alphaLockBit                  = 10
optionKeyBit                  = 11
controlKeyBit                 = 12
rightShiftKeyBit              = 13
rightOptionKeyBit             = 14
rightControlKeyBit            = 15
numLockBit                    = 16

activeFlag                    = 1 << activeFlagBit
btnState                      = 1 << btnStateBit
cmdKey                        = 1 << cmdKeyBit
shiftKey                      = 1 << shiftKeyBit
alphaLock                     = 1 << alphaLockBit
optionKey                     = 1 << optionKeyBit
controlKey                    = 1 << controlKeyBit
rightShiftKey                 = 1 << rightShiftKeyBit
rightOptionKey                = 1 << rightOptionKeyBit
rightControlKey               = 1 << rightControlKeyBit
numLock                       = 1 << numLockBit

# TextInput
kEventTextInputUpdateActiveInputArea    = 1
kEventTextInputUnicodeForKeyEvent       = 2
kEventTextInputOffsetToPos              = 3
kEventTextInputPosToOffset              = 4
kEventTextInputShowHideBottomWindow     = 5
kEventTextInputGetSelectedText          = 6
kEventTextInputUnicodeText              = 7

kEventParamTextInputSendText = _name('tstx')
kEventParamTextInputSendKeyboardEvent = _name('tske')

# Mouse
kEventMouseDown                 = 1
kEventMouseUp                   = 2
kEventMouseMoved                = 5
kEventMouseDragged              = 6
kEventMouseEntered              = 8
kEventMouseExited               = 9
kEventMouseWheelMoved           = 10
kEventParamMouseLocation = _name('mloc')
kEventParamWindowMouseLocation = _name('wmou')
kEventParamMouseButton = _name('mbtn')
kEventParamClickCount = _name('ccnt')
kEventParamMouseWheelAxis = _name('mwax')
kEventParamMouseWheelDelta = _name('mwdl')
kEventParamMouseDelta = _name('mdta')
kEventParamMouseChord = _name('chor')
kEventParamTabletEventType = _name('tblt')
kEventParamMouseTrackingRef = _name('mtrf')
typeMouseButton         = _name('mbtn')
typeMouseWheelAxis      = _name('mwax')
typeMouseTrackingRef    = _name('mtrf')

kEventMouseButtonPrimary = 1
kEventMouseButtonSecondary = 2
kEventMouseButtonTertiary = 3

