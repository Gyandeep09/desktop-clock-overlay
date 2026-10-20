import ctypes
import os
import subprocess
import sys
import time
import traceback
import tkinter as tk
from ctypes import wintypes
from tkinter import font as tkfont

HERE = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(HERE, "clock_log.txt")
SETTINGS_PATH = os.path.join(HERE, "clock_settings.py")
SCRIPT_PATH = os.path.abspath(__file__)

KEY = "#010101"
GLOW_LAYERS = [(6, "#0d1112"), (3, "#1e2528")]
DAYS_SHORT = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
DAYS_FULL = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY", "SATURDAY", "SUNDAY"]
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN",
          "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.windll.gdi32
HWND = ctypes.c_void_p
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, HWND, wintypes.LPARAM)

gdi32.AddFontResourceExW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.c_void_p]
gdi32.AddFontResourceExW.restype = ctypes.c_int
user32.FindWindowW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.FindWindowW.restype = HWND
user32.FindWindowExW.argtypes = [HWND, HWND, wintypes.LPCWSTR, wintypes.LPCWSTR]
user32.FindWindowExW.restype = HWND
user32.GetParent.argtypes = [HWND]
user32.GetParent.restype = HWND
user32.SetParent.argtypes = [HWND, HWND]
user32.SetParent.restype = HWND
user32.SendMessageTimeoutW.argtypes = [HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM,
                                       wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_size_t)]
user32.SetWindowPos.argtypes = [HWND, HWND, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, wintypes.UINT]
user32.SetLayeredWindowAttributes.argtypes = [HWND, wintypes.COLORREF, wintypes.BYTE, wintypes.DWORD]
user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.IsWindowVisible.argtypes = [HWND]

get_long = getattr(user32, "GetWindowLongPtrW", user32.GetWindowLongW)
set_long = getattr(user32, "SetWindowLongPtrW", user32.SetWindowLongW)
get_long.argtypes = [HWND, ctypes.c_int]
get_long.restype = ctypes.c_ssize_t
set_long.argtypes = [HWND, ctypes.c_int, ctypes.c_ssize_t]
set_long.restype = ctypes.c_ssize_t


def log(message):
    with open(LOG_PATH, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def load_settings():
    with open(SETTINGS_PATH, encoding="utf-8") as handle:
        source = handle.read()
    exec(compile(source, SETTINGS_PATH, "exec"), globals())


def files_are_valid():
    try:
        with open(SETTINGS_PATH, encoding="utf-8") as handle:
            exec(compile(handle.read(), SETTINGS_PATH, "exec"), {})
        with open(SCRIPT_PATH, encoding="utf-8") as handle:
            compile(handle.read(), SCRIPT_PATH, "exec")
        return True
    except Exception:
        log("edit rejected, fix the error and save again:\n" + traceback.format_exc())
        return False


def file_stamps():
    try:
        return (os.path.getmtime(SETTINGS_PATH), os.path.getmtime(SCRIPT_PATH))
    except OSError:
        return None


def enable_dpi_awareness():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            user32.SetProcessDPIAware()
        except Exception:
            pass


def load_local_font():
    folders = [
        HERE,
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts"),
    ]
    for folder in folders:
        if not os.path.isdir(folder):
            continue
        for name in os.listdir(folder):
            low = name.lower()
            if low.startswith("anurati") and low.endswith((".otf", ".ttf")):
                path = os.path.join(folder, name)
                count = gdi32.AddFontResourceExW(path, 0x10, None)
                log(f"font file: {path} (loaded: {count})")
                return path
    log("font file: Anurati .otf not found in script folder or Windows font folders")
    return None


def pick_family(wanted, installed, fallback):
    lookup = {name.lower(): name for name in installed}
    key = wanted.lower()
    if key in lookup:
        return lookup[key]
    for name_lower, name in lookup.items():
        if name_lower.startswith(key):
            return name
    return fallback


def find_desktop_layer():
    progman = user32.FindWindowW("Progman", None)
    if not progman:
        return None, None, "Progman not found"
    result = ctypes.c_size_t()
    user32.SendMessageTimeoutW(progman, 0x052C, 0xD, 0x1, 0, 1000, ctypes.byref(result))
    time.sleep(0.3)
    defview = user32.FindWindowExW(progman, None, "SHELLDLL_DefView", None)
    if defview:
        return progman, defview, "new layout (icons inside Progman)"
    found = []

    def visit(hwnd, lparam):
        if hwnd != progman and user32.FindWindowExW(hwnd, None, "SHELLDLL_DefView", None):
            sibling = user32.FindWindowExW(None, hwnd, "WorkerW", None)
            if sibling:
                found.append(sibling)
        return True

    callback = WNDENUMPROC(visit)
    user32.EnumWindows(callback, 0)
    if found:
        return found[0], None, "classic layout (separate WorkerW)"
    return None, None, "no desktop layer found"


def embed_in_desktop(hwnd, x, y, w, h):
    parent, defview, layout = find_desktop_layer()
    log(f"desktop layout: {layout}")
    if not parent:
        return False
    user32.SetParent(hwnd, parent)
    style = get_long(hwnd, -16)
    style = (style & ~0x80000000 & ~0x00C00000 & ~0x00040000) | 0x40000000 | 0x10000000
    set_long(hwnd, -16, style)
    flags = 0x0010 | 0x0020 | 0x0040
    if defview:
        user32.SetWindowPos(hwnd, None, x, y, w, h, flags)
    else:
        user32.SetWindowPos(hwnd, None, x, y, w, h, flags | 0x0004)
    return True


def track(text):
    return "\u200a".join(text) if SMALL_SPACING else text


def main():
    open(LOG_PATH, "w").close()
    load_settings()
    enable_dpi_awareness()
    load_local_font()

    state = {"restart": False}
    stamps = {"value": file_stamps()}
    days = DAYS_FULL if FULL_DAY_NAMES else DAYS_SHORT

    root = tk.Tk()
    root.title("DesktopClock")
    root.overrideredirect(True)
    root.configure(bg=KEY)
    root.attributes("-transparentcolor", KEY)

    installed = set(tkfont.families())
    day_family = pick_family(DAY_FONT, installed, "Segoe UI")
    small_family = pick_family(SMALL_FONT, installed, "Segoe UI")
    log(f"day font in use: {day_family}")
    log(f"small font in use: {small_family}")

    day_font = tkfont.Font(family=day_family, size=-DAY_SIZE_PX)
    small_font = tkfont.Font(family=small_family, size=-SMALL_SIZE_PX)

    pad = max(r for r, _ in GLOW_LAYERS) + 4 if GLOW else 4
    widest_day = max(day_font.measure(d) for d in days)
    sample = track("00 WWW 0000" + SEPARATOR + "00:00:00")
    width = max(widest_day, small_font.measure(sample)) + pad * 2
    day_h = day_font.metrics("linespace")
    small_h = small_font.metrics("linespace")
    height = day_h + GAP_PX + small_h + pad * 2

    canvas = tk.Canvas(root, width=width, height=height, bg=KEY,
                       highlightthickness=0, bd=0)
    canvas.pack()

    day_items = []
    if GLOW:
        for r, colour in GLOW_LAYERS:
            d = int(r * 0.7)
            for dx, dy in [(r, 0), (-r, 0), (0, r), (0, -r), (d, d), (d, -d), (-d, d), (-d, -d)]:
                day_items.append(canvas.create_text(pad + dx, pad + dy, text="", anchor="nw",
                                                    font=day_font, fill=colour))
    day_items.append(canvas.create_text(pad, pad, text="", anchor="nw",
                                        font=day_font, fill=TEXT_COLOR))

    small_y = pad + day_h + GAP_PX
    left_item = canvas.create_text(0, small_y, text="", font=small_font, fill=TEXT_COLOR)
    right_item = canvas.create_text(0, small_y, text="", font=small_font, fill=TEXT_COLOR)

    def place_small(day_width):
        left_x = pad + SMALL_OFFSET_X
        right_x = pad + day_width - SMALL_OFFSET_X
        if SMALL_LAYOUT == "split":
            canvas.coords(left_item, left_x + DATE_OFFSET_X, small_y + DATE_OFFSET_Y)
            canvas.itemconfigure(left_item, anchor="nw")
            canvas.coords(right_item, right_x + TIME_OFFSET_X, small_y + TIME_OFFSET_Y)
            canvas.itemconfigure(right_item, anchor="ne")
        elif SMALL_LAYOUT == "left":
            canvas.coords(left_item, left_x, small_y)
            canvas.itemconfigure(left_item, anchor="nw")
        elif SMALL_LAYOUT == "right":
            canvas.coords(left_item, right_x, small_y)
            canvas.itemconfigure(left_item, anchor="ne")
        else:
            canvas.coords(left_item, pad + day_width / 2, small_y)
            canvas.itemconfigure(left_item, anchor="n")

    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    x = int((sw - width) * POS_X) + OFFSET_X
    y = int((sh - height) * POS_Y) + OFFSET_Y
    root.geometry(f"{width}x{height}+{x}+{y}")
    root.update_idletasks()
    root.update()

    hwnd = user32.GetParent(root.winfo_id()) or root.winfo_id()
    ex_style = get_long(hwnd, -20)
    ex_style |= 0x00080000 | 0x00000020 | 0x00000080 | 0x08000000
    set_long(hwnd, -20, ex_style)

    embedded = EMBED_IN_DESKTOP and embed_in_desktop(hwnd, x, y, width, height)
    if embedded:
        ok = user32.SetLayeredWindowAttributes(hwnd, 0x010101, 0, 0x1)
        log(f"colorkey set: {bool(ok)} (error {ctypes.get_last_error()}), visible: {bool(user32.IsWindowVisible(hwnd))}")
    log(f"embedded in desktop: {bool(embedded)}")

    last = {"day": None, "left": None, "right": None}

    def tick():
        t = time.localtime()
        day = days[t.tm_wday]
        clock = time.strftime("%H:%M:%S" if SHOW_SECONDS else "%H:%M", t)
        date = f"{t.tm_mday:02d} {MONTHS[t.tm_mon - 1]} {t.tm_year}"
        if SMALL_LAYOUT == "split":
            left_text, right_text = track(date), track(clock)
        else:
            left_text, right_text = track(date + SEPARATOR + clock), ""

        if day != last["day"]:
            for item in day_items:
                canvas.itemconfigure(item, text=day)
            place_small(day_font.measure(day))
            last["day"] = day
        if left_text != last["left"]:
            canvas.itemconfigure(left_item, text=left_text)
            last["left"] = left_text
        if right_text != last["right"]:
            canvas.itemconfigure(right_item, text=right_text)
            last["right"] = right_text

        root.after(1005 - int((time.time() % 1) * 1000), tick)

    def watch():
        now = file_stamps()
        if now != stamps["value"]:
            stamps["value"] = now
            if files_are_valid():
                state["restart"] = True
                root.destroy()
                return
        root.after(700, watch)

    def check_quit():
        down = lambda vk: user32.GetAsyncKeyState(vk) & 0x8000
        if down(0x11) and down(0x12) and down(0x51):
            root.destroy()
            return
        root.after(250, check_quit)

    tick()
    check_quit()
    watch()
    root.mainloop()

    if state["restart"]:
        subprocess.Popen([sys.executable, SCRIPT_PATH])


if __name__ == "__main__":
    try:
        main()
    except Exception:
        log(traceback.format_exc())
