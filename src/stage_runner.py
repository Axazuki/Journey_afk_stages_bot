"""Game logic: state machine for the AFK Stages auto-pusher.

The only place that knows what the bot is trying to accomplish.
"""
from __future__ import annotations

from enum import Enum
from typing import Literal

from .config import Config
from .screen_matcher import ScreenMatcher
from .window_agent import WindowAgent

Mode = Literal["phantimal", "battle"]


class ExitReason(Enum):
    DONE = "done"
    STUCK = "stuck"


class StageRunner:
    def __init__(
        self,
        agent: WindowAgent,
        matcher: ScreenMatcher,
        config: Config,
        mode: Mode,
    ) -> None:
        self._agent = agent
        self._matcher = matcher
        self._config = config
        self._mode = mode

    def run(self) -> ExitReason:
        raise NotImplementedError
