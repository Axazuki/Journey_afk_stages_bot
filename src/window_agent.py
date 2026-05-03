"""Window-level interaction: locate the game window, capture it, send taps.

Knows nothing about game logic.
"""
from __future__ import annotations

import numpy as np


class WindowAgent:
    def __init__(self, window_title: str) -> None:
        self._title = window_title

    def attach(self) -> None:
        raise NotImplementedError

    def get_rect(self) -> tuple[int, int, int, int]:
        raise NotImplementedError

    def screenshot(self) -> np.ndarray:
        raise NotImplementedError

    def tap_abs(self, x: int, y: int) -> None:
        raise NotImplementedError

    def tap_rel(self, x: int, y: int) -> None:
        raise NotImplementedError

    def tap_normalized(self, nx: float, ny: float) -> None:
        raise NotImplementedError
