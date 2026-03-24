"""
WinAgent Action Recorder
同步錄製：鍵盤輸入 + UIA UI 元素點擊
"""

import time
import json
import os
from datetime import datetime
from threading import Thread
import sys

try:
    import uiautomation as auto
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "uiautomation"])
    import uiautomation as auto

# 全域錄製資料
recording = []
is_recording = False

class ActionRecorder:
    def __init__(self):
        self.recording = []
        self.is_recording = False
        self.last_window = None
        
    def start(self):
        """開始錄製"""
        self.is_recording = True
        self.recording = []
        print("\n" + "="*50)
        print("[錄製開始] 正在記錄你的操作...")
        print("="*50)
        print("操作說明:")
        print("  - 鍵盤輸入會被紀錄")
        print("  - 滑鼠點擊會被紀錄 (包括點擊了哪個UI元素)")
        print("  - 按 ESC 鍵停止錄製")
        print("="*50 + "\n")
        
    def stop(self):
        """停止錄製"""
        self.is_recording = False
        print("\n" + "="*50)
        print(f"[錄製停止] 共紀錄 {len(self.recording)} 個動作")
        print("="*50)
        
    def record_key(self, key):
        """紀錄鍵盤輸入"""
        if not self.is_recording:
            return
            
        action = {
            "type": "keyboard",
            "key": key,
            "timestamp": time.time(),
            "window": self.get_current_window_name()
        }
        self.recording.append(action)
        print(f"[鍵盤] {key}")
        
    def record_click(self, x, y):
        """紀錄滑鼠點擊 + 解析 UI 元素"""
        if not self.is_recording:
            return
            
        # 取得點擊位置的 UI 元素
        element = auto.ElementFromPoint(x, y)
        
        info = {
            "type": "click",
            "x": x,
            "y": y,
            "timestamp": time.time(),
            "window": self.get_current_window_name()
        }
        
        if element:
            try:
                info["element"] = {
                    "name": element.Name or "(無名稱)",
                    "control_type": str(element.ControlTypeName),
                    "automation_id": element.AutomationId or "",
                    "class_name": element.ClassName or ""
                }
                elem_desc = f"{element.ControlTypeName}: {element.Name or element.AutomationId or '?'}"
                print(f"[點擊] ({x}, {y}) -> {elem_desc}")
            except:
                print(f"[點擊] ({x}, {y}) -> (無法識別元素)")
        else:
            print(f"[點擊] ({x}, {y}) -> (無 UI 元素)")
            
        self.recording.append(info)
        
    def get_current_window_name(self):
        """取得目前前景視窗名稱"""
        try:
            w = auto.GetFocusedControl()
            if w:
                root = auto.GetRootElement()
                return root.Name or "Unknown"
        except:
            pass
        return "Unknown"
        
    def save(self, filepath=None):
        """儲存錄製結果"""
        if not filepath:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"recording_{ts}.json"
            
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                "recorded_at": datetime.now().isoformat(),
                "actions": self.recording
            }, f, ensure_ascii=False, indent=2)
            
        print(f"\n[儲存] 錄製已儲存: {filepath}")
        return filepath
        
    def load(self, filepath):
        """載入錄製"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.recording = data.get("actions", [])
        print(f"[載入] 已載入 {len(self.recording)} 個動作")
        
    def replay(self, speed=1.0, loop=1):
        """播放錄製的動作"""
        if not self.recording:
            print("[播放] 沒有可播放的動作")
            return
            
        print(f"\n{'='*50}")
        print(f"[播放] 開始播放 {len(self.recording)} 個動作 (速度: {speed}x, 循環: {loop}次)")
        print("="*50)
        
        for loop_idx in range(loop):
            print(f"\n--- 循環 {loop_idx + 1}/{loop} ---")
            
            last_time = 0
            for i, action in enumerate(self.recording):
                # 計算時間差
                if last_time > 0:
                    delay = (action["timestamp"] - last_time) / speed
                    if delay > 0:
                        time.sleep(min(delay, 2))  # 最多等2秒
                
                # 執行動作
                if action["type"] == "keyboard":
                    print(f"  [播放鍵盤] {action['key']}")
                    auto.SendKeys(action["key"])
                    
                elif action["type"] == "click":
                    x, y = action["x"], action["y"]
                    elem = action.get("element", {})
                    print(f"  [播放點擊] ({x}, {y}) -> {elem.get('name', '?')}")
                    
                    # 移動並點擊
                    auto.MoveTo(x, y)
                    auto.Click()
                    
                last_time = action["timestamp"]
                
            time.sleep(0.5)
            
        print("\n" + "="*50)
        print("[播放] 完成")
        print("="*50)


def demo_scan_only():
    """示範：僅掃描模式 - 監控並顯示 UI 元素"""
    print("="*60)
    print("WinAgent UI Spy - 即時監控模式")
    print("="*60)
    print("功能：")
    print("  - 持續監控前景視窗的 UI 變化")
    print("  - 顯示所有可點擊的按鈕和控制項")
    print("  - 按 Ctrl+C 停止")
    print("="*60 + "\n")
    
    last_hwnd = None
    
    try:
        while True:
            # 取得前景視窗
            fg = auto.GetFocusedControl()
            if not fg:
                time.sleep(0.5)
                continue
                
            # 取得根視窗
            try:
                root = auto.GetRootElement()
            except:
                root = None
                
            if not root or not root.NativeWindowHandle:
                time.sleep(0.5)
                continue
                
            # 如果視窗改變，重新掃描
            hwnd = root.NativeWindowHandle
            if hwnd != last_hwnd:
                last_hwnd = hwnd
                
                print("\n" + "-"*50)
                print(f"[視窗] {root.Name}")
                print("-"*50)
                
                # 遍歷尋找按鈕
                buttons = []
                
                def find_buttons(ctrl, depth=0):
                    if depth > 3:  # 限制深度
                        return
                    try:
                        if "Button" in str(ctrl.ControlTypeName):
                            name = ctrl.Name or ctrl.AutomationId or "(無名)"
                            if name not in [b[0] for b in buttons]:
                                rect = ctrl.BoundingRectangle
                                if rect:
                                    buttons.append((name, ctrl.ControlTypeName, rect))
                    except:
                        pass
                        
                    for child in ctrl.GetChildren()[:10]:  # 限制子元素數量
                        find_buttons(child, depth+1)
                        
                find_buttons(root)
                
                if buttons:
                    print(f"找到 {len(buttons)} 個可點擊元素:")
                    for name, ctype, rect in buttons[:15]:
                        print(f"  [{ctype}] {name}")
                else:
                    print("未找到按鈕控制項")
                    
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n[停止] 監控結束")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="WinAgent Action Recorder")
    parser.add_argument("--scan", action="store_true", help="僅監控 UI 元素")
    parser.add_argument("--record", action="store_true", help="開始錄製")
    parser.add_argument("--replay", metavar="FILE", help="播放錄製檔案")
    parser.add_argument("--speed", type=float, default=1.0, help="播放速度")
    parser.add_argument("--loop", type=int, default=1, help="播放循環次數")
    
    args = parser.parse_args()
    
    if args.scan:
        demo_scan_only()
    elif args.replay:
        recorder = ActionRecorder()
        recorder.load(args.replay)
        recorder.replay(speed=args.speed, loop=args.loop)
    elif args.record:
        print("錄製模式即將啟動...")
        print("請執行你的操作，完成後按 ESC 停止")
        print("\n提示: 這個版本需要搭配鍵盤監控工具")
        print("建議使用獨立的鍵盤監控腳本來配合")
    else:
        # 預設：掃描模式
        demo_scan_only()


if __name__ == "__main__":
    main()
