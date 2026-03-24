"""
WinAgent UIA Demo - 使用純 Win32 API
更穩定可靠的方法
"""

import ctypes
from ctypes import wintypes
import subprocess
import time
from datetime import datetime
import os

# Win32 constants
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
VK_CONTROL = 0x11
VK_S = 0x53
VK_RETURN = 0x0D

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

def find_window_by_pid(pid):
    """根據 PID 找到視窗"""
    windows = []
    
    def enum_windows(hwnd, lParam):
        if user32.IsWindowVisible(hwnd):
            _, found_pid = ctypes.c_long(), ctypes.c_long()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(found_pid))
            if found_pid.value == pid:
                windows.append(hwnd)
        return True
    
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(EnumWindowsProc(enum_windows), 0)
    return windows[0] if windows else None

def send_keys_to_window(hwnd, keys):
    """發送鍵盤訊息到視窗"""
    for c in keys:
        # Key down
        user32.PostMessageW(hwnd, WM_KEYDOWN, ord(c.upper()), 0)
        time.sleep(0.05)
        # Key up
        user32.PostMessageW(hwnd, WM_KEYUP, ord(c.upper()), 0)
        time.sleep(0.05)

def demo():
    print("=" * 50)
    print("WinAgent UIA Demo (Win32 API)")
    print("=" * 50)
    
    docs = os.path.expanduser("~/Documents")
    
    # 1. Launch Notepad
    print("\n[1] Launch Notepad")
    proc = subprocess.Popen("notepad.exe")
    time.sleep(2)
    
    hwnd = find_window_by_pid(proc.pid)
    if not hwnd:
        print("    [ERROR] Cannot find window")
        return
    
    print(f"    Window found (PID: {proc.pid})")
    
    # 2. Activate window and type
    print("\n[2] Type text")
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.3)
    
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    msg = f"Hi, I win - {now}"
    
    # Use SendKeys via ctypes
    for c in msg:
        user32.PostMessageW(hwnd, WM_KEYDOWN, ord(c), 0)
        time.sleep(0.02)
        user32.PostMessageW(hwnd, WM_KEYUP, ord(c), 0)
        time.sleep(0.02)
    
    print(f"    Typed: {msg}")
    
    # 3. Save As (Ctrl+S)
    print("\n[3] Save As")
    # Ctrl down
    user32.PostMessageW(hwnd, WM_KEYDOWN, VK_CONTROL, 0)
    time.sleep(0.1)
    # S down
    user32.PostMessageW(hwnd, WM_KEYDOWN, VK_S, 0)
    time.sleep(0.1)
    # S up
    user32.PostMessageW(hwnd, WM_KEYUP, VK_S, 0)
    time.sleep(0.1)
    # Ctrl up
    user32.PostMessageW(hwnd, WM_KEYUP, VK_CONTROL, 0)
    time.sleep(1)
    
    # 4. Type filename
    print("\n[4] Type filename")
    fname = f"WinTest_{datetime.now().strftime('%H%M%S')}.txt"
    
    for c in fname:
        user32.PostMessageW(hwnd, WM_KEYDOWN, ord(c), 0)
        time.sleep(0.02)
        user32.PostMessageW(hwnd, WM_KEYUP, ord(c), 0)
        time.sleep(0.02)
    
    time.sleep(0.3)
    
    # 5. Enter to save
    print("\n[5] Save")
    user32.PostMessageW(hwnd, WM_KEYDOWN, VK_RETURN, 0)
    time.sleep(0.1)
    user32.PostMessageW(hwnd, WM_KEYUP, VK_RETURN, 0)
    time.sleep(1)
    
    # 6. Check
    print("\n[6] Check result")
    fpath = os.path.join(docs, fname)
    
    print("\n" + "=" * 50)
    if os.path.exists(fpath):
        print(f"[OK] Saved: {fpath}")
        with open(fpath, 'r', encoding='utf-8') as f:
            print("Content:")
            print(f.read())
    else:
        # Try alternate location
        fpath = os.path.join(os.path.expanduser("~/Desktop"), fname)
        if os.path.exists(fpath):
            print(f"[OK] Saved: {fpath}")
            with open(fpath, 'r', encoding='utf-8') as f:
                print(f.read())
        else:
            print("[WARN] File not found")
    print("=" * 50)
    
    # Cleanup
    time.sleep(1)
    proc.terminate()
    print("\n[Done]")

if __name__ == "__main__":
    demo()