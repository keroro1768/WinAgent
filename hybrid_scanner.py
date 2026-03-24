"""
WinAgent Hybrid Scanner - UIA + OCR 混合掃描系統
當 UIA 可用時使用 UIA，不可用時使用 OCR
"""

import subprocess
import json
import time
import ctypes
from ctypes import wintypes
from datetime import datetime
import os
import sys

# Try to import uiautomation
try:
    import uiautomation as auto
    UIA_AVAILABLE = True
except:
    UIA_AVAILABLE = False
    print("UIAutomation not available, will use OCR only")

class HybridScanner:
    def __init__(self):
        self.user32 = ctypes.windll.user32
        self.elements = []
        self.tabs = {}
        self.buttons = {}
        self.menus = {}
        self.uia_elements = []
        self.ocr_elements = []
        
    def get_window(self, process_name_substring):
        """取得目標視窗"""
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
    
    # ========== UIAutomation Method ==========
    def scan_uia(self, window_info):
        """使用 UIAutomation 掃描"""
        if not UIA_AVAILABLE:
            return {"status": "unavailable", "reason": "UIA not installed"}
        
        try:
            # Get window by PID
            pid = window_info['pid']
            w = auto.WindowControl(ProcessId=pid)
            
            if not w.Exists(2):
                return {"status": "error", "reason": "Window not found"}
            
            elements = []
            
            def walk(ctrl, depth=0):
                if depth > 6:
                    return
                try:
                    name = (ctrl.Name or ctrl.AutomationId or '')[:50]
                    ctype = str(ctrl.ControlTypeName)
                    
                    rect = ctrl.BoundingRectangle
                    bounds = {}
                    if rect and rect.width > 0:
                        bounds = {'x': rect.left, 'y': rect.top, 'w': rect.width, 'h': rect.height}
                    
                    elements.append({
                        'depth': depth,
                        'type': ctype,
                        'name': name,
                        'bounds': bounds,
                        'method': 'uia'
                    })
                except:
                    pass
                
                try:
                    for child in list(ctrl.GetChildren())[:50]:
                        walk(child, depth + 1)
                except:
                    pass
            
            walk(w)
            
            # Categorize
            tabs = [e for e in elements if 'Tab' in e['type']]
            buttons = [e for e in elements if 'Button' in e['type']]
            
            return {
                "status": "success",
                "total": len(elements),
                "tabs": tabs,
                "buttons": buttons,
                "all": elements
            }
            
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    # ========== OCR Method ==========
    def scan_ocr(self, window_info):
        """使用 OCR 掃描"""
        try:
            hwnd = window_info['hwnd']
            
            rect = wintypes.RECT()
            self.user32.GetWindowRect(hwnd, ctypes.byref(rect))
            
            x, y = rect.left, rect.top
            w, h = rect.right - rect.left, rect.bottom - rect.top
            
            # Run OCR
            ocr_cmd = [
                "dotnet", "run", "--project",
                "D:/Project/WinAgent/WinAgentOCR/WinAgentOCR.csproj",
                hex(hwnd)
            ]
            
            result = subprocess.run(
                ocr_cmd,
                capture_output=True,
                text=True,
                cwd="D:/Project/WinAgent/WinAgentOCR"
            )
            
            # Parse OCR output
            elements = []
            lines = result.stdout.split('\n')
            
            tab_keywords = ['home', 'view', 'break', 'time travel', 'model', 'scripting',
                          'source', 'memory', 'extensions', 'file', 'document', 'note', 'command', '文件']
            button_keywords = ['go', 'step', 'break', 'stop', 'run', 'start', 'restart', 'detach',
                            'settings', 'help', 'save', 'open', 'close', 'ok', 'cancel', 'debug', 'continue']
            
            for line in lines:
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
                            if any(kw in name_clean for kw in tab_keywords):
                                elem_type = 'tab'
                            elif any(kw in name_clean for kw in button_keywords):
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
            
            return {
                "status": "success",
                "total": len(elements),
                "tabs": [e for e in elements if e['type'] == 'tab'],
                "buttons": [e for e in elements if e['type'] == 'button'],
                "all": elements
            }
            
        except Exception as e:
            return {"status": "error", "reason": str(e)}
    
    # ========== Hybrid Scan ==========
    def scan_hybrid(self, process_name):
        """執行混合掃描"""
        print("="*60)
        print("WinAgent Hybrid Scanner")
        print("="*60)
        
        # Step 1: Find window
        print(f"\n[1] Finding window: {process_name}")
        window = self.get_window(process_name)
        
        if not window:
            print(f"   ERROR: Window not found")
            return None
        
        print(f"   Found: {window['title']}")
        print(f"   Class: {window['class']}")
        print(f"   PID: {window['pid']}")
        
        results = {
            "window": window,
            "uia": None,
            "ocr": None,
            "merged": []
        }
        
        # Step 2: Try UIAutomation
        print(f"\n[2] Scanning with UIAutomation...")
        uia_result = self.scan_uia(window)
        
        if uia_result["status"] == "success":
            print(f"   SUCCESS: Found {uia_result['total']} elements")
            print(f"   Tabs: {len(uia_result['tabs'])}, Buttons: {len(uia_result['buttons'])}")
            results["uia"] = uia_result
            
            # Add to merged
            for e in uia_result.get("all", [])[:50]:
                results["merged"].append(e)
        else:
            print(f"   FAILED: {uia_result.get('reason', 'Unknown')}")
        
        # Step 3: Try OCR
        print(f"\n[3] Scanning with OCR...")
        ocr_result = self.scan_ocr(window)
        
        if ocr_result["status"] == "success":
            print(f"   SUCCESS: Found {ocr_result['total']} elements")
            results["ocr"] = ocr_result
            
            # Add OCR elements not found by UIA
            results["merged"].extend(ocr_result.get("all", [])[:30])
        else:
            print(f"   FAILED: {ocr_result.get('reason', 'Unknown')}")
        
        # Step 4: Display results
        print(f"\n[4] Results Summary")
        print("="*60)
        
        # Categorize merged results
        tabs = [e for e in results["merged"] if e.get('type') in ['tab', 'TabControl', 'TabItemControl']]
        buttons = [e for e in results["merged"] if 'button' in e.get('type', '').lower()]
        
        print(f"\n[UIA Tabs] ({len(uia_result.get('tabs', [])) if uia_result and uia_result['status'] == 'success' else 0}):")
        for t in uia_result.get('tabs', [])[:10]:
            print(f"   {t['name'][:30]}")
        
        print(f"\n[OCR Tabs] ({len([e for e in ocr_result.get('tabs', [])])}):")
        for t in ocr_result.get('tabs', [])[:10]:
            print(f"   {t['name'][:30]}")
        
        # Buttons
        if buttons:
            print(f"\n[BUTTONS] ({len(buttons)}):")
            for b in buttons[:15]:
                method = b.get('method', '?')
                pos = f"@({b.get('x', 0)}, {b.get('y', 0)})" if 'x' in b else ""
                print(f"   [{method}] {b.get('name', '?')[:25]} {pos}")
        
        # Save
        self.save_results(results)
        
        return results
    
    def save_results(self, results):
        """儲存結果"""
        filename = f"hybrid_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = f"D:/Project/WinAgent/scans/{filename}"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Clean for JSON
        clean_results = {
            "scanned_at": datetime.now().isoformat(),
            "window": results.get("window", {}),
            "uia": {
                "status": results.get("uia", {}).get("status"),
                "total": results.get("uia", {}).get("total", 0)
            },
            "ocr": {
                "status": results.get("ocr", {}).get("status"),
                "total": results.get("ocr", {}).get("total", 0)
            },
            "merged_count": len(results.get("merged", []))
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(clean_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n[Saved] {filepath}")
    
    def click_element(self, name):
        """點擊元素"""
        # Find in merged results
        for elem in self.merged:
            if name.lower() in elem.get('name', '').lower():
                x = elem.get('x') or elem.get('bounds', {}).get('x')
                y = elem.get('y') or elem.get('bounds', {}).get('y')
                
                if x and y:
                    print(f"Clicking: {elem.get('name')} @ ({x}, {y})")
                    self.click_at(x, y)
                    return True
        
        return False
    
    def click_at(self, x, y):
        """執行點擊"""
        self.user32.SetCursorPos(int(x), int(y))
        time.sleep(0.05)
        self.user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.05)
        self.user32.mouse_event(0x0004, 0, 0, 0, 0)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="WinAgent Hybrid Scanner")
    parser.add_argument("--scan", "-s", help="Scan application")
    parser.add_argument("--click", "-c", help="Click element")
    parser.add_argument("--process", "-p", default="DbgX", help="Process name")
    parser.add_argument("--uia-only", action="store_true", help="Use UIA only")
    parser.add_argument("--ocr-only", action="store_true", help="Use OCR only")
    
    args = parser.parse_args()
    
    scanner = HybridScanner()
    
    if args.scan:
        results = scanner.scan_hybrid(args.scan or args.process)
    
    elif args.click:
        results = scanner.scan_hybrid(args.process)
        if results:
            scanner.merged = results.get("merged", [])
            if not scanner.click_element(args.click):
                print(f"Element '{args.click}' not found")
    
    else:
        print("Usage:")
        print("  --scan <name>        Scan application")
        print("  --click <element>   Click element")
        print("  --uia-only          Use UIA only")
        print("  --ocr-only          Use OCR only")


if __name__ == "__main__":
    main()
