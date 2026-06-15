"""Хелперы для разбора строковых хоткеев из конфига в объекты pynput и их сравнения.

Поддержка комбинаций: "ctrl+space", "alt+f8", "shift+q" и т.д.
"""
from pynput import keyboard


def parse_key(spec):
    """'f8' -> Key.f8, 'space' -> Key.space, 'q' -> KeyCode('q'), 'ctrl+space' -> (Key.ctrl_l, Key.space)."""
    s = str(spec).lower()
    if "+" in s:
        parts = [parse_key(p.strip()) for p in s.split("+")]
        return tuple(parts)
    special = getattr(keyboard.Key, s, None)
    if special is not None:
        return special
    return keyboard.KeyCode.from_char(s)


def _is_modifier(key):
    """True если клавиша — модификатор (ctrl, alt, shift, win)."""
    return key in (
        keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
        keyboard.Key.alt_l, keyboard.Key.alt_r,
        keyboard.Key.shift, keyboard.Key.shift_r,
        keyboard.Key.cmd, keyboard.Key.cmd_r,
    )


class ComboTracker:
    """Отслеживает зажатые модификаторы для проверки комбинаций."""

    def __init__(self):
        self._pressed = set()

    def on_press(self, key):
        self._pressed.add(key)

    def on_release(self, key):
        self._pressed.discard(key)

    def check(self, combo):
        """Проверить, что все клавиши комбинации зажаты одновременно."""
        if not isinstance(combo, tuple):
            return False
        return all(k in self._pressed for k in combo)


def key_matches(event_key, target):
    """Совпадает ли клавиша из listener (Key/KeyCode) с распарсенным target."""
    if isinstance(target, tuple):
        return False
    if isinstance(target, keyboard.Key):
        return event_key == target
    return getattr(event_key, "char", None) == getattr(target, "char", None)
