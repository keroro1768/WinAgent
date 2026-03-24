import ctypes
from ctypes import wintypes
import json

user32 = ctypes.windll.user32

# Get foreground
hwnd = user32.GetForegroundWindow()
print('Foreground:', hex(hwnd))

# Find all windows with DbgX
results = []

def callback(hwnd, lParam):
    cls_buff = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, cls_buff, 256)
    cls = cls_buff.value
    
    if 'Dbg' in cls or 'dbg' in cls.lower():
        length = user32.GetWindowTextLengthW(hwnd)
        title = ''
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value
        
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        
        results.append({
            'hwnd': int(hwnd),
            'class': cls,
            'title': title[:50],
            'x': rect.left, 'y': rect.top,
            'w': rect.right - rect.left,
            'h': rect.bottom - rect.top
        })
    
    return 1

CMPFUNC = ctypes.CFUNCTYPE(wintypes.INT, wintypes.HWND, wintypes.LPARAM)
user32.EnumWindows(CMPFUNC(callback), 0)

print('Found:', len(results))
for r in results:
    print(f'  [{r["class"][:30]}] {r["title"][:30]} @({r["x"]},{r["y"]})')

# Save
with open('D:/Project/WinAgent/windbg_dlgx.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print('Saved')
