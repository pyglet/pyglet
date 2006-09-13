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

