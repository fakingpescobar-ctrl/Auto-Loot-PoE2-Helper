"""Интерактивная калибровка джойстика для PoE2.

Просит нажать конкретные кнопки и сохраняет раскладку.
"""
import json
import sys
import time
from pathlib import Path

try:
    import pygame
    pygame.init()
    pygame.joystick.init()
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False

MAPPINGS_DIR = Path(__file__).resolve().parents[1] / "config" / "gamepad"

ACTIONS = [
    ("pickup", "Подбор лута (поднять вещь с земли)"),
    ("hp_flask", "Выпить бутылку HP"),
    ("mana_flask", "Выпить бутылку манны"),
    ("dodge", "Уклонение / рывок"),
    ("skill_1", "Скилл 1 (первый слот)"),
    ("skill_2", "Скилл 2 (второй слот)"),
    ("skill_3", "Скилл 3 (третий слот)"),
    ("skill_4", "Скилл 4 (четвёртый слот)"),
]


def calibrate():
    if not HAS_PYGAME:
        print("Установи pygame: pip install pygame")
        return

    count = pygame.joystick.get_count()
    if count == 0:
        print("Джойстик не обнаружен. Подключи и попробуй снова.")
        return

    js = pygame.joystick.Joystick(0)
    js.init()
    print(f"Джойстик: {js.get_name()}")
    print(f"Кнопок: {js.get_numbuttons()}, Оси: {js.get_numaxes()}")
    print()

    mapping = {"name": js.get_name(), "buttons": {}}

    for action, prompt in ACTIONS:
        print(f"{'='*50}")
        print(f"  Нажми кнопку для: {prompt}")
        print(f"  (для отмены нажми Options/Start)")
        print(f"{'='*50}")

        button = wait_for_button(js)
        if button is None:
            print("  Отмена.\n")
            continue

        mapping["buttons"][action] = button
        print(f"  -> Button {button}: {get_button_name(js, button)}\n")

    print(f"\n{'='*50}")
    print("Результат калибровки:")
    print(f"{'='*50}")
    for action, btn in mapping["buttons"].items():
        print(f"  {action:15s} -> Button {btn}: {get_button_name(js, btn)}")

    save = input("\nСохранить? (y/n): ").strip().lower()
    if save == "y":
        save_mapping(mapping)
        print("Сохранено в config/gamepad/mapping.json")
    else:
        print("Не сохранено.")


def wait_for_button(js, timeout=None):
    """Ждать нажатия кнопки. Возвращает номер кнопки или None."""
    start = time.time()
    prev_state = [js.get_button(i) for i in range(js.get_numbuttons())]

    while True:
        if timeout and time.time() - start > timeout:
            return None

        pygame.event.pump()

        for i in range(js.get_numbuttons()):
            current = js.get_button(i)
            if current and not prev_state[i]:
                prev_state[i] = current
                time.sleep(0.15)
                return i
            prev_state[i] = current

        if any(js.get_button(i) for i in [9, 10]):
            return None

        time.sleep(0.01)


def get_button_name(js, btn_id):
    """Получить имя кнопки по номеру."""
    name = js.get_name().lower()
    if "ps" in name or "dualshock" in name or "dualsense" in name:
        ps_map = {0: "X", 1: "O", 2: "Square", 3: "Triangle",
                  4: "L1", 5: "R1", 6: "L2", 7: "R2",
                  8: "Share", 9: "Options", 10: "PS",
                  11: "L3", 12: "R3",
                  13: "D-pad Up", 14: "D-pad Down",
                  15: "D-pad Left", 16: "D-pad Right"}
        return ps_map.get(btn_id, f"Button {btn_id}")
    else:
        xbox_map = {0: "A", 1: "B", 2: "X", 3: "Y",
                    4: "LB", 5: "RB", 6: "Back", 7: "Start",
                    8: "Xbox", 9: "Left Stick", 10: "Right Stick",
                    11: "D-pad Up", 12: "D-pad Down",
                    13: "D-pad Left", 14: "D-pad Right"}
        return xbox_map.get(btn_id, f"Button {btn_id}")


def save_mapping(mapping):
    MAPPINGS_DIR.mkdir(parents=True, exist_ok=True)
    path = MAPPINGS_DIR / "mapping.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)


def load_mapping():
    path = MAPPINGS_DIR / "mapping.json"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return None


def main():
    calibrate()


if __name__ == "__main__":
    main()
