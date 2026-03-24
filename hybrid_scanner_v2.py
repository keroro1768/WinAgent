"""
WinAgent Hybrid Scanner v2 - Enhanced
Includes auto-activation and re-scan capability
"""

import subprocess
import json
import time
import ctypes
from ctypes import wintypes
from datetime import datetime
import os
import sys

try:
    import uiautomation as auto
    UIA_AVAILABLE = True
except:
    UIA_AVAILABLE = False

class HybridScanner:
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.merged = []
        
    def get_window(self, process_name):
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
            
            if process_name.lower() in cls.lower() or process_name.lower() in title.lower():
                results.append({'hwnd': hwnd, 'title': title, 'class': cls, 'pid': pid.value})
            
            return 1
        
        self.user32.EnumWindows(
            ctypes.CFUNCTYPE(wintypes.INT, wintypes.HWND, wintypes.LPARAM)(enum_callback),
            0
        )
        
        if results:
            def get_size(r):
                rect = wintypes.RECT()
                self.user32.GetWindowRect(r['hwnd'], ctypes.byref(rect))
                return (rect.right - rect.left) * (rect.bottom - rect.top)
            return max(results, key=get_size)
        return None
    
    def click_at(self, x, y):
        self.user32.SetCursorPos(int(x), int(y))
        time.sleep(0.1)
        self.user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.05)
        self.user32.mouse_event(0x0004, 0, 0, 0, 0)
    
    def activate_main_ui(self, window_info):
        """嘗試啟動主 UI"""
        print("\n[Activate] Trying to activate main UI...")
        
        # First, try clicking "Start debugging" button
        # This might open the main debugging interface
        
        # Alternative: try keyboard shortcut to open a file
        print("[Activate] Pressing Ctrl+O to open file...")
        
        hwnd = window_info['hwnd']
        self.user32.SetForegroundWindow(hwnd)
        time.sleep(0.2)
        
        # Send Ctrl+O
        self.user32.keybd_event(0x11, 0, 0, 0)  # Ctrl down
        time.sleep(0.05)
        self.user32.keybd_event(0x4F, 0, 0, 0)  # O down
        time.sleep(0.05)
        self.user32.keybd_event(0x4F, 0, 2, 0)  # O up
        time.sleep(0.05)
        self.user32.keybd_event(0x11, 0, 2, 0)  # Ctrl up
        
        time.sleep(1)
        
        # Check if window changed
        new_window = self.get_window(window_info['class'].split('[')[0])
        if new_window:
            return new_window
        
        return window_info
    
    def scan_ocr(self, window_info):
        """OCR 掃描"""
        hwnd = window_info['hwnd']
        
        rect = wintypes.RECT()
        self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        
        x, y = rect.left, rect.top
        
        ocr_cmd = [
            "dotnet", "run", "--project",
            "D:/Project/WinAgent/WinAgentOCR/WinAgentOCR.csproj",
            hex(hwnd)
        ]
        
        result = subprocess.run(
            ocr_cmd, capture_output=True, encoding='utf-8', errors='ignore',
            cwd="D:/Project/WinAgent/WinAgentOCR"
        )
        
        elements = []
        
        # Keywords
        tab_keywords = ['home', 'view', 'breakpoints', 'time travel', 'model', 'scripting',
                       'source', 'memory', 'extensions', 'file', 'document', 'note', 'command',
                       '文件', '檢視', '中斷點']
        
        button_keywords = ['go', 'step', 'break', 'stop', 'run', 'start', 'restart', 'detach',
                          'settings', 'help', 'save', 'open', 'close', 'ok', 'cancel', 'debug', 
                          'continue', 'pause', 'flow', 'reverse', 'preferences', 'assembly']
        
        for line in result.stdout.split('\n'):
            if '@' in line and '(' in line:
                try:
                    parts = line.split('@')
                    name = parts[0].strip()
                    coords = parts[1].strip('() \n').split(',')
                    
                    if len(coords) >= 2:
                        ex = int(coords[0]) + x
                        ey = int(coords[1]) + y
                        
                        name_clean = name.lower().replace(' ', '')
                        
                        elem_type = 'text'
                        if any(kw in name_clean for kw in [k.lower().replace(' ', '') for kw in tab_keywords]):
                            elem_type = 'tab'
                        elif any(kw in name_clean for kw in [k.lower().replace(' ', '') for kw in button_keywords]):
                            elem_type = 'button'
                        
                        elements.append({
                            'name': name,
                            'x': ex,
                            'y': ey,
                            'type': elem_type,
                            'method': 'ocr'
                        })
                except:
                    pass
        
        return elements
    
    def scan_uia(self, window_info):
        """UIA 掃描"""
        if not UIA_AVAILABLE:
            return []
        
        try:
            w = auto.WindowControl(ProcessId=window_info['pid'])
            if not w.Exists(2):
                return []
            
            elements = []
            
            def walk(ctrl, depth=0):
                if depth > 5:
                    return
                try:
                    name = (ctrl.Name or ctrl.AutomationId or '')[:40]
                    ctype = str(ctrl.ControlTypeName)
                    
                    rect = ctrl.BoundingRectangle
                    bounds = {}
                    if rect and rect.width > 0:
                        bounds = {'x': rect.left, 'y': rect.top, 'w': rect.width, 'h': rect.height}
                    
                    elements.append({
                        'name': name,
                        'type': ctype,
                        'bounds': bounds,
                        'method': 'uia'
                    })
                except:
                    pass
                
                try:
                    for child in list(ctrl.GetChildren())[:30]:
                        walk(child, depth + 1)
                except:
                    pass
            
            walk(w)
            return elements
        except:
            return []
    
    def full_scan(self, process_name, auto_activate=True):
        """完整掃描流程"""
        print("="*60)
        print("WinAgent Hybrid Scanner v2")
        print("="*60)
        
        # Find window
        window = self.get_window(process_name)
        if not window:
            print(f"ERROR: Window not found: {process_name}")
            return
        
        print(f"\n[1] Window: {window['title']}")
        print(f"    PID: {window['pid']}")
        
        # Initial scan
        print(f"\n[2] Initial OCR scan...")
        ocr_elements = self.scan_ocr(window)
        print(f"    Found {len(ocr_elements)} elements")
        
        # Try to activate main UI if we're on start page
        if auto_activate:
            # Check if we're on start page (few elements)
            if len(ocr_elements) < 10:
                window = self.activate_main_ui(window)
                
                # Rescan
                print(f"\n[3] Re-scan after activation...")
                ocr_elements = self.scan_ocr(window)
                print(f"    Found {len(ocr_elements)} elements")
        
        # Also try UIA
        print(f"\n[4] UIA scan...")
        uia_elements = self.scan_uia(window)
        print(f"    Found {len(uia_elements)} elements")
        
        # Merge and display
        self.merged = ocr_elements + uia_elements
        
        print("\n" + "="*60)
        print("RESULTS")
        print("="*60)
        
        # Tabs
        tabs = [e for e in self.merged if e.get('type') == 'tab']
        if tabs:
            print(f"\n[TABS] ({len(tabs)}):")
            for t in tabs[:15]:
                pos = f"@({t['x']},{t['y']})" if 'x' in t else ""
                print(f"  {t['name'][:25]:<25} {pos}")
        
        # Buttons
        buttons = [e for e in self.merged if 'button' in e.get('type', '').lower()]
        if buttons:
            print(f"\n[BUTTONS] ({len(buttons)}):")
            for b in buttons[:20]:
                pos = f"@({b['x']},{b['y']})" if 'x' in b else ""
                print(f"  {b['name'][:25]:<25} {pos}")
        
        # Save
        filename = f"hybrid_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = f"D:/Project/WinAgent/scans/{filename}"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'scanned_at': datetime.now().isoformat(),
                'window': window,
                'elements': self.merged
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n[Saved] {filepath}")
        
        return self.merged
    
    def click_element(self, name):
        """點擊元素"""
        name_lower = name.lower()
        
        for elem in self.merged:
            elem_name = elem.get('name', '').lower()
            if name_lower in elem_name or elem_name in name_lower:
                x = elem.get('x') or elem.get('bounds', {}).get('x')
                y = elem.get('y') or elem.get('bounds', {}).get('y')
                
                if x and y:
                    print(f"Clicking: {elem['name']} @ ({x}, {y})")
                    self.click_at(x, y)
                    return True
        
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--scan", "-s", help="Scan application")
    parser.add_argument("--click", "-c", help="Click element")
    parser.add_argument("--process", "-p", default="DbgX")
    parser.add_argument("--no-activate", action="store_true", help="Skip auto-activation")
    
    args = parser.parse_args()
    
    scanner = HybridScanner()
    
    if args.scan:
        scanner.full_scan(args.scan or args.process, auto_activate=not args.no_activate)
    
    elif args.click:
        scanner.full_scan(args.process, auto_activate=not args.no_activate)
        scanner.click_element(args.click)
    
    else:
        print("Usage:")
        print("  --scan <name>        Scan app")
        print("  --click <element>   Click element")
        print("  --no-activate       Skip auto-activation")
