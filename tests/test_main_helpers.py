import threading

from src.config_manager import load_config
from src.main import Status, State, build_detector, detector_colors


def test_detector_colors():
    base = load_config(None)
    base["filter"]["scan_colors"] = False  # отключаем авто-сканирование для теста
    base["filter"]["category_colors"] = {}  # изолируем от категорийных цветов
    marker = list(base["filter"]["marker_rgb"])
    assert detector_colors(base) == [marker]
    base["filter"]["extra_colors"] = [[255, 0, 0]]
    assert detector_colors(base) == [marker, [255, 0, 0]]


def test_build_detector_bounds_count():
    base = load_config(None)
    base["filter"]["scan_colors"] = False
    base["filter"]["category_colors"] = {}  # изолируем от категорийных цветов
    base["filter"]["extra_colors"] = [[255, 0, 0]]
    det = build_detector(base)
    assert len(det.bounds) == 2


def test_status_threadsafe():
    s = Status(a=0)

    def writer():
        for i in range(200):
            s.update(a=i)

    t = threading.Thread(target=writer)
    t.start()
    for _ in range(200):
        _ = s.snapshot()
    t.join()
    assert "a" in s.snapshot()


def test_state_threadsafe():
    s = State()

    def toggler():
        for _ in range(100):
            s.toggle_auto()

    def pickuper():
        for _ in range(100):
            s.set_pickup(True)
            s.set_pickup(False)

    t1 = threading.Thread(target=toggler)
    t2 = threading.Thread(target=pickuper)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    auto_on, _ = s.snapshot()
    assert isinstance(auto_on, bool)
