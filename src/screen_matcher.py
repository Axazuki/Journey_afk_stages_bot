"""Template matching on captured screenshots. Knows nothing about game logic.

Templates live as PNGs in templates_dir. Each template may have an optional
JSON sidecar with the same stem to override match threshold and restrict the
search region:

    {"threshold": 0.9, "region": {"x": 0.0, "y": 0.0, "w": 1.0, "h": 0.33}}

Region coordinates are normalized to the screenshot ([0..1] in both axes), so
the same sidecar survives resolution changes that keep the same aspect ratio.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .window_agent import WindowAgent


@dataclass(frozen=True)
class Match:
    x: int
    y: int
    confidence: float


@dataclass(frozen=True)
class _TemplateSpec:
    image: np.ndarray
    threshold: float
    region: tuple[float, float, float, float] | None  # nx, ny, nw, nh


class ScreenMatcher:
    def __init__(self, templates_dir: Path, default_threshold: float = 0.85) -> None:
        self._templates_dir = Path(templates_dir)
        self._default_threshold = default_threshold
        self._cache: dict[str, _TemplateSpec] = {}

    def _load(self, name: str) -> _TemplateSpec:
        if name in self._cache:
            return self._cache[name]

        png = self._templates_dir / f"{name}.png"
        if not png.exists():
            raise FileNotFoundError(f"template not found: {png}")
        image = cv2.imread(str(png), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"failed to decode template: {png}")

        threshold = self._default_threshold
        region: tuple[float, float, float, float] | None = None
        sidecar = self._templates_dir / f"{name}.json"
        if sidecar.exists():
            data = json.loads(sidecar.read_text(encoding="utf-8"))
            threshold = float(data.get("threshold", threshold))
            r = data.get("region")
            if r is not None:
                region = (
                    float(r["x"]),
                    float(r["y"]),
                    float(r["w"]),
                    float(r["h"]),
                )

        spec = _TemplateSpec(image=image, threshold=threshold, region=region)
        self._cache[name] = spec
        return spec

    def find(self, name: str, screenshot: np.ndarray) -> Match | None:
        spec = self._load(name)

        haystack = screenshot
        offset_x = offset_y = 0
        if spec.region is not None:
            H, W = screenshot.shape[:2]
            nx, ny, nw, nh = spec.region
            x0, y0 = int(nx * W), int(ny * H)
            x1, y1 = int((nx + nw) * W), int((ny + nh) * H)
            haystack = screenshot[y0:y1, x0:x1]
            offset_x, offset_y = x0, y0

        th, tw = spec.image.shape[:2]
        hh, hw = haystack.shape[:2]
        if th > hh or tw > hw:
            return None

        result = cv2.matchTemplate(haystack, spec.image, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val < spec.threshold:
            return None

        cx = offset_x + max_loc[0] + tw // 2
        cy = offset_y + max_loc[1] + th // 2
        return Match(x=cx, y=cy, confidence=float(max_val))

    def wait_for(
        self,
        name: str,
        agent: WindowAgent,
        timeout: float,
        interval: float = 0.5,
    ) -> Match | None:
        deadline = time.monotonic() + timeout
        while True:
            m = self.find(name, agent.screenshot())
            if m is not None:
                return m
            if time.monotonic() >= deadline:
                return None
            time.sleep(interval)

    def wait_for_any(
        self,
        names: list[str],
        agent: WindowAgent,
        timeout: float,
        interval: float = 0.5,
    ) -> tuple[str, Match] | None:
        deadline = time.monotonic() + timeout
        while True:
            shot = agent.screenshot()
            for name in names:
                m = self.find(name, shot)
                if m is not None:
                    return (name, m)
            if time.monotonic() >= deadline:
                return None
            time.sleep(interval)
