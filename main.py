"""Entry point for the AFK Journey AFK Stages auto-pusher."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src import config as cfg


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AFK Journey AFK Stages auto-pusher")
    p.add_argument("--mode", choices=["phantimal", "battle"], required=True)
    p.add_argument("--debug", action="store_true")
    p.add_argument("--config", type=Path, default=Path("config.ini"))
    return p.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    log = logging.getLogger("afkj-bot")

    config = cfg.load(args.config)
    log.info("loaded config from %s", args.config)
    log.info(
        "mode=%s debug=%s window.title=%r",
        args.mode, args.debug, config.window.title,
    )

    log.warning("skeleton build — StageRunner not yet implemented")
    return 0


if __name__ == "__main__":
    sys.exit(main())
