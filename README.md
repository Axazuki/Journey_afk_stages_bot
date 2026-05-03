# AFK Journey AFK Stages auto-pusher

Console utility that automatically pushes AFK Stages in the native Windows AFK Journey client by reusing other players' formations from Records. See `TZ_afkj_bot.md` for the full spec.

## Usage (Windows)

1. Launch AFK Journey, switch to **borderless windowed** mode at the resolution the templates were captured for.
2. Navigate to the **AFK Stages** screen with Battle / Phantimal Challenge tabs visible.
3. Run one of:
   - Double-click `run-phantimal.bat` or `run-battle.bat` (window stays open after exit so you can read the log).
   - Double-click `run-smoke.bat` to verify the bot can find the game window — it just attaches, screenshots once into `debug/`, and exits.
   - Or from a terminal in the unzipped folder:

     ```
     .\afkj-bot.exe --mode {phantimal|battle} [--debug]
     .\afkj-bot.exe --smoke
     ```

> Display scaling other than 100% (Settings → System → Display → Scale) can offset window coordinates. If `--smoke` saves a screenshot that's clipped or shifted, set scale to 100% and retry.

## Build

The Windows `.exe` is produced by the **Build Windows EXE** GitHub Action on every push to `develop` (and `main`, once it has commits). Open the latest run, download the `afkj-bot-win` artifact, unzip it on Windows. Run `afkj-bot.exe` from the unzipped folder — `config.ini` and `templates/` must sit alongside it.

## Templates

`templates/` must contain PNG crops captured from the live game in the target resolution. See §9 of the TZ for the list of required filenames.

Workflow:

1. In the running game, press `Win+Shift+S` and crop the UI element.
2. Save the PNG into `templates/` with the exact name from §9.
3. Optionally drop a `<name>.json` sidecar next to it to override match threshold or restrict the search region.
