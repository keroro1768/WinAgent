import ctypes
from ctypes import wintypes
import json

user32 = ctypes.windll.user32
hwnd = 0x50720

results = []

def enum_child(hwnd, lParam):
    cls = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, cls, 256)
    
    length = user32.GetWindowTextLengthW(hwnd)
    text = ''
    if length > 0:
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        text = buff.value
    
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    
    results.append({
        'hwnd': int(hwnd),
        'class': cls.value[:50],
        'text': text[:50],
        'x': rect.left,
        'y': rect.top,
        'w': rect.right - rect.left,
        'h': rect.bottom - rect.top
    })
    
    return 1

user32.EnumChildWindows(hwnd, ctypes.CFUNCTYPE(wintypes.INT, wintypes.HWND, wintypes.LPARAM)(enum_child), 0)

print(f'Found {len(results)} windows\n')

# Show all with meaningful content
for r in results:
    if r['w'] > 10 and r['h'] > 5:
        print(f"[{r['class'][:30]:<30}] '{r['text'][:25]:<25}' @({r['x']},{r['y']}) {r['w']}x{r['h']}")

# Save
with open('D:/Project/WinAgent/windbg_windows2.json', 'w', encoding='utf-8', errors='ignore') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print('\nSaved')
