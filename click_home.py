import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32

# Find main window
wins = []

def callback(hwnd, lParam):
    cls = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, cls, 256)
    
    if 'DbgX.Shell' in cls.value:
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        w = rect.right - rect.left
        if w > 500:
            wins.append({
                'hwnd': hwnd,
                'x': rect.left,
                'y': rect.top,
                'w': w,
                'h': rect.bottom - rect.top
            })
    return 1

CMPFUNC = ctypes.CFUNCTYPE(wintypes.INT, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows(CMPFUNC(callback), 0)

if wins:
    m = wins[0]
    print(f"Window: ({m['x']}, {m['y']}) {m['w']}x{m['h']}")
    
    # Click Home tab
    x = m['x'] + 150
    y = m['y'] + 112
    
    print(f"Clicking Home tab at ({x}, {y})...")
    user32.SetCursorPos(x, y)
    time.sleep(0.1)
    user32.mouse_event(0x0002, 0, 0, 0, 0)  # Down
    time.sleep(0.05)
    user32.mouse_event(0x0004, 0, 0, 0, 0)  # Up
    print("Done!")
else:
    print("Window not found")
