"""DualSense HID reader - reads raw HID reports like DS4Windows.

Replaces pygame-based dualsense_bridge.py.
Parses button IDs directly from HID report bytes.
"""
import hid
import logging
import threading
import time

_log = logging.getLogger("autoloot.dualsense_hid")

# DualSense USB Vendor/Product IDs
DS_VID = 0x054C
DS_PID = 0x0CE6

# HID report layout (Report ID 0x01):
# Byte 0: Report ID (0x01)
# Byte 1: Left Stick X (0-255, center=128)
# Byte 2: Left Stick Y (0-255, center=128)
# Byte 3: Right Stick X (0-255, center=128)
# Byte 4: Right Stick Y (0-255, center=128)
# Byte 5: L2 Trigger (0-255)
# Byte 6: R2 Trigger (0-255)
# Byte 7: Sequence number
# Byte 8: Hat switch (bits 0-3) + Square(bit4) Cross(bit5) Circle(bit6) Triangle(bit7)
# Byte 9: L1(bit0) R1(bit1) L2-btn(bit2) R2-btn(bit3) Create(bit4) Options(bit5) L3(bit6) R3(bit7)
# Byte 10: PS(bit0) Touchpad(bit1) Mute(bit2)

HAT_UP = 0
HAT_UP_RIGHT = 1
HAT_RIGHT = 2
HAT_DOWN_RIGHT = 3
HAT_DOWN = 4
HAT_DOWN_LEFT = 5
HAT_LEFT = 6
HAT_UP_LEFT = 7
HAT_CENTERED = 8

# XInput button masks
XINPUT_A = 0x1000
XINPUT_B = 0x2000
XINPUT_X = 0x4000
XINPUT_Y = 0x8000
XINPUT_LB = 0x0100
XINPUT_RB = 0x0200
XINPUT_BACK = 0x0020
XINPUT_START = 0x0010
XINPUT_L3 = 0x0040
XINPUT_R3 = 0x0080
XINPUT_DPAD_UP = 0x0001
XINPUT_DPAD_DOWN = 0x0002
XINPUT_DPAD_LEFT = 0x0004
XINPUT_DPAD_RIGHT = 0x0008

# Activation output report (enables input reports on DualSense)
ACTIVATION_REPORT = bytes([
    0x02,  # Report ID
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
])


class DualSenseHIDReader:
    """Reads DualSense input via raw HID (like DS4Windows)."""

    def __init__(self, virtual_gamepad):
        self._gp = virtual_gamepad
        self._thread = None
        self._stop = None
        self._dev = None

    def start(self):
        """Find and open DualSense HID device."""
        try:
            self._dev = hid.device()
            self._dev.open(DS_VID, DS_PID)
        except Exception as e:
            _log.warning("Cannot open DualSense HID: %s", e)
            return False

        # Send activation report to enable input
        try:
            self._dev.write(ACTIVATION_REPORT)
            _log.info("DualSense activation report sent")
        except Exception as e:
            _log.warning("Activation failed: %s (may already be active)", e)

        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        _log.info("DualSense HID reader started")
        return True

    def stop(self):
        if self._stop:
            self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        if self._dev:
            try:
                self._dev.close()
            except Exception:
                pass
            self._dev = None

    def _loop(self):
        prev_btn8 = 0
        prev_btn9 = 0
        prev_btn10 = 0

        while not self._stop.is_set():
            try:
                report = self._dev.read(64)
                if not report or len(report) < 11:
                    continue

                # Sticks (center = 128, range 0-255)
                lx = report[1]
                ly = report[2]
                rx = report[3]
                ry = report[4]
                lx_val = int((lx - 128) * 256)  # -32768..32767
                ly_val = int((128 - ly) * 256)  # INVERTED: DualSense 0=up, XInput 32767=up
                rx_val = int((rx - 128) * 256)
                ry_val = int((128 - ry) * 256)  # INVERTED
                lx_val = max(-32767, min(32767, lx_val))
                ly_val = max(-32767, min(32767, ly_val))
                rx_val = max(-32767, min(32767, rx_val))
                ry_val = max(-32767, min(32767, ry_val))
                self._gp.left_joystick(x_value=lx_val, y_value=ly_val)
                self._gp.right_joystick(x_value=rx_val, y_value=ry_val)

                # Triggers (0-255)
                l2 = report[5]
                r2 = report[6]
                self._gp.left_trigger(value=l2)
                self._gp.right_trigger(value=r2)

                # Buttons byte 8
                b8 = report[8]
                hat = b8 & 0x0F
                sq = bool(b8 & 0x10)
                cross = bool(b8 & 0x20)
                circ = bool(b8 & 0x40)
                tri = bool(b8 & 0x80)

                # Buttons byte 9
                b9 = report[9]
                l1 = bool(b9 & 0x01)
                r1 = bool(b9 & 0x02)
                create = bool(b9 & 0x10)
                options = bool(b9 & 0x20)
                l3 = bool(b9 & 0x40)
                r3 = bool(b9 & 0x80)

                # Buttons byte 10
                b10 = report[10]
                ps = bool(b10 & 0x01)
                touchpad = bool(b10 & 0x02)

                # Map to Xbox buttons on state change
                self._map_button(cross, prev_btn8 & 0x20, XINPUT_A, "Cross->A")
                self._map_button(circ, prev_btn8 & 0x40, XINPUT_B, "Circle->B")
                self._map_button(sq, prev_btn8 & 0x10, XINPUT_X, "Square->X")
                self._map_button(tri, prev_btn8 & 0x80, XINPUT_Y, "Triangle->Y")
                self._map_button(l1, prev_btn9 & 0x01, XINPUT_LB, "L1->LB")
                self._map_button(r1, prev_btn9 & 0x02, XINPUT_RB, "R1->RB")
                self._map_button(l3, prev_btn9 & 0x40, XINPUT_L3, "L3")
                self._map_button(r3, prev_btn9 & 0x80, XINPUT_R3, "R3")
                self._map_button(create, prev_btn9 & 0x10, XINPUT_BACK, "Create->Back")
                self._map_button(options, prev_btn9 & 0x20, XINPUT_START, "Options->Start")

                # Hat switch (D-pad)
                prev_hat = prev_btn8 & 0x0F
                if hat != prev_hat:
                    self._map_hat(hat)

                self._gp.update()
                prev_btn8 = b8
                prev_btn9 = b9
                prev_btn10 = b10

            except Exception as e:
                _log.debug("HID read error: %s", e)

    def _map_button(self, pressed, was_pressed, xinput_mask, name):
        if pressed and not was_pressed:
            self._gp.press_button(button=xinput_mask)
            _log.debug("HID: %s DOWN", name)
        elif not pressed and was_pressed:
            self._gp.release_button(button=xinput_mask)
            _log.debug("HID: %s UP", name)

    def _map_hat(self, hat):
        masks = {
            HAT_UP: XINPUT_DPAD_UP,
            HAT_UP_RIGHT: XINPUT_DPAD_UP | XINPUT_DPAD_RIGHT,
            HAT_RIGHT: XINPUT_DPAD_RIGHT,
            HAT_DOWN_RIGHT: XINPUT_DPAD_DOWN | XINPUT_DPAD_RIGHT,
            HAT_DOWN: XINPUT_DPAD_DOWN,
            HAT_DOWN_LEFT: XINPUT_DPAD_DOWN | XINPUT_DPAD_LEFT,
            HAT_LEFT: XINPUT_DPAD_LEFT,
            HAT_UP_LEFT: XINPUT_DPAD_UP | XINPUT_DPAD_LEFT,
        }
        mask = masks.get(hat, 0)
        if mask:
            self._gp.press_button(button=mask)
            _log.debug("HID: D-pad %d", hat)
        else:
            # Release all D-pad buttons
            for m in [XINPUT_DPAD_UP, XINPUT_DPAD_DOWN, XINPUT_DPAD_LEFT, XINPUT_DPAD_RIGHT]:
                self._gp.release_button(button=m)
