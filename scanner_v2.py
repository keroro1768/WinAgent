"""
WinAgent Universal UI Scanner v2
結合 OCR + 座標映射，掃描並操控任何 WPF/Win32 應用程式
"""

import subprocess
import json
import time
import ctypes
from ctypes import wintypes
from datetime import datetime
import os
import re

class WinAgentUIScanner:
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.elements = []  # 所有找到的 UI 元素
        self.tabs = {}       # 分頁元素
        self.buttons = {}    # 按鈕元素
        self.all_text = []   # 所有文字元素
        
    def get_window_by_process(self, process_name_substring):
        """透過程序名稱取得視窗"""
        results = []
        
        def enum_callback(hwnd, lParam):
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
            cls = cls_buff.value
            
            if process_name_substring.lower() in cls.lower() or process_name_substring.lower() in title.lower():
                results.append({'hwnd': hwnd, 'title': title, 'class': cls, 'pid': pid.value})
            
            return 1
        
        CMPFUNC = ctypes.CFUNCTYPE(wintypes.INT, wintypes.HWND, wintypes.LPARAM)
        self.user32.EnumWindows(CMPFUNC(enum_callback), 0)
        
        if results:
            def get_size(r):
                rect = wintypes.RECT()
                self.user32.GetWindowRect(r['hwnd'], ctypes.byref(rect))
                return (rect.right - rect.left) * (rect.bottom - rect.top)
            return max(results, key=get_size)
        return None
    
    def capture_window(self, hwnd):
        """截圖並 OCR 識別"""
        rect = wintypes.RECT()
        self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        
        x, y = rect.left, rect.top
        w, h = rect.right - rect.left, rect.bottom - rect.top
        
        print(f"Window: ({x}, {y}) {w}x{h}")
        
        # Run OCR
        ocr_cmd = ["dotnet", "run", "--project", "D:/Project/WinAgent/WinAgentOCR/WinAgentOCR.csproj", hex(hwnd)]
        result = subprocess.run(ocr_cmd, capture_output=True, text=True, cwd="D:/Project/WinAgent/WinAgentOCR")
        
        # Parse ALL OCR output more aggressively
        self._parse_all_text(result.stdout, x, y)
        
        return self.all_text
    
    def _parse_all_text(self, output, offset_x, offset_y):
        """解析所有 OCR 文字"""
        self.elements = []
        self.tabs = {}
        self.buttons = {}
        self.all_text = []
        
        lines = output.split('\n')
        
        # Keywords for categorization
        tab_keywords = ['home', 'view', 'breakpoints', 'time travel', 'model', 'scripting', 
                       'source', 'memory', 'extensions', 'file', 'document', 'note', 'command', 
                       '文件', '檢視', '中斷點', '來源']
        
        button_keywords = ['go', 'step', 'break', 'stop', 'run', 'start', 'restart', 'detach', 
                          'settings', 'help', 'save', 'open', 'close', 'ok', 'cancel', 'yes', 'no',
                          'debug', 'continue', 'pause', 'flow', 'reverse', 'preferences', 'assembly']
        
        for line in lines:
            if '@' in line and '(' in line:
                try:
                    parts = line.split('@')
                    name = parts[0].strip()
                    coords = parts[1].strip('() \n').split(',')
                    
                    if len(coords) >= 2:
                        x = int(coords[0]) + offset_x
                        y = int(coords[1]) + offset_y
                        
                        name_clean = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]', '', name).lower()
                        
                        element = {
                            'name': name,
                            'x': x,
                            'y': y,
                            'type': 'text'
                        }
                        
                        self.all_text.append(element)
                        
                        # Categorize - check if any keyword matches
                        is_tab = any(kw in name_clean for kw in [k.lower().replace(' ', '') for kw in tab_keywords])
                        is_button = any(kw in name_clean for kw in [k.lower().replace(' ', '') for kw in button_keywords])
                        
                        if is_tab:
                            element['type'] = 'tab'
                            # Use clean name as key
                            key = name_clean[:15]
                            if key not in self.tabs:
                                self.tabs[key] = element
                        elif is_button:
                            element['type'] = 'button'
                            key = name_clean[:15]
                            if key not in self.buttons:
                                self.buttons[key] = element
                        
                        self.elements.append(element)
                        
                except:
                    pass
    
    def click_at(self, x, y):
        """點擊座標"""
        self.user32.SetCursorPos(x, y)
        time.sleep(0.05)
        self.user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.05)
        self.user32.mouse_event(0x0004, 0, 0, 0, 0)
    
    def find_and_click(self, name):
        """根據名稱尋找並點擊"""
        name_clean = re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]', '', name).lower()
        
        # Try exact match in tabs
        for key, tab in self.tabs.items():
            if name_clean in key or key in name_clean:
                print(f"Clicking TAB: {tab['name']} @ ({tab['x']}, {tab['y']})")
                self.click_at(tab['x'], tab['y'])
                return True
        
        # Try buttons
        for key, btn in self.buttons.items():
            if name_clean in key or key in name_clean:
                print(f"Clicking BUTTON: {btn['name']} @ ({btn['x']}, {btn['y']})")
                self.click_at(btn['x'], btn['y'])
                return True
        
        # Try all elements
        for elem in self.all_text:
            if name_clean in re.sub(r'[^a-zA-Z0-9\u4e00-\u9fff]', '', elem['name']).lower():
                print(f"Clicking: {elem['name']} @ ({elem['x']}, {elem['y']})")
                self.click_at(elem['x'], elem['y'])
                return True
        
        return False
    
    def scan_and_print(self, process_name):
        """掃描並顯示"""
        window = self.get_window_by_process(process_name)
        
        if not window:
            print(f"Window not found: {process_name}")
            return
        
        print(f"\nWindow: {window['title']}")
        print(f"Class: {window['class']}")
        print(f"HWND: {hex(window['hwnd'])}\n")
        
        print("Running OCR scan...")
        self.capture_window(window['hwnd'])
        
        print("\n" + "="*60)
        print(f"Total elements: {len(self.all_text)}")
        print("="*60)
        
        if self.tabs:
            print(f"\n[TABS] ({len(self.tabs)}):")
            for key, tab in self.tabs.items():
                print(f"  {tab['name']:<25} @ ({tab['x']}, {tab['y']})")
        
        if self.buttons:
            print(f"\n[BUTTONS] ({len(self.buttons)}):")
            for key, btn in list(self.buttons.items())[:25]:
                print(f"  {btn['name']:<25} @ ({btn['x']}, {btn['y']})")
        
        # Show all text elements in top area (likely UI)
        top_elements = [e for e in self.all_text if e['y'] < 300]
        if top_elements:
            print(f"\n[ALL UI ELEMENTS (y<300)] ({len(top_elements)}):")
            for e in top_elements[:30]:
                print(f"  {e['name'][:30]:<30} @ ({e['x']}, {e['y']})")
        
        self.save_to_file()
        
        return self.all_text
    
    def save_to_file(self, filename=None):
        """儲存結果"""
        if not filename:
            filename = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            'scanned_at': datetime.now().isoformat(),
            'total': len(self.all_text),
            'tabs': self.tabs,
            'buttons': self.buttons,
            'all': self.all_text
        }
        
        filepath = f"D:/Project/WinAgent/scans/{filename}"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n[Saved] {filepath}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="WinAgent UI Scanner")
    parser.add_argument("--scan", "-s", help="Scan app")
    parser.add_argument("--click", "-c", help="Click element")
    parser.add_argument("--process", "-p", default="DbgX", help="Process name")
    
    args = parser.parse_args()
    
    scanner = WinAgentUIScanner()
    
    if args.scan:
        scanner.scan_and_print(args.scan or args.process)
    
    elif args.click:
        scanner.scan_and_print(args.process)
        print(f"\nTrying to click: {args.click}")
        if not scanner.find_and_click(args.click):
            print("Element not found")
    
    else:
        print("Usage:")
        print("  --scan <name>   Scan application")
        print("  --click <name>  Click element")

if __name__ == "__main__":
    main()
