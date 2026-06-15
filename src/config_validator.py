"""Валидация конфига: проверка наличия обязательных полей и типов значений.

Вызывается при загрузке конфига. Логирует предупреждения, не крашит приложение.
"""
import logging

_log = logging.getLogger("autoloot.config")

REQUIRED_SECTIONS = {
    "game": {"window_title": str},
    "capture": {"backend": str, "target_fps": int},
    "filter": {"path": str, "marker_rgb": list, "categories": list},
    "vision": {"min_blob_area": int},
    "loot": {"pickup_radius_px": int, "mode": str},
    "hotkeys": {"toggle": str, "pickup": str, "quit": str},
}

OPTIONAL_TYPES = {
    "game": {},
    "capture": {},
    "filter": {"extra_colors": list, "category_colors": dict},
    "vision": {"hue_tolerance": int, "sat_min": int, "val_min": int, "close_px": int},
    "loot": {
        "click_cooldown_ms": (int, float), "dedup_ms": (int, float),
        "dedup_px": int, "lazy_radius_px": int,
        "randomize_delay_ms": list, "human_mouse": bool,
        "category_priority": dict, "center_offset_xy": list,
    },
    "hotkeys": {"profile": str, "calibrate": str},
    "hp_flask": {"enabled": bool, "key": str, "threshold": (int, float), "cooldown_ms": (int, float)},
    "automation": {"enabled": bool, "only_when_foreground": bool, "actions": list},
    "overlay": {"enabled": bool, "show_radius": bool, "poll_ms": int},
    "logging": {"level": str},
}

VALID_MODES = {"hold", "toggle", "single", "lazy"}
VALID_BACKENDS = {"dxcam", "mss"}


def validate(cfg):
    """Проверить конфиг. Возвращает список строк предупреждений (пустой = всё ок)."""
    warnings = []

    for section, fields in REQUIRED_SECTIONS.items():
        if section not in cfg:
            warnings.append(f"Отсутствует секция '{section}'")
            continue
        for field, ftype in fields.items():
            val = cfg[section].get(field)
            if val is None:
                warnings.append(f"[{section}] Отсутствует обязательное поле '{field}'")
            elif not isinstance(val, ftype):
                warnings.append(f"[{section}.{field}] Ожидается {ftype.__name__}, "
                                f"получено {type(val).__name__}")

    loot = cfg.get("loot", {})
    mode = loot.get("mode")
    if mode and mode not in VALID_MODES:
        warnings.append(f"[loot.mode] Неизвестный режим '{mode}'. Допустимые: {VALID_MODES}")

    backend = cfg.get("capture", {}).get("backend")
    if backend and backend not in VALID_BACKENDS:
        warnings.append(f"[capture.backend] Неизвестный бэкенд '{backend}'. Допустимые: {VALID_BACKENDS}")

    marker = cfg.get("filter", {}).get("marker_rgb", [])
    if marker and (len(marker) != 3 or not all(0 <= c <= 255 for c in marker)):
        warnings.append(f"[filter.marker_rgb] Должен быть [R, G, B] (0-255), получено: {marker}")

    hp_cfg = cfg.get("hp_flask", {})
    if hp_cfg.get("enabled"):
        threshold = hp_cfg.get("threshold", 0.65)
        if not (0.0 < threshold < 1.0):
            warnings.append(f"[hp_flask.threshold] Должен быть 0.0 < threshold < 1.0, "
                            f"получено: {threshold}")

    for section, opt_fields in OPTIONAL_TYPES.items():
        sec_cfg = cfg.get(section, {})
        for field, expected in opt_fields.items():
            val = sec_cfg.get(field)
            if val is not None:
                if isinstance(expected, tuple):
                    if not isinstance(val, expected):
                        names = "/".join(t.__name__ for t in expected)
                        warnings.append(f"[{section}.{field}] Ожидается {names}, "
                                        f"получено {type(val).__name__}")
                elif not isinstance(val, expected):
                    warnings.append(f"[{section}.{field}] Ожидается {expected.__name__}, "
                                    f"получено {type(val).__name__}")

    for w in warnings:
        _log.warning("Конфиг: %s", w)

    return warnings
