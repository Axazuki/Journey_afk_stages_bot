"""Window-level interaction: locate the game window, capture it, send taps.

Knows nothing about game logic. Re-reads the window rect on every action so
that a window that moved between frames still gets the click.
"""
from __future__ import annotations

import mss
import numpy as np
import pydirectinput
import pygetwindow as gw


class WindowAgent:
    def __init__(self, window_title: str) -> None:
        self._title = window_title
        self._window: gw.Window | None = None

    def attach(self) -> None:
        candidates = gw.getWindowsWithTitle(self._title)
        if not candidates:
            raise RuntimeError(f"window not found: {self._title!r}")
        exact = [w for w in candidates if w.title == self._title]
        self._window = exact[0] if exact else candidates[0]

    def get_rect(self) -> tuple[int, int, int, int]:
        if self._window is None:
            raise RuntimeError("call attach() first")
        return (
            int(self._window.left),
            int(self._window.top),
            int(self._window.width),
            int(self._window.height),
        )

    def screenshot(self) -> np.ndarray:
        x, y, w, h = self.get_rect()
        with mss.mss() as sct:
            raw = sct.grab({"left": x, "top": y, "width": w, "height": h})
        return np.array(raw)[:, :, :3]

    def tap_abs(self, x: int, y: int) -> None:
        pydirectinput.click(x, y)

    def tap_rel(self, x: int, y: int) -> None:
        rx, ry, _, _ = self.get_rect()
        pydirectinput.click(rx + x, ry + y)

    def tap_normalized(self, nx: float, ny: float) -> None:
        rx, ry, w, h = self.get_rect()
        pydirectinput.click(rx + int(nx * w), ry + int(ny * h))
