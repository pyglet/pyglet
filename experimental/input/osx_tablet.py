#!/usr/bin/env python

'''
'''

__docformat__ = 'restructuredtext'
__version__ = '$Id: $'

import ctypes

import pyglet
from pyglet.window.carbon import CarbonEventHandler, carbon, _oscheck
from pyglet.window.carbon.constants import *
from pyglet.window.carbon.constants import _name

kEventTabletPoint = 1
kEventTabletProximity = 2
kEventParamTabletPointRec = _name('tbrc')
kEventParamTabletProximityRec = _name('tbpx')
typeTabletPointRec = _name('tbrc')
typeTabletProximityRec = _name('tbpx')

class TabletProximityRec(ctypes.Structure):
    _fields_ = (
        ('vendorID', ctypes.c_uint16),
        ('tabletID', ctypes.c_uint16),
        ('pointerID', ctypes.c_uint16),
        ('deviceID', ctypes.c_uint16),
        ('systemTabletID', ctypes.c_uint16),
        ('vendorPointerType', ctypes.c_uint16),
        ('pointerSerialNumber', ctypes.c_uint32),
        ('uniqueID', ctypes.c_uint64),
        ('capabilityMask', ctypes.c_uint32),
        ('pointerType', ctypes.c_uint8),
        ('enterProximity', ctypes.c_uint8),
    )

class TabletPointRec(ctypes.Structure):
    _fields_ = (
        ('absX', ctypes.c_int32),
        ('absY', ctypes.c_int32),
        ('absZ', ctypes.c_int32),
        ('buttons', ctypes.c_uint16),
        ('pressure', ctypes.c_uint16),
        ('tiltX', ctypes.c_int16),
        ('tiltY', ctypes.c_int16),
        ('rotation', ctypes.c_uint16),
        ('tangentialPressure', ctypes.c_int16),
        ('deviceID', ctypes.c_uint16),
        ('vendor1', ctypes.c_int16),
        ('vendor2', ctypes.c_int16),
        ('vendor3', ctypes.c_int16),
    )

class TabletWindow(pyglet.window.Window):
    def _tablet_event(self, ev):
        '''Process tablet event and return True if some event was processed.
        Return True if no tablet event found.
        '''
        event_type = ctypes.c_uint32()
        r = carbon.GetEventParameter(ev, kEventParamTabletEventType,
            typeUInt32, None,
            ctypes.sizeof(event_type), None,
            ctypes.byref(event_type))
        if r != noErr:
            return False

        if event_type.value == kEventTabletProximity:
            proximity_rec = TabletProximityRec()
            _oscheck(
            carbon.GetEventParameter(ev, kEventParamTabletProximityRec,
                typeTabletProximityRec, None, 
                ctypes.sizeof(proximity_rec), None, 
                ctypes.byref(proximity_rec))
            )
            print (proximity_rec.vendorID,
                proximity_rec.tabletID, proximity_rec.pointerID,
                proximity_rec.deviceID, proximity_rec.systemTabletID,
                proximity_rec.vendorPointerType,
                proximity_rec.pointerSerialNumber,
                proximity_rec.uniqueID,
                proximity_rec.capabilityMask,
                't', proximity_rec.pointerType,
                proximity_rec.enterProximity,
            )

        if event_type.value == kEventTabletPoint:
            point_rec = TabletPointRec()
            _oscheck(
            carbon.GetEventParameter(ev, kEventParamTabletPointRec,
                typeTabletPointRec, None,
                ctypes.sizeof(point_rec), None,
                ctypes.byref(point_rec))
            )
            print (point_rec.absX, 
                   point_rec.absY,
                   point_rec.absZ,
                   point_rec.buttons,
                   point_rec.pressure,
                   point_rec.tiltX,
                   point_rec.tiltY,
                   point_rec.rotation,
                   point_rec.tangentialPressure,
                   point_rec.deviceID,
                   point_rec.vendor1,
                   point_rec.vendor2,
                   point_rec.vendor3,
               )

        return True

    @CarbonEventHandler(kEventClassTablet, kEventTabletProximity)    
    def _on_tablet_proximity(self, next_handler, ev, data):
        self._tablet_event(ev)
        carbon.CallNextEventHandler(next_handler, ev)
        return noErr

    @CarbonEventHandler(kEventClassTablet, kEventTabletPoint)    
    def _on_tablet_point(self, next_handler, ev, data):
        self._tablet_event(ev)
        carbon.CallNextEventHandler(next_handler, ev)
        return noErr

    @CarbonEventHandler(kEventClassMouse, kEventMouseDragged)
    def _on_mouse_dragged(self, next_handler, ev, data):
        self._tablet_event(ev)
        return super(TabletWindow, self)._on_mouse_dragged(
            next_handler, ev, data)

    @CarbonEventHandler(kEventClassMouse, kEventMouseDown)
    def _on_mouse_down(self, next_handler, ev, data):
        self._tablet_event(ev)
        return super(TabletWindow, self)._on_mouse_down(
            next_handler, ev, data)

    @CarbonEventHandler(kEventClassMouse, kEventMouseUp)
    def _on_mouse_up(self, next_handler, ev, data):
        self._tablet_event(ev)
        return super(TabletWindow, self)._on_mouse_up(
            next_handler, ev, data)

    @CarbonEventHandler(kEventClassMouse, kEventMouseMoved)
    def _on_mouse_moved(self, next_handler, ev, data):
        self._tablet_event(ev)
        return super(TabletWindow, self)._on_mouse_moved(
            next_handler, ev, data)



if __name__ == '__main__':
    TabletWindow()
    pyglet.app.run()

