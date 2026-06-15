"""Эмуляция джойстика через виртуальный Xbox контроллер.

Позволяет боту нажимать кнопки джойстика (X, L2 и т.д.)
без реального джойстика.

Требует: vgamepad (pip install vgamepad)
Для PoE2: X=подбор, L2=HP фласка, R2=MP фласка
"""
import logging
import time

_log = logging.getLogger("autoloot.gamepad")

try:
    import vgamepad as vg
    HAS_VGAMEPAD = True
except ImportError:
    HAS_VGAMEPAD = False


# PoE2 кнопки (PS4 layout)
class Button:
    X = "cross"           # подбор лута
    CIRCLE = "circle"
    SQUARE = "square"
    TRIANGLE = "triangle"
    L1 = "left_shoulder"
    R1 = "right_shoulder"
    L2 = "left_trigger"   # HP фласка
    R2 = "right_trigger"  # MP фласка
    DPAD_UP = "up"
    DPAD_DOWN = "down"
    DPAD_LEFT = "left"
    DPAD_RIGHT = "right"
    OPTIONS = "options"
    SHARE = "share"


class GamepadEmulator:
    """Эмуляция Xbox контроллера для PoE2."""

    def __init__(self):
        self._gamepad = None
        self.enabled = False

        if HAS_VGAMEPAD:
            try:
                self._gamepad = vg.VX360Gamepad()
                self.enabled = True
                _log.info("Виртуальный Xbox контроллер создан")
            except Exception as e:
                _log.warning("Не удалось создать контроллер: %s", e)
        else:
            _log.info("vgamepad не установлен (pip install vgamepad)")

    def press(self, button, duration=0.05):
        """Нажать и отпустить кнопку."""
        if not self.enabled or not self._gamepad:
            return

        try:
            self._set_button(button, True)
            self._gamepad.update()
            time.sleep(duration)
            self._set_button(button, False)
            self._gamepad.update()
        except Exception as e:
            _log.debug("Ошибка нажатия %s: %s", button, e)

    def hold(self, button):
        """Зажать кнопку."""
        if not self.enabled or not self._gamepad:
            return
        try:
            self._set_button(button, True)
            self._gamepad.update()
        except Exception:
            pass

    def release(self, button):
        """Отпустить кнопку."""
        if not self.enabled or not self._gamepad:
            return
        try:
            self._set_button(button, False)
            self._gamepad.update()
        except Exception:
            pass

    def pickup(self):
        """Подобрать лут (X/Cross)."""
        self.press(Button.X, duration=0.03)

    def use_hp_flask(self):
        """Использовать HP фласку (L2)."""
        self.press(Button.L2, duration=0.05)

    def use_mana_flask(self):
        """Использовать MP фласку (R2)."""
        self.press(Button.R2, duration=0.05)

    def dodge(self):
        """Уклонение (Circle)."""
        self.press(Button.CIRCLE, duration=0.03)

    def skill(self, slot):
        """Использовать скилл по слоту (1-4)."""
        btn = {1: Button.SQUARE, 2: Button.TRIANGLE,
               3: Button.L1, 4: Button.R1}.get(slot)
        if btn:
            self.press(btn, duration=0.03)

    def _set_button(self, button, pressed):
        """Установить состояние кнопки."""
        if not self._gamepad:
            return

        btn_map = {
            Button.X: vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            Button.CIRCLE: vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            Button.SQUARE: vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            Button.TRIANGLE: vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            Button.L1: vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            Button.R1: vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            Button.L2: None,  # axis, not button
            Button.R2: None,  # axis, not button
            Button.DPAD_UP: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
            Button.DPAD_DOWN: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
            Button.DPAD_LEFT: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
            Button.DPAD_RIGHT: vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
            Button.OPTIONS: vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            Button.SHARE: vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
        }

        btn = btn_map.get(button)
        if btn is not None:
            if pressed:
                self._gamepad.press_button(button=btn)
            else:
                self._gamepad.release_button(button=btn)
        elif button == Button.L2:
            self._gamepad.left_trigger(value=255 if pressed else 0)
        elif button == Button.R2:
            self._gamepad.right_trigger(value=255 if pressed else 0)

    def reset(self):
        """Сбросить все кнопки."""
        if self._gamepad:
            try:
                self._gamepad.reset()
                self._gamepad.update()
            except Exception:
                pass
