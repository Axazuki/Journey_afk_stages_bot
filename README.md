# AFK Journey AFK Stages auto-pusher

Console utility that automatically pushes AFK Stages in the native Windows AFK Journey client by reusing other players' formations from Records. See `TZ_afkj_bot.md` for the full spec.

## Usage (Windows)

1. Launch AFK Journey, switch to **borderless windowed** mode at the resolution the templates were captured for.
2. Navigate to the **AFK Stages** screen with Battle / Phantimal Challenge tabs visible.
3. Run:

   ```
   afkj-bot.exe --mode {phantimal|battle} [--debug]
   ```

## Build

The Windows `.exe` is produced by the **Build Windows EXE** GitHub Action on every push to `main`. Open the latest run, download the `afkj-bot-win` artifact, unzip it on Windows. Run `afkj-bot.exe` from the unzipped folder — `config.ini` and `templates/` must sit alongside it.

## Templates

`templates/` must contain PNG crops captured from the live game in the target resolution. See §9 of the TZ for the list of required filenames.

Workflow:

1. In the running game, press `Win+Shift+S` and crop the UI element.
2. Save the PNG into `templates/` with the exact name from §9.
3. Optionally drop a `<name>.json` sidecar next to it to override match threshold or restrict the search region.
