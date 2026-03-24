import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32
hwnd = 0x50720

# Get window position
rect = wintypes.RECT()
user32.GetWindowRect(hwnd, ctypes.byref(rect))
win_x = rect.left
win_y = rect.top
win_w = rect.right - rect.left
win_h = rect.bottom - rect.top

print(f"Window: ({win_x}, {win_y}) {win_w}x{win_h}")

# Try different Y positions for tabs (typical ribbon is 80-150px from top)
# Based on typical WinDBG UI, tabs should be around y = 95-130

# Let's try multiple positions to find the tabs
test_positions = [
    ("Home", win_x + 100, win_y + 95),
    ("Home", win_x + 120, win_y + 100),
    ("Home", win_x + 130, win_y + 110),
    ("Home", win_x + 150, win_y + 115),
    ("Home", win_x + 150, win_y + 120),
]

def click(x, y):
    user32.SetCursorPos(x, y)
    time.sleep(0.1)
    user32.mouse_event(0x0002, 0, 0, 0, 0)  # Down
    time.sleep(0.05)
    user32.mouse_event(0x0004, 0, 0, 0, 0)  # Up

print("\nTrying different positions:")
for name, x, y in test_positions:
    print(f"  {name} at ({x}, {y})...")
    click(x, y)
    time.sleep(0.3)

print("\nDone! Try clicking manually to see where the cursor goes.")
