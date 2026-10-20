# Desktop Clock Overlay

A lightweight Windows desktop overlay that shows a huge day name with a tiny date and time on your wallpaper. It is written in plain Python with `tkinter` and `ctypes`, so there is nothing heavy to run and no Wallpaper Engine is needed. The window is borderless, transparent and click-through, so your mouse clicks pass straight through to the desktop.

<img src="Preview.png" alt="Preview" width="400">

## Features

- Large full-word day name (or short `MON`, `TUE`, ...) in the Anurati sci-fi font
- Small date and time line in a clean secondary font, split to the left and right edges, centered, or aligned to one side
- Transparent background and click-through window
- Very low memory and CPU use
- Settings live in one file, and the clock reloads itself when you save it
- Quit any time with **Ctrl + Alt + Q**

## Font

The day name uses **Anurati**, designed by **Emmeran Richard**.

- Website: https://www.emmeranrichard.fr
- The font's own readme says it is free to use, including commercially.

The font file is **not included** in this repository. Download it from the designer's website and place `Anurati-Regular.otf` in the same folder as `desktop_clock.pyw`. Please respect the designer's terms and credit him if you share your work.

Anurati has no digits, so the date and time line uses **Bahnschrift**, which comes with Windows 10 and 11.

## Requirements

- Windows 10 or 11
- Python 3.8 or newer from https://www.python.org/downloads (tick **Add python.exe to PATH** and keep **tcl/tk** selected in the installer)

No extra packages are needed.

## Setup

1. Download or clone this repository, for example to `C:\DesktopClock`.
2. Download Anurati and put `Anurati-Regular.otf` in the same folder.
3. Double-click `desktop_clock.pyw`. No console window opens.

The script loads the font from its own folder, so you do not have to install the font in Windows, although installing it is fine too.

## Start with Windows

1. Press `Win + R`, type `shell:startup` and press Enter.
2. Right-click `desktop_clock.pyw` and choose **Create shortcut**.
3. Move that shortcut into the Startup folder that opened.

To stop it starting at login, delete the shortcut from that folder.

## Stopping it

- Press **Ctrl + Alt + Q**
- Or double-click `stop_clock.bat` (this ends every `pythonw.exe` on your PC)
- Or end `pythonw.exe` in Task Manager, under Details

## Settings

All settings are in `clock_settings.py`. Edit the file, press save, and the clock restarts within a second and shows the change. If you save a mistake, the clock ignores it and keeps running, and the error is written to `clock_log.txt`.

| Setting                          | What it does                                                            |
| -------------------------------- | ----------------------------------------------------------------------- |
| `DAY_FONT`                       | Font for the big day name                                               |
| `SMALL_FONT`                     | Font for the date and time line                                         |
| `FULL_DAY_NAMES`                 | `True` for TUESDAY, `False` for TUE                                     |
| `DAY_SIZE_PX`                    | Height of the day text in pixels                                        |
| `SMALL_SIZE_PX`                  | Height of the date and time text in pixels                              |
| `GAP_PX`                         | Space between the day and the date/time line                            |
| `SMALL_LAYOUT`                   | `"split"`, `"center"`, `"left"` or `"right"`                            |
| `SMALL_OFFSET_X`                 | Pushes split text inward from the edges of the day                      |
| `SMALL_SPACING`                  | Adds letter spacing to the small line                                   |
| `SEPARATOR`                      | Text between date and time when not split                               |
| `DATE_OFFSET_X`, `DATE_OFFSET_Y` | Moves the date in pixels (split layout)                                 |
| `TIME_OFFSET_X`, `TIME_OFFSET_Y` | Moves the time in pixels (split layout)                                 |
| `POS_X`, `POS_Y`                 | Position on screen from 0 to 1 (0 is left or top, 1 is right or bottom) |
| `OFFSET_X`, `OFFSET_Y`           | Fine position nudge in pixels                                           |
| `TEXT_COLOR`                     | Text colour, for example `"#FFFFFF"`                                    |
| `GLOW`                           | Adds a soft dark shadow around the day text                             |
| `SHOW_SECONDS`                   | Show seconds in the time                                                |
| `EMBED_IN_DESKTOP`               | Experimental, see below                                                 |

Keep the Y offsets small. The window is only as tall as the text, so a large downward move can cut the text off. Raise `GAP_PX` to put more space between the lines.

## Desktop embedding (experimental)

With `EMBED_IN_DESKTOP = False` (the default), the clock is a normal borderless window. It appears on top when it launches, and other windows cover it as soon as you click them. The Show Desktop button hides it.

With `EMBED_IN_DESKTOP = True`, the script tries to attach the clock to the desktop layer behind your icons and windows. This depends on Windows internals that differ between versions, and on some Windows 11 builds the clock may not appear. If that happens, set it back to `False`.

## Troubleshooting

- **Nothing appears:** open `clock_log.txt` in the same folder and check which fonts and mode were used.
- **The day looks like a plain font:** make sure `Anurati-Regular.otf` is in the same folder, then check `clock_log.txt` for `day font in use`.
- **The file is "in use" and can't be replaced:** run `stop_clock.bat`, or restart the PC. Windows locks installed font files.
- **Text is cut off:** increase `GAP_PX` or reduce the Y offsets.

## How it works

The window is a `tkinter` window with a colour key that Windows treats as fully transparent. Calls through `ctypes` make it click-through and hide it from the taskbar and Alt+Tab. The text is redrawn only when it changes, so it stays light on resources.

## License

The code is released under the MIT License, see `LICENSE`. The Anurati font is not covered by this license and remains the work of its designer.

## Credits

- Anurati font by Emmeran Richard, https://www.emmeranrichard.fr
- Bahnschrift font by Microsoft, bundled with Windows
