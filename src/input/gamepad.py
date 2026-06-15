"""Эмуляция джойстика через виртуальный Xbox контроллер.

Позволяет боту нажимать кнопки джойстика (X, L2 и т.д.)
без реального джойстика.

Требует: vgamepad (pip install vgamepad)
Для PoE2: X=подбор, L2=HP фласка, R2=MP фласка
"""
import json
import logging
import time
from pathlib import Path

_log = logging.getLogger("autoloot.gamepad")

try:
    import vgamepad as vg
    HAS_VGAMEPAD = True
except ImportError:
    HAS_VGAMEPAD = False

MAPPING_FILE = Path(__file__).resolve().parents[2] / "config" / "gamepad" / "mapping.json"


class GamepadEmulator:
    """Эмуляция Xbox контроллера для PoE2."""

    def __init__(self):
        self._gamepad = None
        self.enabled = False
        self._mapping = self._load_mapping()

        if HAS_VGAMEPAD:
            try:
                self._gamepad = vg.VX360Gamepad()
                self.enabled = True
                _log.info("Virtual Xbox controller created")
            except Exception as e:
                _log.warning("Failed to create controller: %s", e)
        else:
            _log.info("vgamepad not installed (pip install vgamepad)")

    def _load_mapping(self):
        if MAPPING_FILE.exists():
            try:
                with open(MAPPING_FILE, encoding="utf-8") as f:
                    data = json.load(f)
                _log.info("Gamepad mapping loaded: %s", data.get("name", "unknown"))
                return data.get("buttons", {})
            except Exception:
                pass
        return {}

    def _get_xbox_button(self, action):
        """Get Xbox button constant from action name using PS4-to-Xbox mapping."""
        ps4_id = self._mapping.get(action)
        if ps4_id is None:
            return None

        PS4_TO_XBOX = {
            0: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,              # PS4 X
            1: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,              # PS4 O
            2: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,              # PS4 Square
            3: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,              # PS4 Triangle
            4: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,  # PS4 L1
            5: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER, # PS4 R1
            8: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,           # PS4 Share
            9: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,          # PS4 Options
            10: vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,         # PS4 PS
            11: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,    # PS4 L3
            12: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,   # PS4 R3
            13: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,       # PS4 D-pad Up
            14: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,     # PS4 D-pad Down
            15: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,     # PS4 D-pad Left
            16: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,    # PS4 D-pad Right
        }
        return PS4_TO_XBOX.get(ps4_id)

    def press(self, action, duration=0.05):
        """Нажать и отпустить кнопку по действию."""
        if not self.enabled or not self._gamepad:
            return

        try:
            xbox_btn = self._get_xbox_button(action)
            if xbox_btn is not None:
                self._gamepad.press_button(button=xbox_btn)
                self._gamepad.update()
                time.sleep(duration)
                self._gamepad.release_button(button=xbox_btn)
                self._gamepad.update()
            elif action == "hp_flask":
                self._gamepad.left_trigger(value=255)
                self._gamepad.update()
                time.sleep(duration)
                self._gamepad.left_trigger(value=0)
                self._gamepad.update()
            elif action == "mana_flask":
                self._gamepad.right_trigger(value=255)
                self._gamepad.update()
                time.sleep(duration)
                self._gamepad.right_trigger(value=0)
                self._gamepad.update()
        except Exception as e:
            _log.debug("Press error %s: %s", action, e)

    def pickup(self):
        self.press("pickup", duration=0.03)

    def use_hp_flask(self):
        self.press("hp_flask", duration=0.05)

    def use_mana_flask(self):
        self.press("mana_flask", duration=0.05)

    def dodge(self):
        self.press("dodge", duration=0.03)

    def skill(self, slot):
        self.press(f"skill_{slot}", duration=0.03)

    def reset(self):
        if self._gamepad:
            try:
                self._gamepad.reset()
                self._gamepad.update()
            except Exception:
                pass
