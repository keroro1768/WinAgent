"""
WinAgent UIA Demo v5 - 簡化穩定版
使用最可靠的純鍵盤模擬方式
"""

import subprocess
import time
import sys
import os
from datetime import datetime
import threading

try:
    import uiautomation as auto
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "uiautomation"])
    import uiautomation as auto

def check_file_recently_modified(folder, extension=".txt", minutes=1):
    """檢查最近修改的檔案"""
    import glob
    import time
    
    pattern = os.path.join(folder, f"*{extension}")
    files = glob.glob(pattern)
    
    if not files:
        return None
        
    # 按修改時間排序
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    
    # 檢查最近的
    for f in files[:5]:
        mtime = os.path.getmtime(f)
        if time.time() - mtime < minutes * 60:
            return f
    
    return None

def demo():
    print("=" * 50)
    print("WinAgent UIA Demo v5")
    print("=" * 50)
    
    docs = os.path.expanduser("~/Documents")
    desktop = os.path.expanduser("~/Desktop")
    
    # 1. Launch Notepad
    print("\n[1] Launch Notepad")
    proc = subprocess.Popen("notepad.exe")
    pid = proc.pid
    print(f"    PID: {pid}")
    time.sleep(2)
    
    # 2. Type
    print("\n[2] Type text")
    edit = auto.EditControl(searchDepth=1, ProcessId=pid)
    edit.Click()
    time.sleep(0.3)
    
    now = datetime.now().strftime("%Y/%m/%d %H:%M")
    msg = f"Hi, I win - {now}"
    auto.SendKeys(msg)
    print(f"    Typed: {msg}")
    
    # 3. Save As
    print("\n[3] Save As (Ctrl+Shift+S)")
    auto.SendKeys("^+s")
    time.sleep(1.5)
    
    # 4. Type filename
    print("\n[4] Type filename")
    fname = f"WinTest_{datetime.now().strftime('%H%M%S')}.txt"
    auto.SendKeys(fname)
    time.sleep(0.5)
    
    # 5. Save
    print("\n[5] Confirm save")
    auto.SendKeys("{ENTER}")
    time.sleep(1)
    
    # 6. Check result
    print("\n[6] Check result")
    fpath_doc = os.path.join(docs, fname)
    fpath_desk = os.path.join(desktop, fname)
    
    result = ""
    if os.path.exists(fpath_doc):
        result = fpath_doc
    elif os.path.exists(fpath_desk):
        result = fpath_desk
    else:
        # 嘗試找任何最近修改的 txt
        result = check_file_recently_modified(docs) or check_file_recently_modified(desktop)
    
    print("\n" + "=" * 50)
    if result:
        print(f"[OK] Saved: {result}")
        with open(result, 'r', encoding='utf-8') as f:
            print("Content:")
            print("-" * 20)
            print(f.read())
    else:
        print("[WARN] File not found")
    print("=" * 50)
    
    # Close
    time.sleep(1)
    proc.terminate()
    print("\n[Done]")

if __name__ == "__main__":
    demo()
