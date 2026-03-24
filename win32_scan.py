import ctypes
from ctypes import wintypes
import json

user32 = ctypes.windll.user32

# Get WinDBG window
hwnd = user32.GetForegroundWindow()
print('Main HWND:', hex(hwnd))

# Get title
length = user32.GetWindowTextLengthW(hwnd)
buff = ctypes.create_unicode_buffer(length + 1)
user32.GetWindowTextW(hwnd, buff, length + 1)
print('Title:', buff.value)

# EnumChildWindows callback
results = []

def enum_child(hwnd, lParam):
    try:
        length = user32.GetWindowTextLengthW(hwnd)
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value
        else:
            title = ''
        
        cls_buff = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls_buff, 256)
        cls = cls_buff.value
        
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        
        results.append({
            'hwnd': int(hwnd),
            'title': title[:50],
            'class': cls[:50],
            'x': rect.left, 'y': rect.top,
            'w': rect.right - rect.left,
            'h': rect.bottom - rect.top
        })
    except:
        pass
    return 1

# Define callback type
CMPFUNC = ctypes.CFUNCTYPE(wintypes.INT, wintypes.HWND, wintypes.LPARAM)
enum_func = CMPFUNC(enum_child)

# Enum children
user32.EnumChildWindows(hwnd, enum_func, 0)

print(f'\nFound {len(results)} child windows\n')

# Group by class
by_class = {}
for r in results:
    cls = r['class']
    if cls not in by_class:
        by_class[cls] = []
    by_class[cls].append(r)

print('By class:')
for cls, items in sorted(by_class.items(), key=lambda x: -len(x[1])):
    print(f'  {cls}: {len(items)}')

print('\nAll windows:')
for r in results[:40]:
    print(f"  [{r['class'][:20]:<20}] {r['title'][:25]:<25} @({r['x']:>4},{r['y']:>4})")

# Save
with open('D:/Project/WinAgent/windbg_windows.json', 'w', encoding='utf-8', errors='ignore') as f:
    json.dump({
        'app': 'WinDBG',
        'main_hwnd': int(hwnd),
        'title': buff.value,
        'total': len(results),
        'by_class': {k: len(v) for k, v in by_class.items()},
        'windows': results
    }, f, ensure_ascii=False, indent=2)

print('\nSaved to windbg_windows.json')
