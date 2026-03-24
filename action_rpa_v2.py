"""
WinAgent Action RPA - 完整版
包含鍵盤鉤子來正確擷取 F9/F10 停止訊號
"""

import json
import os
import time
import ctypes
from ctypes import wintypes, windll, CFUNCTYPE, POINTER, c_int, c_void_p, byref
from datetime import datetime
from threading import Thread
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
WH_KEYBOARD_LL = 13
WH_MOUSE_LL = 7
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202

# 鍵盤鉤子
keyboard_hook = None
mouse_hook = None
stop_event = None

def get_cursor_pos():
    x, y = wintypes.DWORD(), wintypes.DWORD()
    user32.GetCursorPos(ctypes.byref(x), ctypes.byref(y))
    return x.value, y.value

def click_at(x, y):
    user32.SetCursorPos(x, y)
    time.sleep(0.03)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.03)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def send_keys(text):
    auto.SendKeys(text, waitTime=0.03)

# ===== Hook Functions =====
def keyboard_proc(code, wparam, lparam):
    """鍵盤鉤子回調"""
    global stop_event
    
    if code >= 0:
        vk_code = ctypes.cast(lparam, POINTER(c_int)).contents.value
        
        # F9 = 120, F10 = 121
        if vk_code in [120, 121]:  # F9 or F10
            stop_event = vk_code
            
    return user32.CallNextHookEx(keyboard_hook, code, wparam, lparam)

def mouse_proc(code, wparam, lparam):
    """滑鼠鉤子回調"""
    global last_mouse_click
    
    if code >= 0:
        if wparam == WM_LBUTTONDOWN:
            x, y = get_cursor_pos()
            last_mouse_click = (x, y)
            
    return user32.CallNextHookEx(mouse_hook, code, wparam, lparam)

# ===== Recorder with Hooks =====
class ActionRecorder:
    def __init__(self):
        self.actions = []
        self.is_recording = False
        self.start_time = None
        self.recording_thread = None
        
    def start(self):
        """開始錄製"""
        global keyboard_hook, mouse_hook, stop_event, last_mouse_click
        
        stop_event = None
        last_mouse_click = None
        
        self.is_recording = True
        self.actions = []
        self.start_time = time.time()
        
        print("\n" + "="*50)
        print("[開始錄製]")
        print("  - 點擊將被自動記錄")
        print("  - 鍵盤輸入將被記錄")
        print("  - 按 F9 停止並儲存")
        print("  - 按 F10 停止並直接播放")
        print("="*50)
        
        # 安裝鍵盤鉤子
        keyboard_hook = windll.user32.SetWindowsHookExA(
            WH_KEYBOARD_LL, keyboard_proc, None, 0
        )
        
        # 安裝滑鼠鉤子
        mouse_hook = windll.user32.SetWindowsHookExA(
            WH_MOUSE_LL, mouse_proc, None, 0
        )
        
        # 訊息泵浦執行緒
        def pump():
            msg = wintypes.MSG()
            while self.is_recording and stop_event is None:
                if user32.PeekMessageA(byref(msg), None, 0, 0, 1):
                    user32.TranslateMessage(byref(msg))
                    user32.DispatchMessageA(byref(msg))
                time.sleep(0.01)
                
            # 清理鉤子
            if keyboard_hook:
                windll.user32.UnhookWindowsHookEx(keyboard_hook)
            if mouse_hook:
                windll.user32.UnhookWindowsHookEx(mouse_hook)
                
        self.recording_thread = Thread(target=pump, daemon=True)
        self.recording_thread.start()
        
        # 記錄執行緒
        def record_loop():
            global last_mouse_click
            
            while self.is_recording:
                # 檢查點擊
                if last_mouse_click:
                    x, y = last_mouse_click
                    last_mouse_click = None
                    
                    # 取得 UI 元素資訊
                    elem_info = None
                    try:
                        elem = auto.ElementFromPoint(x, y)
                        if elem:
                            elem_info = {
                                "name": elem.Name or "(無名)",
                                "type": str(elem.ControlTypeName),
                                "automation_id": elem.AutomationId or ""
                            }
                    except:
                        pass
                    
                    action = {
                        "type": "click",
                        "x": x,
                        "y": y,
                        "timestamp": time.time() - self.start_time,
                        "element": elem_info
                    }
                    self.actions.append(action)
                    name = elem_info["name"] if elem_info else "?"
                    print(f"  [記錄] 點擊 ({x}, {y}) -> {name}")
                    
                time.sleep(0.05)
                
        self.record_thread = Thread(target=record_loop, daemon=True)
        self.record_thread.start()
        
    def stop(self, save=True):
        """停止錄製"""
        global stop_event
        
        self.is_recording = False
        
        if self.recording_thread:
            self.recording_thread.join(timeout=1)
            
        print("\n" + "="*50)
        print(f"[停止錄製] {len(self.actions)} 個動作")
        
        if save and self.actions:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{ts}.json"
            filepath = os.path.join("recordings", filename)
            os.makedirs("recordings", exist_ok=True)
            
            data = {
                "created": datetime.now().isoformat(),
                "duration": time.time() - self.start_time,
                "actions": self.actions
            }
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"[儲存] {filepath}")
            return filepath
        return None

# ===== Player =====
class ActionPlayer:
    def __init__(self):
        self.actions = []
        
    def load(self, filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.actions = data.get("actions", [])
        print(f"[載入] {len(self.actions)} 個動作")
        
    def play(self, speed=1.0, loop=1):
        if not self.actions:
            print("[錯誤] 沒有動作")
            return
            
        print(f"\n{'='*50}")
        print(f"[播放] {len(self.actions)} 個動作")
        print("="*50)
        
        for li in range(loop):
            print(f"\n--- 循環 {li+1}/{loop} ---")
            last_t = 0
            
            for action in self.actions:
                delay = (action["timestamp"] - last_t) / speed
                if delay > 0:
                    time.sleep(min(delay, 2))
                    
                if action["type"] == "click":
                    x, y = action["x"], action["y"]
                    elem = action.get("element", {})
                    name = elem.get("name", "?") if elem else "?"
                    print(f"  [點擊] ({x}, {y}) -> {name}")
                    click_at(x, y)
                    
                elif action["type"] == "key":
                    key = action["key"]
                    print(f"  [鍵盤] {key}")
                    send_keys(key)
                    
                last_t = action["timestamp"]
                
            time.sleep(0.3)
            
        print("\n[完成]")

# ===== Main =====
def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--record", action="store_true")
    parser.add_argument("--play", metavar="FILE")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--loop", type=int, default=1)
    args = parser.parse_args()
    
    if args.list:
        os.makedirs("recordings", exist_ok=True)
        files = sorted(os.listdir("recordings"), reverse=True)
        print("錄製檔案:")
        for f in files:
            fpath = os.path.join("recordings", f)
            size = os.path.getsize(fpath)
            print(f"  {f} ({size/1024:.1f} KB)")
            
    elif args.play:
        player = ActionPlayer()
        player.load(args.play)
        player.play(speed=args.speed, loop=args.loop)
        
    elif args.record:
        recorder = ActionRecorder()
        recorder.start()
        
        # 等到按下 F9 或 F10
        while stop_event is None:
            time.sleep(0.1)
            
        filepath = recorder.stop(save=True)
        
        if stop_event == 121 and filepath:  # F10 - 立即播放
            print("\n[立即播放]")
            player = ActionPlayer()
            player.load(filepath)
            player.play(speed=args.speed, loop=args.loop)
            
    else:
        print("WinAgent Action RPA")
        print("")
        print("用法:")
        print("  --record        開始錄製 (按F9儲存, F10播放)")
        print("  --play FILE    播放錄製")
        print("  --list         列出錄製")
        print("  --speed 2.0    速度")
        print("  --loop 3       循環")

if __name__ == "__main__":
    main()
