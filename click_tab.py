import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

def click_at(x, y):
    user32.SetCursorPos(x, y)
    time.sleep(0.1)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

# Get WinDBG main window
def find_main_window():
    results = []
    
    def enum_callback(hwnd, lParam):
        cls_buff = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buff, 256)
        cls = cls_buff.value
        
        if 'DbgX.Shell' in cls and ';;' in cls:
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            w = rect.right - rect.left
            h = rect.bottom - rect.top
            if w > 500:  # Main window
                results.append({
                    'hwnd': hwnd,
                    'x': rect.left,
                    'y': rect.top,
                    'w': w,
                    'h': h
                })
        return 1
    
    CMPFUNC = ctypes.CFUNCTYPE(wintypes.INT, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(CMPFUNC(enum_callback), 0)
    return results

windows = find_main_window()

if windows:
    win = windows[0]
    print(f"Main window: ({win['x']}, {win['y']}) {win['w']}x{win['h']}")
    
    # Home tab is typically at the top, in the ribbon area
    # Let's click on the left side of the toolbar
    # Based on the UI structure, tabs are around y=100-130
    
    # Click on Home tab area (left side)
    home_x = win['x'] + 150  # Left portion
    home_y = win['y'] + 115  # Tab bar height
    
    print(f"Clicking Home tab at ({home_x}, {home_y})...")
    click_at(home_x, home_y)
    print("Done!")
    
    # Also try View tab (next to Home)
    time.sleep(0.3)
    view_x = win['x'] + 220
    view_y = win['y'] + 115
    print(f"Clicking View tab at ({view_x}, {view_y})...")
    click_at(view_x, view_y)
    print("Done!")
    
else:
    print("Main window not found")
