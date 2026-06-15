"""Полноценное GUI приложение Auto Loot PoE2 Helper (PyQt5).

Вкладки:
  Dashboard  — статус в реальном времени
  Profiles   — управление профилями
  Settings   — все настройки
  Stats      — статистика сессии
  Logs       — логи в реальном времени
"""
from __future__ import annotations

import sys
import threading
import time
from pathlib import Path

try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QGroupBox, QFormLayout, QComboBox, QSpinBox,
        QDoubleSpinBox, QCheckBox, QTextEdit, QTableWidget, QTableWidgetItem,
        QHeaderView, QSplitter, QFrame, QProgressBar, QSlider, QLineEdit,
        QMessageBox, QFileDialog, QSystemTrayIcon, QMenu, QAction,
    )
    from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
    from PyQt5.QtGui import QFont, QColor, QIcon, QPalette
    HAS_PYQT5 = True
except ImportError:
    HAS_PYQT5 = False

from ..config_manager import load_config, DEFAULT_PATH
from ..core.profiles import ProfileManager, PROFILES_DIR


# === Стиль ===
DARK_STYLE = """
QMainWindow { background: #1a1a2e; }
QTabWidget::pane { border: 1px solid #2a2a4a; background: #16213e; }
QTabBar::tab { background: #0f3460; color: #9fb3c8; padding: 10px 20px;
               border: 1px solid #2a2a4a; border-bottom: none; border-radius: 4px 4px 0 0; }
QTabBar::tab:selected { background: #16213e; color: #00ff88; }
QTabBar::tab:hover { background: #1a1a4e; }
QGroupBox { border: 1px solid #2a2a4a; border-radius: 6px; margin-top: 10px;
            padding-top: 15px; color: #e0e0e0; font-weight: bold; }
QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
QLabel { color: #e0e0e0; }
QLabel#header { color: #00ff88; font-size: 18px; font-weight: bold; }
QLabel#status-on { color: #00ff88; font-size: 14px; font-weight: bold; }
QLabel#status-off { color: #ff4444; font-size: 14px; font-weight: bold; }
QPushButton { background: #0f3460; color: #e0e0e0; border: 1px solid #2a2a4a;
              padding: 8px 16px; border-radius: 4px; }
QPushButton:hover { background: #1a1a4e; }
QPushButton:pressed { background: #00ff88; color: #000; }
QPushButton#danger { background: #8b0000; }
QPushButton#danger:hover { background: #a00000; }
QPushButton#success { background: #006400; }
QPushButton#success:hover { background: #008000; }
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox { background: #0f3460; color: #e0e0e0;
    border: 1px solid #2a2a4a; padding: 5px; border-radius: 3px; }
QTextEdit { background: #0a0a1a; color: #00ff88; font-family: Consolas; border: 1px solid #2a2a4a; }
QTableWidget { background: #0f3460; color: #e0e0e0; gridline-color: #2a2a4a; }
QHeaderView::section { background: #16213e; color: #00ff88; padding: 5px; border: 1px solid #2a2a4a; }
QProgressBar { border: 1px solid #2a2a4a; border-radius: 4px; text-align: center; color: #000; }
QProgressBar::chunk { background: #00ff88; border-radius: 3px; }
QCheckBox { color: #e0e0e0; }
QCheckBox::indicator { width: 16px; height: 16px; }
QSlider::groove:horizontal { background: #2a2a4a; height: 6px; border-radius: 3px; }
QSlider::handle:horizontal { background: #00ff88; width: 16px; margin: -5px 0; border-radius: 8px; }
"""


class Signals(QObject):
    """Сигналы для обновления GUI из потоков."""
    status_update = pyqtSignal(dict)
    log_message = pyqtSignal(str)


class DashboardTab(QWidget):
    """Главная вкладка: статус в реальном времени."""

    def __init__(self, signals: Signals):
        super().__init__()
        self.signals = signals
        self._setup_ui()
        self.signals.status_update.connect(self._update_status)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("AUTO LOOT POE2 HELPER")
        header.setObjectName("header")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)

        self.status_label = QLabel("OFF")
        self.status_label.setObjectName("status-off")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)

        stats_group = QGroupBox("Статистика")
        stats_layout = QFormLayout()

        self.mode_label = QLabel("-")
        self.profile_label = QLabel("default")
        self.targets_label = QLabel("0")
        self.radius_label = QLabel("0")
        self.picked_label = QLabel("0")
        self.session_label = QLabel("-")
        self.hp_label = QLabel("-")
        self.cat_label = QLabel("all")

        stats_layout.addRow("Режим:", self.mode_label)
        stats_layout.addRow("Профиль:", self.profile_label)
        stats_layout.addRow("Целей:", self.targets_label)
        stats_layout.addRow("В радиусе:", self.radius_label)
        stats_layout.addRow("Подобрано:", self.picked_label)
        stats_layout.addRow("Категория:", self.cat_label)
        stats_layout.addRow("Сессия:", self.session_label)
        stats_layout.addRow("HP:", self.hp_label)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        btn_layout = QHBoxLayout()
        self.toggle_btn = QPushButton("START (F8)")
        self.toggle_btn.setObjectName("success")
        self.toggle_btn.clicked.connect(self._toggle)
        btn_layout.addWidget(self.toggle_btn)

        self.reload_btn = QPushButton("Reload (F5)")
        self.reload_btn.clicked.connect(self._reload)
        btn_layout.addWidget(self.reload_btn)

        layout.addLayout(btn_layout)
        layout.addStretch()

    def _update_status(self, data: dict):
        active = data.get("active", False)
        self.status_label.setText("ACTIVE" if active else "IDLE")
        self.status_label.setObjectName("status-on" if active else "status-off")
        self.status_label.setStyleSheet("")

        self.mode_label.setText(data.get("mode", "-"))
        self.profile_label.setText(data.get("profile", "default"))
        self.targets_label.setText(str(data.get("targets", 0)))
        self.radius_label.setText(str(data.get("in_radius", 0)))
        self.picked_label.setText(str(data.get("picked", 0)))
        self.cat_label.setText(data.get("active_cat", "all"))
        self.session_label.setText(data.get("session_stats", "-"))
        hp = data.get("hp")
        self.hp_label.setText(f"{hp}%" if hp is not None else "-")

    def _toggle(self):
        from pynput.keyboard import Controller
        kb = Controller()
        from ..input.keyboard import parse_key
        k = parse_key("f8")
        kb.press(k)
        kb.release(k)

    def _reload(self):
        from pynput.keyboard import Controller
        kb = Controller()
        from ..input.keyboard import parse_key
        k = parse_key("f5")
        kb.press(k)
        kb.release(k)


class ProfilesTab(QWidget):
    """Управление профилями."""

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("Профили")
        header.setObjectName("header")
        layout.addWidget(header)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Имя", "Режим", "Радиус", "Файл"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self._refresh)
        btn_layout.addWidget(refresh_btn)

        delete_btn = QPushButton("Удалить")
        delete_btn.setObjectName("danger")
        delete_btn.clicked.connect(self._delete)
        btn_layout.addWidget(delete_btn)
        layout.addLayout(btn_layout)

    def _refresh(self):
        pm = ProfileManager()
        self.table.setRowCount(len(pm.names))
        for i, name in enumerate(pm.names):
            cfg = pm.load(name)
            loot = cfg.get("loot", {})
            self.table.setItem(i, 0, QTableWidgetItem(name))
            self.table.setItem(i, 1, QTableWidgetItem(loot.get("mode", "-")))
            self.table.setItem(i, 2, QTableWidgetItem(str(loot.get("pickup_radius_px", "-"))))
            path = PROFILES_DIR / f"{name}.yaml" if name != "default" else "default.yaml"
            self.table.setItem(i, 3, QTableWidgetItem(str(path)))

    def _delete(self):
        row = self.table.currentRow()
        if row < 0:
            return
        name = self.table.item(row, 0).text()
        if name == "default":
            QMessageBox.warning(self, "Ошибка", "Нельзя удалить default профиль.")
            return
        reply = QMessageBox.question(self, "Удалить", f"Удалить профиль '{name}'?")
        if reply == QMessageBox.Yes:
            path = PROFILES_DIR / f"{name}.yaml"
            if path.exists():
                path.unlink()
            self._refresh()


class SettingsTab(QWidget):
    """Настройки всех модулей."""

    def __init__(self):
        super().__init__()
        self._values = {}
        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("Настройки")
        header.setObjectName("header")
        layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        form = QFormLayout(container)

        self._add_spin(form, "Target FPS", "capture.target_fps", 30, 1, 120)
        self._add_check(form, "Double Buffer", "capture.double_buffer", True)

        self._add_spin(form, "Min Blob Area", "vision.min_blob_area", 120, 1, 5000)
        self._add_spin(form, "Hue Tolerance", "vision.hue_tolerance", 8, 1, 50)
        self._add_spin(form, "Sat Min", "vision.sat_min", 120, 0, 255)
        self._add_spin(form, "Val Min", "vision.val_min", 120, 0, 255)
        self._add_spin(form, "Close Px", "vision.close_px", 3, 0, 30)
        self._add_check(form, "Auto Calibrate", "vision.auto_calibrate", False)

        self._add_spin(form, "Radius Px", "loot.pickup_radius_px", 250, 50, 2000)
        self._add_spin(form, "Cooldown Ms", "loot.click_cooldown_ms", 300, 10, 2000)
        self._add_spin(form, "Dedup Ms", "loot.dedup_ms", 2500, 0, 10000)
        self._add_spin(form, "Lazy Radius", "loot.lazy_radius_px", 80, 10, 500)
        self._add_combo(form, "Mode", "loot.mode", "toggle", ["hold", "toggle", "single", "lazy"])

        self._add_check(form, "HP Flask", "hp_flask.enabled", True)
        self._add_entry(form, "HP Key", "hp_flask.key", "1")
        self._add_spin(form, "HP Threshold", "hp_flask.threshold", 0.65, 0.1, 1.0, 0.05)
        self._add_spin(form, "HP Cooldown Ms", "hp_flask.cooldown_ms", 4500, 500, 15000)
        self._add_check(form, "Sound", "hp_flask.sound", True)

        self._add_check(form, "Overlay", "overlay.enabled", True)
        self._add_check(form, "Tray Icon", "overlay.tray_icon", True)

        scroll.setWidget(container)
        layout.addWidget(scroll)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Применить")
        save_btn.setObjectName("success")
        save_btn.clicked.connect(self._apply)
        btn_layout.addWidget(save_btn)

        export_btn = QPushButton("Экспорт в YAML")
        export_btn.clicked.connect(self._export)
        btn_layout.addWidget(export_btn)
        layout.addLayout(btn_layout)

    def _add_spin(self, form, label, key, default, from_, to_, step=1):
        var = QSpinBox() if step == 1 else QDoubleSpinBox()
        var.setRange(from_, to_)
        var.setValue(default)
        if step != 1:
            var.setSingleStep(step)
        form.addRow(label, var)
        self._values[key] = var

    def _add_check(self, form, label, key, default):
        var = QCheckBox()
        var.setChecked(default)
        form.addRow(label, var)
        self._values[key] = var

    def _add_entry(self, form, label, key, default):
        var = QLineEdit(default)
        form.addRow(label, var)
        self._values[key] = var

    def _add_combo(self, form, label, key, default, options):
        var = QComboBox()
        var.addItems(options)
        var.setCurrentText(default)
        form.addRow(label, var)
        self._values[key] = var

    def _load_values(self):
        try:
            cfg = load_config(None)
            for key, widget in self._values.items():
                parts = key.split(".")
                val = cfg
                for p in parts:
                    val = val.get(p, {}) if isinstance(val, dict) else None
                if val is None:
                    continue
                if isinstance(widget, QSpinBox):
                    widget.setValue(int(val))
                elif isinstance(widget, QDoubleSpinBox):
                    widget.setValue(float(val))
                elif isinstance(widget, QCheckBox):
                    widget.setChecked(bool(val))
                elif isinstance(widget, QLineEdit):
                    widget.setText(str(val))
                elif isinstance(widget, QComboBox):
                    widget.setCurrentText(str(val))
        except Exception:
            pass

    def _collect(self) -> dict:
        cfg = {}
        for key, widget in self._values.items():
            parts = key.split(".")
            d = cfg
            for p in parts[:-1]:
                d = d.setdefault(p, {})
            if isinstance(widget, QSpinBox):
                d[parts[-1]] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                d[parts[-1]] = widget.value()
            elif isinstance(widget, QCheckBox):
                d[parts[-1]] = widget.isChecked()
            elif isinstance(widget, QLineEdit):
                d[parts[-1]] = widget.text()
            elif isinstance(widget, QComboBox):
                d[parts[-1]] = widget.currentText()
        return cfg

    def _apply(self):
        from pynput.keyboard import Controller
        kb = Controller()
        from ..input.keyboard import parse_key
        k = parse_key("f5")
        kb.press(k)
        kb.release(k)
        QMessageBox.information(self, "OK", "Настройки применены (F5 отправлен).")

    def _export(self):
        cfg = self._collect()
        import yaml
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить профиль", str(PROFILES_DIR), "YAML (*.yaml)")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write("# GUI профиль\n")
                yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)
            QMessageBox.information(self, "OK", f"Сохранено: {path}")


class StatsTab(QWidget):
    """Статистика сессии."""

    def __init__(self, signals: Signals):
        super().__init__()
        self.signals = signals
        self._setup_ui()
        self.signals.status_update.connect(self._update)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("Статистика")
        header.setObjectName("header")
        layout.addWidget(header)

        self.total_label = QLabel("0")
        self.ppm_label = QLabel("0")
        self.time_label = QLabel("0сек")

        stats_group = QGroupBox("Текущая сессия")
        stats_layout = QFormLayout()
        stats_layout.addRow("Всего:", self.total_label)
        stats_layout.addRow("Предм/мин:", self.ppm_label)
        stats_layout.addRow("Время:", self.time_label)
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Категория", "Количество", "Доля"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

    def _update(self, data: dict):
        stats = data.get("stats", {})
        total = data.get("picked", 0)
        self.total_label.setText(str(total))

        session = data.get("session_stats", "")
        if "мин" in session:
            parts = session.split()
            self.ppm_label.setText(parts[-1] if parts else "-")
            self.time_label.setText(" ".join(parts[:-1]) if len(parts) > 1 else "-")

        self.table.setRowCount(len(stats))
        for i, (cat, count) in enumerate(sorted(stats.items(), key=lambda x: -x[1])):
            self.table.setItem(i, 0, QTableWidgetItem(cat))
            self.table.setItem(i, 1, QTableWidgetItem(str(count)))
            pct = count / total * 100 if total else 0
            self.table.setItem(i, 2, QTableWidgetItem(f"{pct:.0f}%"))


class LogsTab(QWidget):
    """Логи в реальном времени."""

    def __init__(self, signals: Signals):
        super().__init__()
        self.signals = signals
        self._setup_ui()
        self.signals.log_message.connect(self._append)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        header = QLabel("Логи")
        header.setObjectName("header")
        layout.addWidget(header)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 10))
        layout.addWidget(self.log_text)

        btn_layout = QHBoxLayout()
        clear_btn = QPushButton("Очистить")
        clear_btn.clicked.connect(lambda: self.log_text.clear())
        btn_layout.addWidget(clear_btn)

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _append(self, msg: str):
        self.log_text.append(msg)
        if self.log_text.document().blockCount() > 1000:
            cursor = self.log_text.textCursor()
            cursor.movePosition(cursor.Start)
            cursor.movePosition(cursor.Down, cursor.KeepAnchor, 200)
            cursor.removeSelectedText()

    def _save(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить логи", "autoloot_gui.log")
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.log_text.toPlainText())


class MainWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auto Loot PoE2 Helper")
        self.setMinimumSize(900, 650)

        self.signals = Signals()

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        tabs = QTabWidget()
        tabs.addTab(DashboardTab(self.signals), "Dashboard")
        tabs.addTab(ProfilesTab(), "Profiles")
        tabs.addTab(SettingsTab(), "Settings")
        tabs.addTab(StatsTab(self.signals), "Stats")
        tabs.addTab(LogsTab(self.signals), "Logs")
        layout.addWidget(tabs)

        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._poll)
        self._poll_timer.start(500)

    def _poll(self):
        pass


def run_gui():
    """Запустить GUI приложение."""
    if not HAS_PYQT5:
        print("PyQt5 не установлен. pip install PyQt5")
        return

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_STYLE)
    app.setFont(QFont("Segoe UI", 10))

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    run_gui()
