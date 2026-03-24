"""
WinAgent Action RPA - 簡化穩定版
使用定時輪詢而非鉤子，更穩定
"""

import json
import os
import time
import ctypes
from ctypes import wintypes, byref
from datetime import datetime
from threading import Thread, Event
import sys

try:
    import uiautomation as auto
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "uiautomation"])
    import uiautomation as auto

# ===== Win32 API =====
user32 = ctypes.windll.user32
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

def get_cursor_pos():
    x, y = wintypes.DWORD(), wintypes.DWORD()
    user32.GetCursorPos(byref(x), byref(y))
    return x.value, y.value

def click_at(x, y):
    user32.SetCursorPos(x, y)
    time.sleep(0.02)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.02)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def send_keys(text):
    auto.SendKeys(text, waitTime=0.02)

# ===== Global State =====
is_recording = False
record_actions = []
start_time = 0
stop_flag = Event()

# ===== Recorder =====
def start_recording():
    global is_recording, record_actions, start_time, stop_flag
    
    is_recording = True
    record_actions = []
    start_time = time.time()
    stop_flag.clear()
    
    print("\n" + "="*50)
    print("[開始錄製]")
    print("  點擊將被自動記錄")
    print("  按 Ctrl+C 停止並儲存")
    print("="*50)
    
    # 記錄執行緒
    last_click = (0, 0)
    
    while is_recording:
        # 檢查目前的滑鼠狀態
        current_pos = get_cursor_pos()
        
        # 簡單的狀態檢測 - 這是簡化版
        # 實際使用時，建議用滑鼠鉤子
        
        time.sleep(0.1)
        
    print(f"\n[停止] 共記錄 {len(record_actions)} 個動作")

def record_click(x, y):
    """記錄點擊"""
    if not is_recording:
        return
    
    # 取得 UI 元素資訊
    elem_info = None
    try:
        elem = auto.ElementFromPoint(x, y)
        if elem:
            elem_info = {
                "name": elem.Name or "(no name)",
                "type": str(elem.ControlTypeName)
            }
    except:
        pass
    
    action = {
        "type": "click",
        "x": x,
        "y": y,
        "timestamp": time.time() - start_time,
        "element": elem_info
    }
    record_actions.append(action)
    name = elem_info["name"] if elem_info else "?"
    print(f"  [記錄] ({x}, {y}) -> {name}")

def save_recording(filename=None):
    """儲存錄製"""
    if not record_actions:
        print("[警告] 沒有動作可儲存")
        return None
    
    if not filename:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recording_{ts}.json"
    
    filepath = os.path.join("recordings", filename)
    os.makedirs("recordings", exist_ok=True)
    
    data = {
        "created": datetime.now().isoformat(),
        "duration": time.time() - start_time,
        "actions": record_actions
    }
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"[儲存] {filepath}")
    return filepath

# ===== Player =====
def load_recording(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("actions", [])

def play_recording(actions, speed=1.0, loop=1):
    if not actions:
        print("[錯誤] 沒有動作")
        return
    
    print(f"\n{'='*50}")
    print(f"[播放] {len(actions)} 個動作")
    print("="*50)
    
    for li in range(loop):
        print(f"\n--- 循環 {li+1}/{loop} ---")
        last_t = 0
        
        for action in actions:
            delay = (action["timestamp"] - last_t) / speed
            if delay > 0:
                time.sleep(min(delay, 2))
            
            if action["type"] == "click":
                x, y = action["x"], action["y"]
                elem = action.get("element", {})
                name = elem.get("name", "?") if elem else "?"
                print(f"  [點擊] ({x}, {y}) -> {name}")
                click_at(x, y)
                
            last_t = action["timestamp"]
            
        time.sleep(0.3)
        
    print("\n[完成]")

# ===== Demo: Auto-record clicks =====
def demo_auto_record(duration=15):
    """自動記錄點擊（輪詢方式）"""
    global is_recording, record_actions, start_time
    
    is_recording = True
    record_actions = []
    start_time = time.time()
    
    print(f"\n[自動錄製模式] 將錄製 {duration} 秒")
    print("請進行你想記錄的操作...\n")
    
    last_state = user32.GetAsyncKeyState(0x01)  # 左鍵狀態
    last_pos = get_cursor_pos()
    
    end_time = time.time() + duration
    
    while time.time() < end_time:
        # 檢查滑鼠按鈕狀態
        current_state = user32.GetAsyncKeyState(0x01)
        
        # 如果按下（狀態 < 0 表示按下）
        if current_state < 0 and last_state >= 0:
            # 剛按下的時刻
            x, y = get_cursor_pos()
            record_click(x, y)
        
        last_state = current_state
        time.sleep(0.05)
    
    is_recording = False
    
    # 自動儲存
    filepath = save_recording()
    return filepath

# ===== Main =====
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true", help="開始錄製")
    parser.add_argument("--auto", action="store_true", help="自動錄製15秒")
    parser.add_argument("--play", metavar="FILE", help="播放錄製")
    parser.add_argument("--list", action="store_true", help="列出錄製")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--loop", type=int, default=1)
    args = parser.parse_args()
    
    if args.list:
        os.makedirs("recordings", exist_ok=True)
        files = sorted(os.listdir("recordings"), reverse=True)
        if files:
            print("錄製檔案:")
            for f in files:
                print(f"  - {f}")
        else:
            print("沒有錄製檔案")
            
    elif args.play:
        actions = load_recording(args.play)
        play_recording(actions, speed=args.speed, loop=args.loop)
        
    elif args.record:
        try:
            start_recording()
        except KeyboardInterrupt:
            is_recording = False
            save_recording()
            
    elif args.auto:
        demo_auto_record(15)
        
    else:
        print("WinAgent Action RPA")
        print("")
        print("用法:")
        print("  --record        互動錄製 (Ctrl+C 停止)")
        print("  --auto          自動錄製 15 秒")
        print("  --play FILE     播放錄製")
        print("  --list          列出錄製")
        print("  --speed 2.0     播放速度")
        print("  --loop 3         循環次數")

if __name__ == "__main__":
    main()
