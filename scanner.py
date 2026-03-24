"""
WinAgent Universal UI Scanner
結合 OCR + 座標映射，掃描並操控任何 WPF/Win32 應用程式
"""

import subprocess
import json
import time
import ctypes
from ctypes import wintypes
from datetime import datetime
import os

class WinAgentUIScanner:
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.elements = []  # 所有找到的 UI 元素
        self.tabs = {}       # 分頁元素
        self.buttons = {}    # 按鈕元素
        self.menus = {}     # 選單元素
        
    def get_window_by_process(self, process_name_substring):
        """透過程序名稱取得視窗"""
        results = []
        
        def enum_callback(hwnd, lParam):
            # Get process ID
            pid = wintypes.DWORD()
            self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            
            # Get window title
            length = self.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value
            else:
                title = ""
            
            # Get class name
            cls_buff = ctypes.create_unicode_buffer(256)
            self.user32.GetClassNameW(hwnd, cls_buff, 256)
            cls = cls_buff.value
            
            # Check if matches
            if process_name_substring.lower() in cls.lower() or process_name_substring.lower() in title.lower():
                results.append({
                    'hwnd': hwnd,
                    'title': title,
                    'class': cls,
                    'pid': pid.value
                })
            
            return 1
        
        CMPFUNC = ctypes.CFUNCTYPE(wintypes.INT, wintypes.HWND, wintypes.LPARAM)
        self.user32.EnumWindows(CMPFUNC(enum_callback), 0)
        
        # Return the main window (largest one)
        if results:
            main = max(results, key=lambda r: self._get_window_size(r['hwnd']))
            return main
        return None
    
    def _get_window_size(self, hwnd):
        """取得視窗大小"""
        rect = wintypes.RECT()
        self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return (rect.right - rect.left) * (rect.bottom - rect.top)
    
    def capture_window(self, hwnd):
        """截圖並 OCR 識別"""
        rect = wintypes.RECT()
        self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        
        x, y = rect.left, rect.top
        w, h = rect.right - rect.left, rect.bottom - rect.top
        
        print(f"Window: ({x}, {y}) {w}x{h}")
        
        # Build OCR command
        ocr_cmd = [
            "dotnet", "run", "--project", 
            "D:/Project/WinAgent/WinAgentOCR/WinAgentOCR.csproj",
            hex(hwnd)
        ]
        
        result = subprocess.run(ocr_cmd, capture_output=True, text=True, cwd="D:/Project/WinAgent/WinAgentOCR")
        
        # Parse OCR results
        self._parse_ocr_output(result.stdout, x, y)
        
        return self.elements
    
    def _parse_ocr_output(self, output, offset_x, offset_y):
        """解析 OCR 輸出"""
        self.elements = []
        self.tabs = {}
        self.buttons = {}
        
        lines = output.split('\n')
        
        for line in lines:
            if '@' in line and '(' in line:
                try:
                    # Extract name and position
                    parts = line.split('@')
                    name = parts[0].strip()
                    coords = parts[1].strip('() \n').split(',')
                    
                    if len(coords) >= 2:
                        x = int(coords[0]) + offset_x
                        y = int(coords[1]) + offset_y
                        
                        # Normalize name
                        name_lower = name.lower().replace(' ', '')
                        
                        element = {
                            'name': name,
                            'x': x,
                            'y': y,
                            'type': 'unknown'
                        }
                        
                        # Categorize
                        tab_keywords = ['home', 'view', 'break', 'time', 'model', 'script', 'source', 'memory', 'ext', 'file', 'doc', 'note', 'command']
                        button_keywords = ['go', 'step', 'break', 'stop', 'run', 'start', 'restart', 'detach', 'settings', 'help', 'save', 'open', 'close', 'ok', 'cancel', 'yes', 'no']
                        
                        is_tab = any(kw in name_lower for kw in tab_keywords)
                        is_button = any(kw in name_lower for kw in button_keywords)
                        
                        if is_tab:
                            element['type'] = 'tab'
                            # Clean name for key
                            key = name_lower.replace(' ', '')
                            self.tabs[key] = element
                        elif is_button:
                            element['type'] = 'button'
                            self.buttons[name_lower] = element
                        
                        self.elements.append(element)
                        
                except Exception as e:
                    pass
    
    def click_at(self, x, y):
        """點擊座標"""
        self.user32.SetCursorPos(x, y)
        time.sleep(0.05)
        self.user32.mouse_event(0x0002, 0, 0, 0, 0)  # Down
        time.sleep(0.05)
        self.user32.mouse_event(0x0004, 0, 0, 0, 0)  # Up
    
    def find_and_click(self, name):
        """根據名稱尋找並點擊元素"""
        name_lower = name.lower()
        
        # Try tabs first
        for key, tab in self.tabs.items():
            if name_lower in key or key in name_lower:
                print(f"點擊分頁: {tab['name']} @ ({tab['x']}, {tab['y']})")
                self.click_at(tab['x'], tab['y'])
                return True
        
        # Try buttons
        for key, btn in self.buttons.items():
            if name_lower in key or key in name_lower:
                print(f"點擊按鈕: {btn['name']} @ ({btn['x']}, {btn['y']})")
                self.click_at(btn['x'], btn['y'])
                return True
        
        # Try all elements
        for elem in self.elements:
            if name_lower in elem['name'].lower():
                print(f"點擊元素: {elem['name']} @ ({elem['x']}, {elem['y']})")
                self.click_at(elem['x'], elem['y'])
                return True
        
        return False
    
    def scan_and_print(self, process_name):
        """掃描並顯示所有元素"""
        # Find window
        window = self.get_window_by_process(process_name)
        
        if not window:
            print(f"找不到視窗: {process_name}")
            return
        
        print(f"\n找到視窗: {window['title']}")
        print(f"Class: {window['class']}")
        print(f"HWND: {hex(window['hwnd'])}\n")
        
        # Capture and OCR
        print("執行 OCR 掃描...")
        self.capture_window(window['hwnd'])
        
        # Display results
        print("\n" + "="*50)
        print(f"總共找到 {len(self.elements)} 個 UI 元素")
        print("="*50)
        
        if self.tabs:
            print(f"\n[TABS] ({len(self.tabs)}):")
            for key, tab in self.tabs.items():
                print(f"  {tab['name']:<20} @ ({tab['x']}, {tab['y']})")
        
        if self.buttons:
            print(f"\n[BUTTONS] ({len(self.buttons)}):")
            for key, btn in list(self.buttons.items())[:20]:
                print(f"  {btn['name']:<20} @ ({btn['x']}, {btn['y']})")
        
        # Save to file
        self.save_to_file()
        
        return self.elements
    
    def save_to_file(self, filename=None):
        """儲存掃描結果"""
        if not filename:
            filename = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            'scanned_at': datetime.now().isoformat(),
            'total_elements': len(self.elements),
            'tabs': self.tabs,
            'buttons': self.buttons,
            'all_elements': self.elements
        }
        
        filepath = f"D:/Project/WinAgent/scans/{filename}"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n[Saved] {filepath}")
        return filepath


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="WinAgent Universal UI Scanner")
    parser.add_argument("--scan", "-s", help="掃描應用程式")
    parser.add_argument("--click", "-c", help="點擊元素")
    parser.add_argument("--list", "-l", action="store_true", help="顯示最後掃描結果")
    parser.add_argument("--process", "-p", default="DbgX.Shell", help="程序名稱")
    
    args = parser.parse_args()
    
    scanner = WinAgentUIScanner()
    
    if args.scan:
        scanner.scan_and_print(args.scan or args.process)
    
    elif args.click:
        # 需要先掃描
        scanner.scan_and_print(args.process)
        print(f"\n嘗試點擊: {args.click}")
        scanner.find_and_click(args.click)
    
    elif args.list:
        # Show latest scan
        scans_dir = "D:/Project/WinAgent/scans"
        if os.path.exists(scans_dir):
            files = sorted(os.listdir(scans_dir), reverse=True)
            if files:
                with open(os.path.join(scans_dir, files[0]), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    print("最後掃描結果:")
                    print(f"  時間: {data.get('scanned_at', 'N/A')}")
                    print(f"  元素數: {data.get('total_elements', 0)}")
                    print(f"  分頁: {len(data.get('tabs', {}))}")
                    print(f"  按鈕: {len(data.get('buttons', {}))}")
    
    else:
        print("用法:")
        print("  --scan <程序名>      掃描應用程式")
        print("  --click <名稱>      點擊元素")
        print("  --list              顯示最後掃描")
        print("")
        print("範例:")
        print("  python scanner.py --scan DbgX")
        print("  python scanner.py --click memory")
        print("  python scanner.py --list")

if __name__ == "__main__":
    main()
