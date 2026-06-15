"""Прозрачный оверлей с кругом радиуса подбора поверх игры.

Отображает круг радиуса и точку центра персонажа в реальном времени.
Позволяет настраивать радиус перетаскиванием.
"""
from __future__ import annotations

import threading
import time

try:
    import tkinter as tk
    from tkinter import font as tkfont
    HAS_TK = True
except ImportError:
    HAS_TK = False


class RadiusOverlay:
    """Прозрачный оверлей с кругом радиуса."""

    def __init__(self, stop_event, get_state_fn):
        """
        stop_event: threading.Event для остановки
        get_state_fn: callable -> dict с ключами center_x, center_y, radius, active, targets
        """
        self.stop_event = stop_event
        self.get_state = get_state_fn
        self._root = None
        self._canvas = None
        self._radius = 250
        self._dragging = False
        self._drag_start_r = 0
        self._drag_start_y = 0

    def run(self):
        if not HAS_TK:
            return

        self._root = tk.Tk()
        self._root.title("Radius")
        self._root.overrideredirect(True)
        self._root.attributes("-topmost", True)
        self._root.attributes("-alpha", 0.4)
        self._root.config(bg="black")
        self._root.geometry("500x500+100+100")

        try:
            self._root.attributes("-transparentcolor", "black")
        except Exception:
            pass

        self._canvas = tk.Canvas(
            self._root, width=500, height=500,
            bg="black", highlightthickness=0)
        self._canvas.pack()

        self._root.bind("<Button-1>", self._on_press)
        self._root.bind("<B1-Motion>", self._on_drag)
        self._root.bind("<ButtonRelease-1>", self._on_release)
        self._root.bind("<MouseWheel>", self._on_scroll)

        self._update()
        self._root.mainloop()

    def _on_press(self, event):
        self._dragging = True
        self._drag_start_r = self._radius
        self._drag_start_y = event.y_root

    def _on_drag(self, event):
        if self._dragging:
            dy = self._drag_start_y - event.y_root
            self._radius = max(50, min(1500, self._drag_start_r + dy))

    def _on_release(self, event):
        self._dragging = False

    def _on_scroll(self, event):
        if event.delta > 0:
            self._radius = min(1500, self._radius + 10)
        else:
            self._radius = max(50, self._radius - 10)

    def _update(self):
        if self.stop_event.is_set():
            self._root.destroy()
            return

        state = self.get_state()
        self._radius = state.get("radius", self._radius)
        active = state.get("active", False)
        targets = state.get("targets", 0)
        in_radius = state.get("in_radius", 0)

        self._canvas.delete("all")

        cx, cy = 250, 250
        r = self._radius

        color = "#00ff88" if active else "#ff4444"

        self._canvas.create_oval(
            cx - r, cy - r, cx + r, cy + r,
            outline=color, width=2, dash=(6, 4))

        self._canvas.create_oval(
            cx - 4, cy - 4, cx + 4, cy + 4,
            fill=color, outline="")

        self._canvas.create_line(cx - 10, cy, cx + 10, cy, fill=color, width=1)
        self._canvas.create_line(cx, cy - 10, cx, cy + 10, fill=color, width=1)

        f = tkfont.Font(family="Consolas", size=10, weight="bold")
        self._canvas.create_text(
            cx, cy - r - 15,
            text=f"R={self._radius}px",
            fill=color, font=f)
        self._canvas.create_text(
            cx, cy + r + 15,
            text=f"targets:{targets} in:{in_radius}",
            fill=color, font=f)
        self._canvas.create_text(
            cx, cy + r + 30,
            text="drag to resize | scroll to adjust",
            fill="#888888", font=tkfont.Font(family="Consolas", size=8))

        self._root.after(100, self._update)

    def stop(self):
        if self._root:
            try:
                self._root.destroy()
            except Exception:
                pass
