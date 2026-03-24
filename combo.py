"""
WinAgent Combo System
組合計系統 - 將多個動作組合成可重複使用的技能
"""

import json
import os
import time
import ctypes
from ctypes import wintypes, byref
from datetime import datetime
import subprocess
import sys

try:
    import uiautomation as auto
except ImportError:
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
    """在指定座標點擊"""
    user32.SetCursorPos(x, y)
    time.sleep(0.03)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.03)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def click_element_by_name(window, name_pattern, control_type="Button"):
    """根據名稱尋找並點擊 UI 元素"""
    buttons = []
    
    def search(ctrl, depth):
        if depth > 4:
            return
        try:
            ct = str(ctrl.ControlTypeName)
            if control_type in ct:
                name = ctrl.Name or ctrl.AutomationId or ""
                if name_pattern.lower() in name.lower():
                    rect = ctrl.BoundingRectangle
                    if rect:
                        center_x = (rect.left + rect.right) // 2
                        center_y = (rect.top + rect.bottom) // 2
                        buttons.append({
                            "name": name,
                            "x": center_x,
                            "y": center_y,
                            "type": ct
                        })
        except:
            pass
        
        try:
            for child in list(ctrl.GetChildren())[:15]:
                search(child, depth + 1)
        except:
            pass
    
    search(window, 0)
    return buttons

def send_keys(text):
    """發送鍵盤輸入"""
    auto.SendKeys(text, waitTime=0.05)

# ===== Combo Executor =====
class ComboExecutor:
    def __init__(self, combo_dir="combos"):
        self.combo_dir = combo_dir
        os.makedirs(combo_dir, exist_ok=True)
        
    def load_combo(self, name):
        """載入組合計"""
        filepath = os.path.join(self.combo_dir, f"{name}.json")
        if not os.path.exists(filepath):
            # 嘗試直接路徑
            if os.path.exists(name):
                filepath = name
            else:
                raise FileNotFoundError(f"Combo not found: {name}")
        
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def execute(self, name_or_path, variables=None, verbose=True):
        """執行組合計"""
        combo = self.load_combo(name_or_path)
        
        # 變數替換
        variables = variables or {}
        if "timestamp" not in variables:
            variables["timestamp"] = datetime.now().strftime("%Y/%m/%d %H:%M")
        
        if verbose:
            print("\n" + "="*50)
            print(f"[執行] {combo.get('name', name_or_path)}")
            print(f"{'='*50}")
        
        # 執行每個步驟
        for i, step in enumerate(combo.get("steps", []), 1):
            action = step.get("action")
            params = step.get("params", {})
            
            # 變數替換
            for key, value in params.items():
                if isinstance(value, str):
                    for var, val in variables.items():
                        value = value.replace(f"{{{var}}}", val)
                    params[key] = value
            
            if verbose:
                print(f"\n[Step {i}] {action}")
            
            try:
                self._execute_action(action, params, verbose)
            except Exception as e:
                if verbose:
                    print(f"  [錯誤] {e}")
                # 繼續執行或停止取決於設定
                if not combo.get("continue_on_error", True):
                    raise
        
        if verbose:
            print("\n" + "="*50)
            print("[完成] 組合計執行完畢")
            print("="*50)
    
    def _execute_action(self, action, params, verbose):
        """執行單一動作"""
        
        if action == "launch":
            # 啟動應用程式
            app = params.get("app")
            args = params.get("args", "")
            
            if app:
                if verbose:
                    print(f"  啟動: {app} {args}")
                
                # 使用 cmd 啟動以避免路徑問題
                subprocess.Popen(f"{app} {args}", shell=True)
                wait = params.get("wait", 2)
                time.sleep(wait)
        
        elif action == "wait":
            # 等待
            duration = params.get("duration", 1)
            if verbose:
                print(f"  等待: {duration}秒")
            time.sleep(duration)
        
        elif action == "click":
            # 點擊座標
            x = params.get("x")
            y = params.get("y")
            
            if x is not None and y is not None:
                if verbose:
                    print(f"  點擊: ({x}, {y})")
                click_at(x, y)
            else:
                # 嘗試點擊元素
                name = params.get("element")
                if name:
                    self._click_element_by_name(name, verbose)
        
        elif action == "click_element":
            # 按名稱點擊元素
            name = params.get("name")
            control_type = params.get("type", "Button")
            
            if name:
                if verbose:
                    print(f"  點擊元素: {name} ({control_type})")
                self._click_element_by_name(name, verbose, control_type)
        
        elif action == "type":
            # 鍵盤輸入
            text = params.get("text", "")
            if verbose:
                print(f"  輸入: {text}")
            send_keys(text)
        
        elif action == "send_keys":
            # 發送特殊鍵
            keys = params.get("keys", "")
            if verbose:
                print(f"  發送: {keys}")
            send_keys(keys)
        
        elif action == "click_menu":
            # 點擊選單
            menu = params.get("menu", "")
            item = params.get("item", "")
            
            if verbose:
                print(f"  選單: {menu} -> {item}")
            
            # 使用 Alt+字母打開選單
            if menu:
                send_keys(f"%{menu[0]}")
                time.sleep(0.3)
            
            # 選擇項目 (使用快速鍵或方向鍵)
            if item:
                send_keys(item[0])
                time.sleep(0.2)
        
        elif action == "screenshot":
            # 截圖
            import PIL.ImageGrab
            path = params.get("path", f"screenshot_{datetime.now().strftime('%H%M%S')}.png")
            if verbose:
                print(f"  截圖: {path}")
            img = PIL.ImageGrab.grab()
            img.save(path)
        
        elif action == "close":
            # 關閉視窗
            if verbose:
                print(f"  關閉視窗")
            send_keys("%{F4}")
        
        else:
            if verbose:
                print(f"  [未知動作] {action}")
    
    def _click_element_by_name(self, name_pattern, verbose, control_type="Button"):
        """根據名稱找並點擊元素"""
        # 取得前景視窗
        fg = auto.GetForegroundWindow()
        if not fg:
            return
        
        buttons = click_element_by_name(fg, name_pattern, control_type)
        
        if buttons:
            btn = buttons[0]
            if verbose:
                print(f"  找到: {btn['name']} @ ({btn['x']}, {btn['y']})")
            click_at(btn['x'], btn['y'])
        else:
            if verbose:
                print(f"  [未找到] {name_pattern}")

# ===== Combo Manager =====
class ComboManager:
    def __init__(self, combo_dir="combos"):
        self.combo_dir = combo_dir
        os.makedirs(combo_dir, exist_ok=True)
        self._init_default_combos()
    
    def _init_default_combos(self):
        """初始化預設組合計"""
        
        # 開啟 Notepad 並存檔
        notepad_save = {
            "name": "開啟 Notepad 並存檔",
            "description": "打開 Notepad，輸入文字，另存新檔",
            "version": "1.0",
            "steps": [
                {"action": "launch", "params": {"app": "notepad.exe", "wait": 2}},
                {"action": "type", "params": {"text": "Hi, I win - {timestamp}"}},
                {"action": "send_keys", "params": {"keys": "^s"}},
                {"action": "wait", "params": {"duration": 1}},
                {"action": "type", "params": {"text": "output_{timestamp}.txt"}},
                {"action": "send_keys", "params": {"keys": "{ENTER}"}}
            ]
        }
        
        # 開啟計算機
        calculator = {
            "name": "開啟計算機",
            "description": "打開 Windows 計算機",
            "version": "1.0",
            "steps": [
                {"action": "launch", "params": {"app": "calc.exe", "wait": 1}}
            ]
        }
        
        # 開啟記事本 + 輸入內容
        notepad_type = {
            "name": "Notepad 輸入文字",
            "description": "打開 Notepad 並輸入指定文字",
            "version": "1.0",
            "steps": [
                {"action": "launch", "params": {"app": "notepad.exe", "wait": 2}},
                {"action": "type", "params": {"text": "{text}"}}
            ]
        }
        
        # 儲存預設組合
        self.save_combo("notepad_save", notepad_save)
        self.save_combo("calculator", calculator)
        self.save_combo("notepad_type", notepad_type)
    
    def save_combo(self, name, combo_data):
        """儲存組合計"""
        filepath = os.path.join(self.combo_dir, f"{name}.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(combo_data, f, ensure_ascii=False, indent=2)
        print(f"[儲存] {filepath}")
    
    def list_combos(self):
        """列出所有組合計"""
        files = [f for f in os.listdir(self.combo_dir) if f.endswith(".json")]
        combos = []
        
        for f in files:
            path = os.path.join(self.combo_dir, f)
            with open(path, "r", encoding="utf-8") as fp:
                data = json.load(fp)
                combos.append({
                    "name": data.get("name", f[:-5]),
                    "description": data.get("description", ""),
                    "file": f
                })
        
        return combos
    
    def create_from_recording(self, recording_path, name):
        """從錄製建立組合計"""
        with open(recording_path, "r", encoding="utf-8") as f:
            recording = json.load(f)
        
        steps = []
        for action in recording.get("actions", []):
            if action.get("type") == "click":
                steps.append({
                    "action": "click",
                    "params": {
                        "x": action.get("x"),
                        "y": action.get("y")
                    }
                })
            elif action.get("type") == "key":
                steps.append({
                    "action": "type",
                    "params": {
                        "text": action.get("key")
                    }
                })
        
        combo = {
            "name": name,
            "description": f"從錄製建立: {recording_path}",
            "version": "1.0",
            "steps": steps
        }
        
        self.save_combo(name, combo)
        return combo

# ===== Main CLI =====
def main():
    import argparse
    parser = argparse.ArgumentParser(description="WinAgent Combo System")
    parser.add_argument("--list", action="store_true", help="列出所有組合計")
    parser.add_argument("--run", metavar="NAME", help="執行組合計")
    parser.add_argument("--path", metavar="FILE", help="執行指定 JSON 檔案")
    parser.add_argument("--create", metavar="NAME", help="建立新組合計")
    parser.add_argument("--edit", metavar="NAME", help="編輯組合計")
    parser.add_argument("--record", metavar="NAME", help="從錄製建立組合計")
    parser.add_argument("--var", action="append", help="變數 (key=value)")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細輸出")
    
    args = parser.parse_args()
    
    executor = ComboExecutor()
    manager = ComboManager()
    
    # 解析變數
    variables = {}
    if args.var:
        for v in args.var:
            if "=" in v:
                key, value = v.split("=", 1)
                variables[key] = value
    
    if args.list:
        # 列出
        combos = manager.list_combos()
        print("\n可用組合計:")
        print("-"*50)
        for c in combos:
            print(f"  • {c['name']}")
            if c['description']:
                print(f"    {c['description']}")
    
    elif args.run:
        # 執行
        executor.execute(args.run, variables, verbose=args.verbose)
    
    elif args.path:
        # 執行指定檔案
        executor.execute(args.path, variables, verbose=args.verbose)
    
    elif args.record:
        # 從錄製建立
        print(f"[從錄製建立] {args.record}")
        # 這裡需要錄製檔案路徑，簡化處理
        print("用法: --record NAME --from RECORDING_FILE")
    
    elif args.create:
        # 建立新組合計
        new_combo = {
            "name": args.create,
            "description": "New combo",
            "version": "1.0",
            "steps": [
                {"action": "launch", "params": {"app": "notepad.exe"}}
            ]
        }
        manager.save_combo(args.create, new_combo)
        print(f"[建立] {args.create}.json")
    
    elif args.edit:
        # 編輯組合計
        combo = manager.load_combo(args.edit)
        print(json.dumps(combo, ensure_ascii=False, indent=2))
    
    else:
        # 顯示說明
        print("WinAgent Combo System")
        print("")
        print("用法:")
        print("  --list              列出所有組合計")
        print("  --run NAME          執行組合計")
        print("  --path FILE         執行 JSON 檔案")
        print("  --create NAME       建立新組合計")
        print("  --edit NAME         顯示組合計內容")
        print("  --var key=value     傳入變數")
        print("  -v                  詳細輸出")
        print("")
        print("範例:")
        print("  python combo.py --list")
        print("  python combo.py --run notepad_save")
        print("  python combo.py --run notepad_type --var text='Hello World'")
        print("  python combo.py --run mycombo.json")

if __name__ == "__main__":
    main()
