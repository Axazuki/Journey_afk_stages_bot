"""Game logic: linear loop that pushes AFK Stages.

Precondition: bot is launched from the formation editor screen
(the one with btn_records and btn_battle visible). The bot does
not navigate from anywhere else.

One iteration:
    1. tap Records
    2. tap right arrow × current_formation times
    3. tap Copy
    4. tap Battle
    5. wait for btn_battle_win (victory) or btn_retry (defeat)
    6a. victory  → tap btn_battle_win, reset counters,
                   game auto-advances to next stage's formation editor
    6b. defeat   → tap btn_retry, fail_counter += 1
                   if fail_counter exhausted, advance current_formation
                   if all formations exhausted, exit DONE
"""
from __future__ import annotations

import logging
import time
from enum import Enum

import cv2

from .config import Config
from .screen_matcher import Match, ScreenMatcher
from .window_agent import WindowAgent

log = logging.getLogger(__name__)


class ExitReason(Enum):
    DONE = "done"
    STUCK = "stuck"


class StageRunner:
    def __init__(
        self,
        agent: WindowAgent,
        matcher: ScreenMatcher,
        config: Config,
    ) -> None:
        self._agent = agent
        self._matcher = matcher
        self._config = config
        self._current_formation = 0
        self._fail_counter = 0

    def run(self) -> ExitReason:
        timing = self._config.timing
        records_cfg = self._config.records
        strategy = self._config.strategy

        while True:
            log.info(
                "iteration: formation=%d fail_counter=%d",
                self._current_formation, self._fail_counter,
            )

            if not self._tap_when_visible("btn_records", timing.short_wait_sec):
                return self._stuck("btn_records not found on formation screen")

            for i in range(self._current_formation):
                if not self._tap_when_visible(
                    "btn_arrow_right", timing.short_wait_sec
                ):
                    return self._stuck(
                        f"btn_arrow_right not found (arrow #{i + 1})"
                    )
                time.sleep(records_cfg.arrow_settle_sec)

            if not self._tap_when_visible("btn_copy", timing.short_wait_sec):
                return self._stuck("btn_copy not found in records")

            if not self._tap_when_visible("btn_battle", timing.short_wait_sec):
                return self._stuck("btn_battle not found on formation screen")

            outcome = self._matcher.wait_for_any(
                ["btn_battle_win", "btn_retry"],
                self._agent,
                timeout=timing.battle_timeout_sec,
                interval=timing.poll_interval_sec,
            )
            if outcome is None:
                return self._stuck("battle outcome not detected within battle_timeout_sec")

            name, match = outcome

            if name == "btn_battle_win":
                log.info("VICTORY (conf=%.3f)", match.confidence)
                self._tap(match)
                self._fail_counter = 0
                self._current_formation = 0
                continue

            log.info("DEFEAT (conf=%.3f)", match.confidence)
            self._tap(match)
            self._fail_counter += 1

            if self._fail_counter >= strategy.max_failures_per_formation:
                exhausted = self._current_formation
                self._fail_counter = 0
                self._current_formation += 1
                log.info(
                    "formation %d exhausted (%d defeats); switching to formation %d",
                    exhausted,
                    strategy.max_failures_per_formation,
                    self._current_formation,
                )
                if self._current_formation >= strategy.max_formations:
                    log.info(
                        "DONE: %d formations × %d defeats exhausted",
                        strategy.max_formations,
                        strategy.max_failures_per_formation,
                    )
                    return ExitReason.DONE

    def _tap_when_visible(self, name: str, timeout: float) -> bool:
        m = self._matcher.wait_for(
            name,
            self._agent,
            timeout=timeout,
            interval=self._config.timing.poll_interval_sec,
        )
        if m is None:
            return False
        log.debug("tap %s @ (%d,%d) conf=%.3f", name, m.x, m.y, m.confidence)
        self._tap(m)
        return True

    def _tap(self, m: Match) -> None:
        self._agent.tap_abs(m.x, m.y)

    def _stuck(self, reason: str) -> ExitReason:
        log.error("STUCK: %s", reason)
        try:
            self._config.paths.debug_dir.mkdir(parents=True, exist_ok=True)
            out = self._config.paths.debug_dir / f"stuck_{int(time.time())}.png"
            cv2.imwrite(str(out), self._agent.screenshot())
            log.error("dumped last screen to %s", out)
        except Exception as e:
            log.error("failed to dump stuck screenshot: %s", e)
        return ExitReason.STUCK
