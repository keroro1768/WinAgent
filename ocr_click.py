"""
WinAgent OCR Auto-Click
使用 Windows.Media.Ocr 識別文字並自動點擊
"""

import subprocess
import json
import time
import ctypes
from ctypes import wintypes

# Known tab positions from OCR
TABS = {
    "home": (200, 47),      # Approximate - needs OCR to find exact
    "文件": (34, 47),
    "breakpoints": (346, 50),
    "time travel": (506, 50),
    "model": (665, 50),
    "scripting": (781, 50),
    "source": (919, 50),
    "memory": (1040, 50),
    "extensions": (1175, 50),
}

user32 = ctypes.windll.user32

def click_at(x, y):
    """點擊指定座標"""
    user32.SetCursorPos(x, y)
    time.sleep(0.1)
    user32.mouse_event(0x0002, 0, 0, 0, 0)  # Down
    time.sleep(0.05)
    user32.mouse_event(0x0004, 0, 0, 0, 0)  # Up

def get_window_handle(process_name="DbgX.Shell"):
    """取得 WinDBG 視窗 handle"""
    import os
    
    # Try to find window by class name
    result = []
    
    def enum_callback(hwnd, lParam):
        cls = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(hwnd, cls, 256)
        
        if 'DbgX' in cls.value:
            result.append(hwnd)
        return 1
    
    user32.EnumWindows(
        ctypes.CFUNCTYPE(wintypes.INT, wintypes.HWND, wintypes.LPARAM)(enum_callback),
        0
    )
    
    # Return the largest window (main window)
    if result:
        return max(result, key=lambda h: 
            user32.GetWindowRect(h, ctypes.byref(wintypes.RECT())) or 0
        )
    return None

def find_tab_ocr():
    """執行 OCR 找出所有分頁"""
    print("執行 OCR 掃描...")
    
    # Run the OCR tool
    result = subprocess.run(
        ["dotnet", "run", "--project", "D:/Project/WinAgent/WinAgentOCR/WinAgentOCR.csproj"],
        capture_output=True,
        text=True,
        cwd="D:/Project/WinAgent/WinAgentOCR"
    )
    
    # Parse output
    tabs = {}
    lines = result.stdout.split('\n')
    
    for line in lines:
        if '@' in line and '(' in line:
            try:
                # Extract name and position
                parts = line.split('@')
                name = parts[0].strip().split()[-1]  # Last word is usually the name
                coords = parts[1].strip('()').split(',')
                x = int(coords[0])
                y = int(coords[1])
                
                # Normalize name
                name_lower = name.lower()
                if 'break' in name_lower:
                    tabs['breakpoints'] = (x, y)
                elif 'time' in name_lower:
                    tabs['time travel'] = (x, y)
                elif 'model' in name_lower:
                    tabs['model'] = (x, y)
                elif 'script' in name_lower:
                    tabs['scripting'] = (x, y)
                elif 'sour' in name_lower:
                    tabs['source'] = (x, y)
                elif 'mem' in name_lower:
                    tabs['memory'] = (x, y)
                elif 'ext' in name_lower:
                    tabs['extensions'] = (x, y)
                elif '文件' in name or 'doc' in name_lower:
                    tabs['文件'] = (x, y)
            except:
                pass
    
    return tabs

def click_tab(tab_name):
    """點擊指定分頁"""
    tab_name = tab_name.lower()
    
    # First, try to use known positions
    if tab_name in TABS:
        x, y = TABS[tab_name]
        print(f"點擊已知位置: {tab_name} @ ({x}, {y})")
        click_at(x, y)
        return True
    
    # Otherwise, run OCR to find position
    tabs = find_tab_ocr()
    
    if tab_name in tabs:
        x, y = tabs[tab_name]
        print(f"點擊 OCR 位置: {tab_name} @ ({x}, {y})")
        click_at(x, y)
        return True
    
    print(f"找不到分頁: {tab_name}")
    print(f"可用的分頁: {list(TABS.keys())}")
    return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        tab_name = sys.argv[1]
        click_tab(tab_name)
    else:
        print("用法: python ocr_click.py <分頁名稱>")
        print(f"可用分頁: {', '.join(TABS.keys())}")
