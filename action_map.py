"""
WinAgent Action Map System
建立「元素 → 點擊 → 預期結果」的對應關係
"""

import json
import time
import ctypes
from ctypes import wintypes
from datetime import datetime
import os
import subprocess
import mss

class ActionMap:
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.map_dir = "D:/Project/WinAgent/action_maps"
        os.makedirs(self.map_dir, exist_ok=True)
        self.actions = []
        self.app_name = ""
        
    # ===== 螢幕截取 =====
    def screenshot(self, filename=None):
        """截取螢幕"""
        if not filename:
            filename = f"temp_{int(time.time())}.png"
        
        filepath = os.path.join(self.map_dir, filename)
        
        with mss.mss() as sct:
            sct.shot(output=filepath)
        
        return filepath
    
    def window_screenshot(self, hwnd, filename=None):
        """截取視窗"""
        rect = wintypes.RECT()
        self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        
        x, y = rect.left, rect.top
        w, h = rect.right - rect.left, rect.bottom - rect.top
        
        if not filename:
            filename = f"win_{int(time.time())}.png"
        
        filepath = os.path.join(self.map_dir, filename)
        
        with mss.mss() as sct:
            img = sct.grab({"left": x, "top": y, "width": w, "height": h})
            mss.tools.to_png(img.rgb, img.size, output=filepath)
        
        return filepath
    
    # ===== OCR 文字辨識 =====
    def ocr_text(self, filepath=None):
        """OCR 辨識文字"""
        if not filepath:
            filepath = self.screenshot()
        
        cmd = ["dotnet", "run", "--project", 
               "D:/Project/WinAgent/WinAgentOCR/WinAgentOCR.csproj"]
        
        result = subprocess.run(
            cmd, capture_output=True, encoding='utf-8', errors='ignore',
            cwd="D:/Project/WinAgent/WinAgentOCR"
        )
        
        lines = []
        for line in (result.stdout or '').split('\n'):
            if '@' in line and '(' in line:
                try:
                    text = line.split('@')[0].strip()
                    if text:
                        lines.append(text)
                except:
                    pass
        
        return lines
    
    # ===== 點擊 =====
    def click(self, x, y):
        """點擊座標"""
        self.user32.SetCursorPos(int(x), int(y))
        time.sleep(0.05)
        self.user32.mouse_event(0x0002, 0, 0, 0, 0)  # Down
        time.sleep(0.05)
        self.user32.mouse_event(0x0004, 0, 0, 0, 0)  # Up
    
    # ===== 動作記錄 =====
    def record_action(self, label, x, y, expected_result, description=""):
        """記錄一個動作"""
        action = {
            "label": label,
            "x": x,
            "y": y,
            "expected_result": expected_result,
            "description": description,
            "recorded_at": datetime.now().isoformat(),
            "verified": False,
            "verification_count": 0
        }
        
        self.actions.append(action)
        
        print(f"\n+ Action recorded:")
        print(f"  Label: {label}")
        print(f"  Position: ({x}, {y})")
        print(f"  Expected: {expected_result}")
        
        return action
    
    def verify_action(self, action_index):
        """驗證動作 - 點擊前/後截圖比對"""
        if action_index >= len(self.actions):
            print("Invalid action index")
            return False
        
        action = self.actions[action_index]
        
        print(f"\n=== Verifying: {action['label']} ===")
        
        # 點擊前截圖
        print("[1] Capturing before...")
        before_file = f"before_{action['label']}_{int(time.time())}.png"
        before_path = self.screenshot(before_file)
        before_text = self.ocr_text(before_path)
        
        # 執行點擊
        print(f"[2] Clicking at ({action['x']}, {action['y']})...")
        self.click(action['x'], action['y'])
        
        # 等待 UI 更新
        wait_time = action.get('wait_after_click', 2)
        print(f"[3] Waiting {wait_time}s for UI to update...")
        time.sleep(wait_time)
        
        # 點擊後截圖
        print("[4] Capturing after...")
        after_file = f"after_{action['label']}_{int(time.time())}.png"
        after_path = self.screenshot(after_file)
        after_text = self.ocr_text(after_path)
        
        # 比對結果
        print("\n[5] Verification:")
        print(f"  Expected: {action['expected_result']}")
        
        expected_found = False
        for text in after_text:
            if action['expected_result'].lower() in text.lower():
                expected_found = True
                print(f"  ✓ Found: '{text}'")
                break
        
        if not expected_found:
            # 顯示差異
            print(f"\n  Text before: {before_text[:5]}")
            print(f"  Text after:  {after_text[:5]}")
            
            # 找新出現的文字
            new_text = [t for t in after_text if t not in before_text]
            if new_text:
                print(f"\n  New text appeared:")
                for t in new_text[:5]:
                    print(f"    - {t}")
        
        # 更新記錄
        action['verified'] = expected_found
        action['verification_count'] += 1
        action['last_verified'] = datetime.now().isoformat()
        
        return expected_found
    
    # ===== 儲存/載入 =====
    def save(self, app_name=None):
        """儲存動作地圖"""
        if not app_name:
            app_name = self.app_name or "unknown"
        
        filename = f"{app_name}_actions.json"
        filepath = os.path.join(self.map_dir, filename)
        
        data = {
            "app": app_name,
            "created": datetime.now().isoformat(),
            "actions": self.actions
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n[Saved] {filepath}")
        return filepath
    
    def load(self, app_name):
        """載入動作地圖"""
        filename = f"{app_name}_actions.json"
        filepath = os.path.join(self.map_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"Map not found: {filepath}")
            return False
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.actions = data.get('actions', [])
        self.app_name = data.get('app', app_name)
        
        print(f"[Loaded] {len(self.actions)} actions for {self.app_name}")
        return True
    
    def list_actions(self):
        """列出所有動作"""
        print(f"\n[{len(self.actions)} actions for {self.app_name}]")
        
        for i, a in enumerate(self.actions):
            status = "OK" if a.get('verified') else "--"
            print(f"  {i+1}. [{status}] {a['label']}")
            print(f"      Expected: {a['expected_result']}")
    
    def run_action(self, label_or_index):
        """執行單一動作"""
        # 找動作
        action = None
        
        if isinstance(label_or_index, int):
            if 0 <= label_or_index < len(self.actions):
                action = self.actions[label_or_index]
        else:
            for a in self.actions:
                if label_or_index.lower() in a['label'].lower():
                    action = a
                    break
        
        if not action:
            print(f"Action not found: {label_or_index}")
            return False
        
        print(f"\n>>> Running: {action['label']}")
        
        # 點擊
        self.click(action['x'], action['y'])
        
        # 等待
        wait_time = action.get('wait_after_click', 1)
        time.sleep(wait_time)
        
        print(f"Done")
        
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="WinAgent Action Map")
    parser.add_argument("--app", "-a", help="App name")
    parser.add_argument("--load", "-l", help="Load action map")
    parser.add_argument("--list", action="store_true", help="List actions")
    parser.add_argument("--add", nargs=4, metavar=("LABEL"), help="Add action: LABEL X Y EXPECTED")
    parser.add_argument("--run", "-r", help="Run action by label or index")
    parser.add_argument("--verify", "-v", type=int, help="Verify action by index")
    parser.add_argument("--save", "-s", help="Save action map")
    
    args = parser.parse_args()
    
    mapper = ActionMap()
    
    if args.load:
        mapper.load(args.load)
    
    if args.list:
        mapper.list_actions()
    
    if args.add:
        # add: label x y expected
        label = args.add[0]
        x = int(args.add[1])
        y = int(args.add[2])
        expected = args.add[3]
        
        mapper.record_action(label, x, y, expected)
    
    if args.run:
        mapper.run_action(args.run)
    
    if args.verify is not None:
        mapper.verify_action(args.verify)
    
    if args.save:
        mapper.save(args.save)
    
    if not (args.load or args.list or args.add or args.run or args.verify is not None or args.save):
        print("用法:")
        print("  --app <name>           Set app name")
        print("  --load <name>          Load action map")
        print("  --list                 List actions")
        print("  --add L X Y EXPECTED    Add action")
        print("  --run LABEL            Run action")
        print("  --verify N              Verify action N")
        print("  --save NAME             Save map")

if __name__ == "__main__":
    main()
