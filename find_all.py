import ctypes
from ctypes import wintypes
import json

user32 = ctypes.windll.user32

hwnd = 0x50720

all_windows = []

def get_all_children(parent, depth=0):
    if depth > 5:
        return
    
    def enum_cb(hwnd, lParam):
        try:
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
            
            all_windows.append({
                'depth': depth,
                'class': cls.value[:50],
                'text': text[:50],
                'x': rect.left,
                'y': rect.top,
                'w': rect.right - rect.left,
                'h': rect.bottom - rect.top
            })
        except:
            pass
        
        get_all_children(hwnd, depth + 1)
        
        return 1
    
    user32.EnumChildWindows(parent, ctypes.CFUNCTYPE(wintypes.INT, wintypes.HWND, wintypes.LPARAM)(enum_cb), 0)

get_all_children(hwnd)

print(f'Total windows: {len(all_windows)}')

# Search for tab-related text
keywords = ['home', 'view', 'break', 'time', 'model', 'script', 'source', 'memory', 'ext', 'note', 'command', '文件']

found_count = 0
for w in all_windows:
    text_lower = w['text'].lower()
    for kw in keywords:
        if kw in text_lower:
            print(f"  [{w['class'][:30]:<30}] '{w['text']:<20}' @({w['x']},{w['y']}) {w['w']}x{w['h']}")
            found_count += 1

if found_count == 0:
    print('No tab-like text found')
    # Show all non-empty text
    print('\nAll windows with text:')
    for w in all_windows[:30]:
        if w['text']:
            print(f"  [{w['class'][:30]:<30}] '{w['text']:<30}'")

# Save all
with open('D:/Project/WinAgent/all_windows.json', 'w', encoding='utf-8', errors='ignore') as f:
    json.dump(all_windows, f, ensure_ascii=False, indent=2)

print('\nSaved to all_windows.json')
