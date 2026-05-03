"""Template matching on captured screenshots. Knows nothing about game logic."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .window_agent import WindowAgent


@dataclass(frozen=True)
class Match:
    x: int
    y: int
    confidence: float


class ScreenMatcher:
    def __init__(self, templates_dir: Path, default_threshold: float = 0.85) -> None:
        self._templates_dir = templates_dir
        self._default_threshold = default_threshold

    def find(self, name: str, screenshot: np.ndarray) -> Match | None:
        raise NotImplementedError

    def wait_for(
        self,
        name: str,
        agent: WindowAgent,
        timeout: float,
        interval: float = 0.5,
    ) -> Match | None:
        raise NotImplementedError

    def wait_for_any(
        self,
        names: list[str],
        agent: WindowAgent,
        timeout: float,
        interval: float = 0.5,
    ) -> tuple[str, Match] | None:
        raise NotImplementedError
