import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

hwnd = 0x50720  # WinDBG

results = []

def enum_child(hwnd, lParam):
    cls = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, cls, 256)
    
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    
    # Get text
    length = user32.GetWindowTextLengthW(hwnd)
    if length > 0:
        buff = ctypes.create_unicode_buffer(length+1)
        user32.GetWindowTextW(hwnd, buff, length+1)
        text = buff.value
    else:
        text = ''
    
    results.append({
        'class': cls.value[:40],
        'text': text[:30],
        'x': rect.left,
        'y': rect.top,
        'w': rect.right - rect.left,
        'h': rect.bottom - rect.top
    })
    return 1

user32.EnumChildWindows(hwnd, ctypes.CFUNCTYPE(wintypes.INT, wintypes.HWND, wintypes.LPARAM)(enum_child), 0)

print(f'Found {len(results)} children\n')

# Show with positions - filter out tiny windows
for r in results:
    if r['w'] > 20 and r['h'] > 10:  # Non-trivial windows
        print(f"  [{r['class'][:25]:<25}] '{r['text'][:20]:<20}' @({r['x']},{r['y']}) {r['w']}x{r['h']}")
