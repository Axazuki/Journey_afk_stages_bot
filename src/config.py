"""Typed loader for config.ini."""
from __future__ import annotations

from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WindowCfg:
    title: str


@dataclass(frozen=True)
class TimingCfg:
    poll_interval_sec: float
    short_wait_sec: float
    long_wait_sec: float
    battle_timeout_sec: float
    stuck_timeout_sec: float


@dataclass(frozen=True)
class RecordsCfg:
    arrow_settle_sec: float


@dataclass(frozen=True)
class StrategyCfg:
    max_failures_per_formation: int
    max_formations: int


@dataclass(frozen=True)
class MatchingCfg:
    default_threshold: float


@dataclass(frozen=True)
class PathsCfg:
    templates_dir: Path
    debug_dir: Path
    log_file: Path


@dataclass(frozen=True)
class Config:
    window: WindowCfg
    timing: TimingCfg
    records: RecordsCfg
    strategy: StrategyCfg
    matching: MatchingCfg
    paths: PathsCfg


def load(path: Path) -> Config:
    cp = ConfigParser()
    read = cp.read(path, encoding="utf-8")
    if not read:
        raise FileNotFoundError(f"config not found: {path}")

    return Config(
        window=WindowCfg(title=cp["window"]["title"]),
        timing=TimingCfg(
            poll_interval_sec=cp.getfloat("timing", "poll_interval_sec"),
            short_wait_sec=cp.getfloat("timing", "short_wait_sec"),
            long_wait_sec=cp.getfloat("timing", "long_wait_sec"),
            battle_timeout_sec=cp.getfloat("timing", "battle_timeout_sec"),
            stuck_timeout_sec=cp.getfloat("timing", "stuck_timeout_sec"),
        ),
        records=RecordsCfg(
            arrow_settle_sec=cp.getfloat("records", "arrow_settle_sec"),
        ),
        strategy=StrategyCfg(
            max_failures_per_formation=cp.getint(
                "strategy", "max_failures_per_formation"
            ),
            max_formations=cp.getint("strategy", "max_formations"),
        ),
        matching=MatchingCfg(
            default_threshold=cp.getfloat("matching", "default_threshold"),
        ),
        paths=PathsCfg(
            templates_dir=Path(cp["paths"]["templates_dir"]),
            debug_dir=Path(cp["paths"]["debug_dir"]),
            log_file=Path(cp["paths"]["log_file"]),
        ),
    )
