import ctypes
from collections import defaultdict
import pyglet
from pyglet.input.base import DeviceOpenException
from pyglet.input.base import Tablet, TabletCanvas
from pyglet.libs.win32 import libwintab as wintab
from pyglet.util import debug_print

_debug = debug_print('debug_input')

lib = wintab.lib


def wtinfo(category, index, buffer):
    size = lib.WTInfoW(category, index, None)
    assert size <= ctypes.sizeof(buffer)
    lib.WTInfoW(category, index, ctypes.byref(buffer))
    return buffer


def wtinfo_string(category, index):
    size = lib.WTInfoW(category, index, None)
    buffer = ctypes.create_unicode_buffer(size)
    lib.WTInfoW(category, index, buffer)
    return buffer.value


def wtinfo_uint(category, index):
    buffer = wintab.UINT()
    lib.WTInfoW(category, index, ctypes.byref(buffer))
    return buffer.value


def wtinfo_word(category, index):
    buffer = wintab.WORD()
    lib.WTInfoW(category, index, ctypes.byref(buffer))
    return buffer.value


def wtinfo_dword(category, index):
    buffer = wintab.DWORD()
    lib.WTInfoW(category, index, ctypes.byref(buffer))
    return buffer.value


def wtinfo_wtpkt(category, index):
    buffer = wintab.WTPKT()
    lib.WTInfoW(category, index, ctypes.byref(buffer))
    return buffer.value


def wtinfo_bool(category, index):
    buffer = wintab.BOOL()
    lib.WTInfoW(category, index, ctypes.byref(buffer))
    return bool(buffer.value)


class WintabTablet(Tablet):
    def __init__(self, index):
        self._device = wintab.WTI_DEVICES + index
        self.name = wtinfo_string(self._device, wintab.DVC_NAME).strip()
        self.id = wtinfo_string(self._device, wintab.DVC_PNPID)

        hardware = wtinfo_uint(self._device, wintab.DVC_HARDWARE)
        # phys_cursors = hardware & wintab.HWC_PHYSID_CURSORS

        n_cursors = wtinfo_uint(self._device, wintab.DVC_NCSRTYPES)
        first_cursor = wtinfo_uint(self._device, wintab.DVC_FIRSTCSR)

        self.pressure_axis = wtinfo(self._device, wintab.DVC_NPRESSURE, wintab.AXIS())

        self.cursors = []
        self._cursor_map = {}

        for i in range(n_cursors):
            cursor = WintabTabletCursor(self, i + first_cursor)
            if not cursor.bogus:
                self.cursors.append(cursor)
                self._cursor_map[i + first_cursor] = cursor

    def open(self, window):
        return WintabTabletCanvas(self, window)


class WintabTabletCanvas(TabletCanvas):
    override_keys = False

    def __init__(self, device, window, msg_base=wintab.WT_DEFBASE):
        super(WintabTabletCanvas, self).__init__(window)

        self.device = device
        self.msg_base = msg_base

        # Get the extension masks available. Only need to do this once.
        global _extension_masks
        if not _extension_masks:
            _extension_masks = get_extension_masks()

        # Just use system context, for similarity w/ os x and xinput.
        # WTI_DEFCONTEXT detaches mouse from tablet, which is nice, but not
        # possible on os x afiak.
        self.context_info = context_info = wintab.LOGCONTEXT()
        wtinfo(wintab.WTI_DEFSYSCTX, 0, context_info)
        context_info.lcMsgBase = msg_base
        context_info.lcOptions |= wintab.CXO_MESSAGES

        # If you change this, change definition of PACKET also.
        context_info.lcPktData = (
                                         wintab.PK_CHANGED | wintab.PK_CURSOR | wintab.PK_BUTTONS |
                                         wintab.PK_X | wintab.PK_Y | wintab.PK_Z |
                                         wintab.PK_NORMAL_PRESSURE | wintab.PK_TANGENT_PRESSURE |
                                         wintab.PK_ORIENTATION) | _extension_masks
        context_info.lcPktMode = 0  # All absolute (PACKETMODE)

        self._context = lib.WTOpenW(window._hwnd, ctypes.byref(context_info), True)
        if not self._context:
            raise DeviceOpenException("Couldn't open tablet context")

        window._event_handlers[msg_base + wintab.WT_PACKET] = self._event_wt_packet
        window._event_handlers[msg_base + wintab.WT_PROXIMITY] = self._event_wt_proximity

        if _extension_masks:
            window._event_handlers[msg_base + wintab.WT_PACKETEXT] = self._event_wt_packetext

        self._current_cursor = None
        self._pressure_scale = device.pressure_axis.get_scale()
        self._pressure_bias = device.pressure_axis.get_bias()

        self.express_keys = defaultdict(lambda: defaultdict(bool))  # [control_id][location_id]
        self.express_key_ct = 0
        self.touchrings = []  # Not currently implemented.
        self.touchstrips = []  # Not currently implemented.

        # Override test
        for tablet_id in range(get_tablet_count()):
            control_count = self.extension_get(wintab.WTX_EXPKEYS2, tablet_id, 0, 0,
                                               wintab.TABLET_PROPERTY_CONTROLCOUNT)
            self.express_key_ct = control_count
            assert _debug(f"Controls Found: {control_count}")
            if self.override_keys is True:
                for control_id in range(control_count):
                    function_count = self.extension_get(wintab.WTX_EXPKEYS2, tablet_id, control_id, 0,
                                                        wintab.TABLET_PROPERTY_FUNCCOUNT)
                    for function_id in range(function_count):
                        self.extension_set(wintab.WTX_EXPKEYS2, tablet_id, control_id, function_id,
                                           wintab.TABLET_PROPERTY_OVERRIDE, wintab.BOOL(True))

    def extension_get(self, extension, tablet_id, control_id, function_id, property_id, value_type=wintab.UINT):
        prop = wintab.EXTPROPERTY()

        prop.version = 0
        prop.tabletIndex = tablet_id
        prop.controlIndex = control_id
        prop.functionIndex = function_id
        prop.propertyID = property_id
        prop.reserved = 0
        prop.dataSize = ctypes.sizeof(value_type)

        success = lib.WTExtGet(self._context, extension, ctypes.byref(prop))
        if success:
            return ctypes.cast(prop.data, ctypes.POINTER(value_type)).contents.value

        return 0

    def extension_set(self, extension, tablet_id, control_id, function_id, property_id, value):
        prop = wintab.EXTPROPERTY()
        prop.version = 0
        prop.tabletIndex = tablet_id
        prop.controlIndex = control_id
        prop.functionIndex = function_id
        prop.propertyID = property_id
        prop.reserved = 0
        prop.dataSize = ctypes.sizeof(value)
        prop.data[0] = value.value

        success = lib.WTExtSet(self._context, extension, ctypes.byref(prop))
        if success:
            return True

        return False

    def close(self):
        lib.WTClose(self._context)
        self._context = None

        del self.window._event_handlers[self.msg_base + wintab.WT_PACKET]
        del self.window._event_handlers[self.msg_base + wintab.WT_PROXIMITY]

        if _extension_masks:
            del self.window._event_handlers[self.msg_base + wintab.WT_PACKETEXT]

    def _set_current_cursor(self, cursor_type):
        if self._current_cursor:
            self.dispatch_event('on_leave', self._current_cursor)

        self._current_cursor = self.device._cursor_map.get(cursor_type, None)

        if self._current_cursor:
            self.dispatch_event('on_enter', self._current_cursor)

    @pyglet.window.win32.Win32EventHandler(0)
    def _event_wt_packet(self, msg, wParam, lParam):
        if lParam != self._context:
            return

        packet = wintab.PACKET()
        if lib.WTPacket(self._context, wParam, ctypes.byref(packet)) == 0:
            return

        if not packet.pkChanged:
            return

        window_x, window_y = self.window.get_location()  # TODO cache on window
        window_y = self.window.screen.height - window_y - self.window.height
        x = packet.pkX - window_x
        y = packet.pkY - window_y
        pressure = (packet.pkNormalPressure + self._pressure_bias) * self._pressure_scale

        if self._current_cursor is None:
            self._set_current_cursor(packet.pkCursor)

        self.dispatch_event('on_motion', self._current_cursor, x, y, pressure, 0., 0., packet.pkButtons)

    @pyglet.window.win32.Win32EventHandler(0)
    def _event_wt_packetext(self, msg, wParam, lParam):
        packet = wintab.PACKETEXT()
        if lib.WTPacket(lParam, wParam, ctypes.byref(packet)) == 0:
            return

        # Proper context exists in the packet, not the lParam.
        if packet.pkBase.nContext == self._context:
            if packet.pkExpKeys.nControl < self.express_key_ct:
                current_state = self.express_keys[packet.pkExpKeys.nControl][packet.pkExpKeys.nLocation]
                new_state = bool(packet.pkExpKeys.nState)
                if current_state != new_state:
                    event_type = "on_express_key_press" if new_state else "on_express_key_release"

                    self.express_keys[packet.pkExpKeys.nControl][packet.pkExpKeys.nLocation] = new_state

                    self.dispatch_event(event_type, packet.pkExpKeys.nControl, packet.pkExpKeys.nLocation)

    @pyglet.window.win32.Win32EventHandler(0)
    def _event_wt_proximity(self, msg, wParam, lParam):
        if wParam != self._context:
            return

        if not lParam & 0xffff0000:
            # Not a hardware proximity event
            return

        if not lParam & 0xffff:
            # Going out
            self.dispatch_event('on_leave', self._current_cursor)

        # If going in, proximity event will be generated by next event, which
        # can actually grab a cursor id.
        self._current_cursor = None

    # Events

    def on_express_key_press(self, control_id: int, location_id: int):
        """An event called when an ExpressKey is pressed down.

        Args:
            control_id:
                Zero-based index number given to the assigned key by the driver.
                The same control_id may exist in multiple locations, which the location_id is used to differentiate.
            location_id:
                Zero-based index indicating side of tablet where control id was found.
                Some tablets may have clusters of ExpressKey's on various areas of the tablet.
                (0 = left, 1 = right, 2 = top, 3 = bottom, 4 = transducer).
        """

    def on_express_key_release(self, control_id: int, location_id: int):
        """An event called when an ExpressKey is released.

        Args:
            control_id:
                Zero-based index number given to the assigned key by the driver.
                The same control_id may exist in multiple locations, which the location_id is used to differentiate.
            location_id:
                Zero-based index indicating side of tablet where control id was found.
                Some tablets may have clusters of ExpressKey's on various areas of the tablet.
                (0 = left, 1 = right, 2 = top, 3 = bottom, 4 = transducer).
        """


WintabTabletCanvas.register_event_type('on_express_key_press')
WintabTabletCanvas.register_event_type('on_express_key_release')


class WintabTabletCursor:
    def __init__(self, device, index):
        self.device = device
        self._cursor = wintab.WTI_CURSORS + index

        self.name = wtinfo_string(self._cursor, wintab.CSR_NAME).strip()
        self.active = wtinfo_bool(self._cursor, wintab.CSR_ACTIVE)
        pktdata = wtinfo_wtpkt(self._cursor, wintab.CSR_PKTDATA)

        # A whole bunch of cursors are reported by the driver, but most of
        # them are hogwash.  Make sure a cursor has at least X and Y data
        # before adding it to the device.
        self.bogus = not (pktdata & wintab.PK_X and pktdata & wintab.PK_Y)
        if self.bogus:
            return

        self.id = (wtinfo_dword(self._cursor, wintab.CSR_TYPE) << 32) | \
                  wtinfo_dword(self._cursor, wintab.CSR_PHYSID)

    def __repr__(self):
        return 'WintabCursor(%r)' % self.name


def get_spec_version():
    spec_version = wtinfo_word(wintab.WTI_INTERFACE, wintab.IFC_SPECVERSION)
    return spec_version


def get_interface_name():
    interface_name = wtinfo_string(wintab.WTI_INTERFACE, wintab.IFC_WINTABID)
    return interface_name


def get_implementation_version():
    impl_version = wtinfo_word(wintab.WTI_INTERFACE, wintab.IFC_IMPLVERSION)
    return impl_version


def extension_index(ext):
    """Check if a particular extension exists within the driver."""
    exists = True
    i = 0
    index = 0xFFFFFFFF

    while exists:
        tag = wintab.UINT()
        exists = lib.WTInfoW(wintab.WTI_EXTENSIONS + i, wintab.EXT_TAG, ctypes.byref(tag))
        if tag.value == ext:
            index = i
            break

        i += 1

    if index != 0xFFFFFFFF:
        return index

    return None


def get_extension_masks():
    """Determine which extension support is available by getting the masks."""
    masks = 0
    tr_idx = extension_index(wintab.WTX_TOUCHRING)
    if tr_idx is not None:
        assert _debug("Touchring support found")
        masks |= wtinfo_uint(wintab.WTI_EXTENSIONS + tr_idx, wintab.EXT_MASK)
    else:
        assert _debug("Touchring extension not found.")

    ts_idx = extension_index(wintab.WTX_TOUCHSTRIP)
    if ts_idx is not None:
        assert _debug("Touchstrip support found.")
        masks |= wtinfo_uint(wintab.WTI_EXTENSIONS + ts_idx, wintab.EXT_MASK)
    else:
        assert _debug("Touchstrip extension not found.")

    expkeys_idx = extension_index(wintab.WTX_EXPKEYS2)
    if expkeys_idx is not None:
        assert _debug("ExpressKey support found.")
        masks |= wtinfo_uint(wintab.WTI_EXTENSIONS + expkeys_idx, wintab.EXT_MASK)
    else:
        assert _debug("ExpressKey extension not found.")

    return masks


def get_tablet_count():
    """Return just the number of current devices."""
    spec_version = get_spec_version()
    assert _debug(f"Wintab Version: {spec_version}")
    if spec_version < 0x101:
        return 0

    n_devices = wtinfo_uint(wintab.WTI_INTERFACE, wintab.IFC_NDEVICES)
    return n_devices


_extension_masks = None


def get_tablets(display=None):
    # Require spec version 1.1 or greater
    n_devices = get_tablet_count()
    if not n_devices:
        return []

    devices = [WintabTablet(i) for i in range(n_devices)]
    return devices
