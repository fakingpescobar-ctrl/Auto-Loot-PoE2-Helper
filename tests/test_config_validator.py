from src.config_validator import validate


def test_valid_config():
    cfg = {
        "game": {"window_title": "PoE2"},
        "capture": {"backend": "dxcam", "target_fps": 30},
        "filter": {"path": "/tmp/test.filter", "marker_rgb": [255, 0, 200], "categories": ["currency"]},
        "vision": {"min_blob_area": 12},
        "loot": {"pickup_radius_px": 250, "mode": "toggle"},
        "hotkeys": {"toggle": "f8", "pickup": "space", "quit": "f12"},
    }
    warnings = validate(cfg)
    assert warnings == []


def test_missing_section():
    cfg = {"game": {"window_title": "PoE2"}}
    warnings = validate(cfg)
    assert any("capture" in w for w in warnings)


def test_invalid_mode():
    cfg = {
        "game": {"window_title": "PoE2"},
        "capture": {"backend": "dxcam", "target_fps": 30},
        "filter": {"path": "/tmp/t.filter", "marker_rgb": [255, 0, 200], "categories": []},
        "vision": {"min_blob_area": 12},
        "loot": {"pickup_radius_px": 250, "mode": "invalid"},
        "hotkeys": {"toggle": "f8", "pickup": "space", "quit": "f12"},
    }
    warnings = validate(cfg)
    assert any("mode" in w for w in warnings)


def test_bad_marker_rgb():
    cfg = {
        "game": {"window_title": "PoE2"},
        "capture": {"backend": "dxcam", "target_fps": 30},
        "filter": {"path": "/tmp/t.filter", "marker_rgb": [255, 0], "categories": []},
        "vision": {"min_blob_area": 12},
        "loot": {"pickup_radius_px": 250, "mode": "toggle"},
        "hotkeys": {"toggle": "f8", "pickup": "space", "quit": "f12"},
    }
    warnings = validate(cfg)
    assert any("marker_rgb" in w for w in warnings)
