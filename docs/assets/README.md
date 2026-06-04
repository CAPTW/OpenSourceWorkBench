# Documentation Assets

This directory contains curated documentation assets that are intentionally
tracked.

## Screenshots

- [Dark theme](screenshots/osw_dark.png)
- [Light theme](screenshots/osw_light.png)
- [System theme](screenshots/osw_system.png)

The screenshots are generated with:

```powershell
.\.venv\Scripts\python.exe tools\ui\capture_main_window.py --theme dark --out docs\assets\screenshots\osw_dark.png --offscreen --width 2048 --height 1152
.\.venv\Scripts\python.exe tools\ui\capture_main_window.py --theme light --out docs\assets\screenshots\osw_light.png --offscreen --width 2048 --height 1152
.\.venv\Scripts\python.exe tools\ui\capture_main_window.py --theme system --out docs\assets\screenshots\osw_system.png --offscreen --width 2048 --height 1152
```

Keep documentation screenshots small enough for repository use and review them
before committing.
