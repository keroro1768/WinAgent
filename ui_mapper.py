"""
WinAgent UI Mapper - 互動式 UI 元素標記工具
功能：
1. 截圖
2. 讓使用者標記區域
3. OCR 自動辨識文字或手動輸入標籤
4. 儲存 UI 地圖
"""

import subprocess
import json
import time
import ctypes
from ctypes import wintypes
from datetime import datetime
import os
import sys

class UIMapper:
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.gdi32 = ctypes.windll.gdi32
        self.elements = []
        self.map_file = "D:/Project/WinAgent/ui_maps"
        os.makedirs(self.map_file, exist_ok=True)
        
    def get_window(self, name):
        results = []
        
        def cb(hwnd, lParam):
            pid = wintypes.DWORD()
            self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            
            length = self.user32.GetWindowTextLengthW(hwnd)
            title = ""
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value
            
            cls_buff = ctypes.create_unicode_buffer(256)
            self.user32.GetClassNameW(hwnd, cls_buff, 256)
            
            if name.lower() in title.lower() or name.lower() in cls_buff.value.lower():
                rect = wintypes.RECT()
                self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                w = rect.right - rect.left
                h = rect.bottom - rect.top
                results.append({
                    'hwnd': hwnd, 'title': title, 
                    'class': cls_buff.value, 'pid': pid.value,
                    'x': rect.left, 'y': rect.top, 'w': w, 'h': h
                })
            return 1
        
        self.user32.EnumWindows(
            ctypes.CFUNCTYPE(wintypes.INT, wintypes.HWND, wintypes.LPARAM)(cb), 0
        )
        
        if results:
            return max(results, key=lambda r: r['w'] * r['h'])
        return None
    
    def capture_screen(self, x, y, w, h):
        """截取螢幕區域"""
        import mss
        
        if w <= 0 or h <= 0:
            return None
        
        with mss.mss() as sct:
            img = sct.grab({"left": x, "top": y, "width": w, "height": h})
            return img
    
    def ocr_region(self, x, y, w, h):
        """OCR 識別區域內的文字"""
        import mss
        
        # 截圖
        with mss.mss() as sct:
            img = sct.grab({"left": x, "top": y, "width": w, "height": h})
            temp_file = f"D:/Project/WinAgent/temp_region_{int(time.time())}.png"
            mss.tools.to_png(img.rgb, img.size, output=temp_file)
        
        temp_file = f"D:/Project/WinAgent/temp_region_{int(time.time())}.png"
        img.save(temp_file)
        
        # 呼叫 OCR
        cmd = [
            "dotnet", "run", "--project",
            "D:/Project/WinAgent/WinAgentOCR/WinAgentOCR.csproj"
        ]
        
        result = subprocess.run(
            cmd, capture_output=True, encoding='utf-8', errors='ignore',
            cwd="D:/Project/WinAgent/WinAgentOCR"
        )
        
        # 解析結果
        lines = []
        for line in (result.stdout or '').split('\n'):
            if '@' in line and '(' in line:
                try:
                    parts = line.split('@')
                    text = parts[0].strip()
                    if text:
                        lines.append(text)
                except:
                    pass
        
        return ' '.join(lines) if lines else None
    
    def add_element(self, x, y, label=None, width=50, height=30):
        """新增 UI 元素"""
        # 如果沒有標籤，嘗試 OCR
        if not label:
            label = self.ocr_region(x - width//2, y - height//2, width, height)
            if not label:
                label = f"element_{len(self.elements) + 1}"
        
        element = {
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'label': label,
            'added_at': datetime.now().isoformat()
        }
        
        self.elements.append(element)
        print(f"  + Added: {label} @ ({x}, {y})")
        
        return element
    
    def save_map(self, app_name):
        """儲存 UI 地圖"""
        filename = f"{app_name}_{datetime.now().strftime('%Y%m%d')}.json"
        filepath = os.path.join(self.map_file, filename)
        
        data = {
            'app': app_name,
            'created': datetime.now().isoformat(),
            'elements': self.elements
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n[Saved] {filepath}")
        return filepath
    
    def load_map(self, app_name):
        """載入 UI 地圖"""
        # 找最新的
        files = sorted(os.listdir(self.map_file))
        matching = [f for f in files if f.startswith(app_name)]
        
        if matching:
            filepath = os.path.join(self.map_file, matching[-1])
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.elements = data.get('elements', [])
            print(f"[Loaded] {filepath}")
            return True
        return False
    
    def click_element(self, label):
        """點擊已儲存的元素"""
        for elem in self.elements:
            if label.lower() in elem.get('label', '').lower():
                x = elem['x']
                y = elem['y']
                print(f"Clicking: {elem['label']} @ ({x}, {y})")
                
                self.user32.SetCursorPos(x, y)
                time.sleep(0.05)
                self.user32.mouse_event(0x0002, 0, 0, 0, 0)
                time.sleep(0.05)
                self.user32.mouse_event(0x0004, 0, 0, 0, 0)
                return True
        
        print(f"Element not found: {label}")
        return False
    
    def list_elements(self):
        """列出所有元素"""
        print(f"\n[{len(self.elements)} elements]")
        for i, e in enumerate(self.elements):
            print(f"  {i+1}. {e['label']} @ ({e['x']}, {e['y']})")
    
    def interactive_add(self, app_name, count=5):
        """互動式新增元素"""
        print(f"\n{'='*50}")
        print(f"UI Mapper - Interactive Mode")
        print(f"{'='*50}")
        print(f"App: {app_name}")
        print(f"Steps: {count}")
        print(f"\n請將滑鼠移到目標位置，然後按 Enter 新增")
        print(f"輸入自定義標籤，或按 Enter 使用 OCR")
        print(f"輸入 's' 儲存並離開")
        print(f"輸入 'q' 離開")
        print(f"{'='*50}")
        
        for i in range(count):
            input(f"\n[{i+1}/{count}] 按 Enter 取樣位置...")
            
            # 取得滑鼠位置
            pt = wintypes.POINT()
            self.user32.GetCursorPos(ctypes.byref(pt))
            
            print(f"  位置: ({pt.x}, {pt.y})")
            
            # 詢問標籤
            label = input("  標籤 (Enter=OCR, q=離開): ").strip()
            
            if label.lower() == 'q':
                break
            if label.lower() == 's':
                self.save_map(app_name)
                break
            
            # 新增元素
            self.add_element(pt.x, pt.y, label if label else None)
        
        # 儲存
        if self.elements:
            self.save_map(app_name)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="WinAgent UI Mapper")
    parser.add_argument("--map", "-m", help="App name to map")
    parser.add_argument("--add", "-a", type=int, default=5, help="Number of elements to add")
    parser.add_argument("--click", "-c", help="Click element by label")
    parser.add_argument("--list", "-l", action="store_true", help="List elements")
    parser.add_argument("--load", help="Load existing map")
    
    args = parser.parse_args()
    
    mapper = UIMapper()
    
    if args.load:
        mapper.load_map(args.load)
        mapper.list_elements()
    
    elif args.map:
        # 檢查是否已有地圖
        if mapper.load_map(args.map):
            print("已有地圖，繼續新增...")
        
        # 互動式標記
        mapper.interactive_add(args.map, args.add)
    
    elif args.click:
        # 先載入
        app_name = args.click.split()[0] if ' ' in args.click else args.click
        if mapper.load_map(app_name):
            label = args.click.replace(app_name, '').strip() or args.click
            mapper.click_element(label)
        else:
            print(f"找不到地圖: {app_name}")
    
    elif args.list:
        mapper.list_elements()
    
    else:
        print("用法:")
        print("  --map <app>     建立/新增 UI 地圖")
        print("  --add N        新增 N 個元素")
        print("  --click <label> 點擊元素")
        print("  --list         列出元素")
        print("  --load <app>   載入地圖")
        print("")
        print("範例:")
        print("  python ui_mapper.py --map WinDbg --add 10")
        print("  python ui_mapper.py --click memory")
        print("  python ui_mapper.py --list")

if __name__ == "__main__":
    main()
