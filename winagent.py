"""
WinAgent Complete UI Automation System
整合 UIA + OCR + 自動化流程
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
    UIA = True
except:
    UIA = False

class WinAgent:
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.elements = []
        self.window = None
        
    # ========== Window Control ==========
    def find_window(self, name):
        """尋找視窗"""
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
                    'hwnd': hwnd,
                    'title': title,
                    'class': cls_buff.value,
                    'pid': pid.value,
                    'size': w * h
                })
            return 1
        
        self.user32.EnumWindows(
            ctypes.CFUNCTYPE(wintypes.INT, wintypes.HWND, wintypes.LPARAM)(cb), 0
        )
        
        if results:
            self.window = max(results, key=lambda x: x['size'])
            return self.window
        return None
    
    # ========== OCR ==========
    def ocr_scan(self, hwnd=None):
        """OCR 掃描"""
        if hwnd is None:
            hwnd = self.window['hwnd']
        
        rect = wintypes.RECT()
        self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
        
        cmd = [
            "dotnet", "run", "--project",
            "D:/Project/WinAgent/WinAgentOCR/WinAgentOCR.csproj",
            hex(hwnd)
        ]
        
        result = subprocess.run(
            cmd, capture_output=True, encoding='utf-8', errors='ignore',
            cwd="D:/Project/WinAgent/WinAgentOCR"
        )
        
        elements = []
        
        for line in (result.stdout or '').split('\n'):
            if '@' in line and '(' in line:
                try:
                    parts = line.split('@')
                    name = parts[0].strip()
                    coords = parts[1].strip('() \n').split(',')
                    
                    if len(coords) >= 2:
                        x = int(coords[0]) + rect.left
                        y = int(coords[1]) + rect.top
                        
                        # Categorize
                        name_l = name.lower()
                        e_type = 'text'
                        if any(k in name_l for k in ['home','view','break','memory','source','script','model','ext','file','doc','note','command']):
                            e_type = 'tab'
                        elif any(k in name_l for k in ['go','step','run','start','stop','save','open','help','settings']):
                            e_type = 'button'
                        
                        elements.append({
                            'name': name,
                            'x': x,
                            'y': y,
                            'type': e_type,
                            'method': 'ocr'
                        })
                except:
                    pass
        
        return elements
    
    # ========== UIA ==========
    def uia_scan(self, pid):
        """UIA 掃描"""
        if not UIA:
            return []
        
        try:
            w = auto.WindowControl(ProcessId=pid)
            if not w.Exists(1):
                return []
            
            elements = []
            
            def walk(ctrl, d=0):
                if d > 5: return
                try:
                    name = (ctrl.Name or ctrl.AutomationId or '')[:40]
                    ctype = str(ctrl.ControlTypeName)
                    
                    rect = ctrl.BoundingRectangle
                    bounds = {}
                    if rect and rect.width > 0:
                        bounds = {'x': rect.left, 'y': rect.top, 'w': rect.width}
                    
                    elements.append({
                        'name': name,
                        'type': ctype,
                        'bounds': bounds,
                        'method': 'uia'
                    })
                except: pass
                
                try:
                    for c in list(ctrl.GetChildren())[:30]:
                        walk(c, d+1)
                except: pass
            
            walk(w)
            return elements
        except:
            return []
    
    # ========== Hybrid Scan ==========
    def scan(self, app_name):
        """完整掃描"""
        print(f"\n{'='*50}")
        print(f"WinAgent Scanner - {app_name}")
        print(f"{'='*50}")
        
        # Find window
        win = self.find_window(app_name)
        if not win:
            print(f"Window not found: {app_name}")
            return None
        
        self.window = win
        print(f"\nWindow: {win['title']}")
        print(f"PID: {win['pid']}")
        
        # UIA scan
        print("\n[UIA Scan]")
        uia_elements = self.uia_scan(win['pid'])
        print(f"  Found: {len(uia_elements)} elements")
        
        # OCR scan  
        print("\n[OCR Scan]")
        ocr_elements = self.ocr_scan()
        print(f"  Found: {len(ocr_elements)} elements")
        
        # Merge
        self.elements = uia_elements + ocr_elements
        
        # Display
        print(f"\n{'='*50}")
        print(f"Total: {len(self.elements)} elements")
        
        tabs = [e for e in self.elements if e.get('type') in ['tab', 'TabControl']]
        buttons = [e for e in self.elements if 'button' in e.get('type', '').lower()]
        
        if tabs:
            print(f"\n[TABS] ({len(tabs)}):")
            for t in tabs[:10]:
                pos = f"@({t.get('x',0)},{t.get('y',0)})" if 'x' in t else ""
                print(f"  {t['name'][:25]} {pos}")
        
        if buttons:
            print(f"\n[BUTTONS] ({len(buttons)}):")
            for b in buttons[:15]:
                pos = f"@({b.get('x',0)},{b.get('y',0)})" if 'x' in b else ""
                print(f"  {b['name'][:25]} {pos}")
        
        return self.elements
    
    # ========== Actions ==========
    def click_at(self, x, y):
        """點擊"""
        self.user32.SetCursorPos(int(x), int(y))
        time.sleep(0.05)
        self.user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.05)
        self.user32.mouse_event(0x0004, 0, 0, 0, 0)
    
    def click(self, name):
        """點擊元素"""
        name_l = name.lower()
        
        for e in self.elements:
            if name_l in e.get('name', '').lower():
                x = e.get('x') or e.get('bounds', {}).get('x')
                y = e.get('y') or e.get('bounds', {}).get('y')
                
                if x and y:
                    print(f"\nClicking: {e['name']} @ ({x}, {y})")
                    self.click_at(x, y)
                    return True
        
        print(f"\nElement not found: {name}")
        return False
    
    def send_keys(self, keys):
        """發送鍵盤"""
        import uiautomation as auto
        auto.SendKeys(keys)
    
    def open_file(self, filepath):
        """開啟檔案"""
        # Find the window
        win = self.find_window("")
        if not win:
            return
        
        # Send Ctrl+O
        self.send_keys("^o")
        time.sleep(1)
        
        # Type filepath
        self.send_keys(filepath)
        time.sleep(0.3)
        
        # Press Enter
        self.send_keys("{ENTER}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="WinAgent UI Automation")
    parser.add_argument("--scan", "-s", help="Scan app")
    parser.add_argument("--click", "-c", help="Click element")
    parser.add_argument("--app", "-a", default="DbgX", help="App name")
    
    args = parser.parse_args()
    
    agent = WinAgent()
    
    if args.scan:
        agent.scan(args.scan or args.app)
    
    elif args.click:
        agent.scan(args.app)
        agent.click(args.click)
    
    else:
        print("Usage:")
        print("  --scan <app>    Scan application")
        print("  --click <name> Click element")

if __name__ == "__main__":
    main()
