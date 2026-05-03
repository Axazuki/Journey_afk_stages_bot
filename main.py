"""Entry point for the AFK Journey AFK Stages auto-pusher."""
from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import cv2

from src import config as cfg
from src.window_agent import WindowAgent


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AFK Journey AFK Stages auto-pusher")
    p.add_argument("--mode", choices=["phantimal", "battle"])
    p.add_argument("--smoke", action="store_true",
                   help="attach to window, save one screenshot to debug/, exit")
    p.add_argument("--debug", action="store_true")
    p.add_argument("--config", type=Path, default=Path("config.ini"))
    args = p.parse_args()

    if not args.smoke and args.mode is None:
        p.error("--mode is required unless --smoke is set")
    return args


def run_smoke(config: cfg.Config, log: logging.Logger) -> int:
    agent = WindowAgent(config.window.title)
    agent.attach()
    rect = agent.get_rect()
    log.info("attached: rect=%s (x, y, w, h)", rect)

    shot = agent.screenshot()
    log.info("screenshot: shape=%s dtype=%s", shot.shape, shot.dtype)

    config.paths.debug_dir.mkdir(parents=True, exist_ok=True)
    out = config.paths.debug_dir / f"smoke_{int(time.time())}.png"
    cv2.imwrite(str(out), shot)
    log.info("saved %s", out)
    return 0


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    log = logging.getLogger("afkj-bot")

    config = cfg.load(args.config)
    log.info("loaded config from %s", args.config)

    if args.smoke:
        return run_smoke(config, log)

    log.info("mode=%s debug=%s window.title=%r",
             args.mode, args.debug, config.window.title)
    log.warning("StageRunner not yet implemented (Phase 3)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
