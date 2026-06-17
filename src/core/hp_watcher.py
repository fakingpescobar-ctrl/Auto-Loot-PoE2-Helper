"""Авто-фласка ХП: следит за уровнем жизней и жмёт клавишу при просадке.

Работает независимо от F8 (toggle pickup) — всегда активна пока
программа запущена и окно игры в фокусе.

Поддержка джойстика: если input_method=gamepad, жмёт L2 вместо клавиши.
"""
import time

from pynput.keyboard import Controller

from ..input.keyboard import parse_key
from ..vision.hp_detector import detect_hp_ratio

_WARMUP_SEC = 6.0


def _beep():
    try:
        import winsound
        winsound.Beep(800, 150)
    except Exception:
        pass


class HPWatcher:
    def __init__(self, cfg, log):
        self.enabled = bool(cfg.get("enabled", False))
        self.threshold = float(cfg.get("threshold", 0.65))
        self.cooldown = cfg.get("cooldown_ms", 4500) / 1000.0
        self.region = cfg.get("hp_region", None)
        self.sound = bool(cfg.get("sound", True))
        self.input_method = cfg.get("input_method", "keyboard")
        self._key = parse_key(cfg.get("key", "1"))
        self._kb = Controller()
        self._gamepad = None
        self._log = log
        self._last_press = 0.0
        self._last_ratio = 1.0
        self._max_raw = 0.0         # максимум сырого значения = полный ХП
        self._warmup_until = time.perf_counter() + _WARMUP_SEC
        self._sound_cooldown = 0.0

    def set_gamepad(self, gamepad):
        """Установить эмулятор джойстика."""
        self._gamepad = gamepad

    def check(self, frame_bgr, foreground):
        """Вызывать на каждом кадре из главного цикла."""
        if not self.enabled or not foreground:
            return

        raw = detect_hp_ratio(frame_bgr, self.region)

        # самокалибровка: обновляем максимум (= полный ХП)
        if raw > self._max_raw:
            self._max_raw = raw

        # нормированный HP относительно максимума
        hp = raw / self._max_raw if self._max_raw > 0.01 else 1.0
        self._last_ratio = hp

        # во время прогрева только калибруемся, не нажимаем
        if time.perf_counter() < self._warmup_until:
            return

        now = time.perf_counter()
        if now - self._last_press < self.cooldown:
            return

        if hp < self.threshold:
            if self.input_method == "gamepad" and self._gamepad:
                self._gamepad.use_hp_flask()
            else:
                self._kb.press(self._key)
                self._kb.release(self._key)
            self._last_press = now
            self._log.info("HP flask [%s] (HP ~%.0f%% < %.0f%%)",
                           self.input_method, hp * 100, self.threshold * 100)
            if self.sound and now - self._sound_cooldown > 3.0:
                _beep()
                self._sound_cooldown = now

    @property
    def hp_ratio(self):
        return self._last_ratio


def _key_str(key):
    return getattr(key, "char", None) or str(key).replace("Key.", "")
