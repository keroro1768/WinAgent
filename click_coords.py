import ctypes
from ctypes import wintypes
import time

user32 = ctypes.windll.user32

# Get WinDBG window by process name
def find_window_by_pid(pid):
    results = []
    
    def enum_callback(hwnd, lParam):
        thread_id = user32.GetWindowThreadProcessId(hwnd, None)
        # Just get all windows and filter by class name
        cls_buff = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buff, 256)
        cls = cls_buff.value
        
        if 'DbgX' in cls:
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            results.append({
                'hwnd': hwnd,
                'class': cls,
                'x': rect.left,
                'y': rect.top,
                'w': rect.right - rect.left,
                'h': rect.bottom - rect.top
            })
        return 1
    
    CMPFUNC = ctypes.CFUNCTYPE(wintypes.INT, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(CMPFUNC(enum_callback), 0)
    return results

# Find WinDBG
windows = find_window_by_pid(15872)
print(f'Found {len(windows)} WinDBG windows')

for w in windows:
    print(f"  Window: {w['class'][:40]}")
    print(f"  Position: ({w['x']}, {w['y']}) size: {w['w']}x{w['h']}")
    
    # Click in the toolbar area (typically top part of window)
    # Toolbar is usually around 100-150 pixels from top
    click_x = w['x'] + w['w'] // 2  # Center horizontally
    click_y = w['y'] + 120  # About 120 pixels from top (ribbon area)
    
    print(f'\n  Clicking at ({click_x}, {click_y})...')
    
    # Move and click
    user32.SetCursorPos(click_x, click_y)
    time.sleep(0.1)
    user32.mouse_event(0x0002, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN
    time.sleep(0.05)
    user32.mouse_event(0x0004, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTUP
    
    print('  Click sent!')
