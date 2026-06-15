"""Парсер входов джойстика/геймпада.

Определяет подключённый джойстик и логирует нажатия кнопок.
Для PoE2 с джойстиком: L2=HP фласка, X=подбор лута и т.д.

Запуск:
    python -m src.tools.gamepad_test
"""
import sys
import time

try:
    import pygame
    pygame.init()
    pygame.joystick.init()
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


BUTTON_MAP_PS4 = {
    0: "X (Cross)",
    1: "O (Circle)",
    2: "Square",
    3: "Triangle",
    4: "L1",
    5: "R1",
    6: "L2",
    7: "R2",
    8: "Share",
    9: "Options",
    10: "PS",
    11: "L3 (stick press)",
    12: "R3 (stick press)",
    13: "D-pad Up",
    14: "D-pad Down",
    15: "D-pad Left",
    16: "D-pad Right",
}

BUTTON_MAP_XBOX = {
    0: "A",
    1: "B",
    2: "X",
    3: "Y",
    4: "LB",
    5: "RB",
    6: "Back/Select",
    7: "Start",
    8: "Xbox button",
    9: "Left stick press",
    10: "Right stick press",
    11: "D-pad Up",
    12: "D-pad Down",
    13: "D-pad Left",
    14: "D-pad Right",
}

# PoE2 controller actions (по умолчанию)
POE2_ACTIONS = {
    "X (Cross)": "pickup",       # подбор лута
    "L2": "hp_flask",            # выпить HP
    "R2": "mana_flask",          # выпить MP
    "Square": "skill_1",
    "Triangle": "skill_2",
    "O (Circle)": "dodge",
    "L1": "skill_3",
    "R1": "skill_4",
}


def detect_joystick():
    """Определить подключённый джойстик."""
    if not HAS_PYGAME:
        print("pygame не установлен. pip install pygame")
        return None

    count = pygame.joystick.get_count()
    if count == 0:
        print("Джойстик не обнаружен.")
        return None

    js = pygame.joystick.Joystick(0)
    js.init()
    print(f"Джойстик: {js.get_name()}")
    print(f"Кнопок: {js.get_numbuttons()}")
    print(f"Оси: {js.get_numaxes()}")
    print(f"Поводки: {js.get_numhats()}")
    return js


def get_button_map(js):
    """Определить тип кнопок (PS4/Xbox/другой)."""
    name = js.get_name().lower()
    if "ps" in name or "dualshock" in name or "dualsense" in name:
        return BUTTON_MAP_PS4
    elif "xbox" in name or "xinput" in name:
        return BUTTON_MAP_XBOX
    else:
        return {i: f"Button {i}" for i in range(js.get_numbuttons())}


def log_inputs(duration=30):
    """Логировать входы джойстика."""
    js = detect_joystick()
    if not js:
        return

    btn_map = get_button_map(js)
    print(f"\nТип кнопок: {'PS4' if btn_map == BUTTON_MAP_PS4 else 'Xbox' if btn_map == BUTTON_MAP_XBOX else 'Generic'}")
    print(f"Логирую {duration} секунд. Нажимай кнопки...\n")

    start = time.time()
    log = []

    while time.time() - start < duration:
        pygame.event.pump()

        for i in range(js.get_numbuttons()):
            if js.get_button(i):
                name = btn_map.get(i, f"Btn{i}")
                action = POE2_ACTIONS.get(name, "???")
                entry = f"[{time.time()-start:.1f}s] Button {i}: {name} -> {action}"
                print(entry)
                log.append(entry)
                time.sleep(0.2)

        for i in range(js.get_numaxes()):
            val = js.get_axis(i)
            if abs(val) > 0.5:
                direction = "+" if val > 0 else "-"
                print(f"[{time.time()-start:.1f}s] Axis {i}: {val:.2f} ({direction})")

        time.sleep(0.01)

    print(f"\n--- Лог ({len(log)} нажатий) ---")
    for entry in log:
        print(entry)

    print("\n--- Маппинг для PoE2 ---")
    for name, action in POE2_ACTIONS.items():
        print(f"  {name:20s} -> {action}")


def main():
    if not HAS_PYGAME:
        print("Установи pygame: pip install pygame")
        return
    log_inputs(duration=30)


if __name__ == "__main__":
    main()
