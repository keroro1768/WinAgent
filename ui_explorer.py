"""
WinAgent UI Explorer
通用 UI 控件遍歷與分析工具
可以掃描任何 Windows 應用程式的 UI 控件樹
"""

import subprocess
import time
import sys
import os
import json
from datetime import datetime

try:
    import uiautomation as auto
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "uiautomation"])
    import uiautomation as auto

class UIExplorer:
    def __init__(self):
        self.results = []
        
    def scan_window_by_name(self, window_name):
        """透過視窗名稱尋找並掃描"""
        window = auto.WindowControl(searchDepth=10, Name=window_name)
        if not window.Exists(3):
            print(f"[錯誤] 找不到視窗: {window_name}")
            return None
        
        return self.scan_element(window)
    
    def scan_window_by_pid(self, pid):
        """透過 PID 掃描"""
        try:
            window = auto.WindowControl(searchDepth=1, ProcessId=pid)
            if not window.Exists(1):
                print(f"[錯誤] 找不到 PID: {pid}")
                return None
            return self.scan_element(window)
        except Exception as e:
            print(f"[錯誤] {e}")
            return None
    
    def scan_foreground(self):
        """掃描目前前景視窗"""
        fg = auto.GetForegroundWindow()
        if not fg:
            print("[錯誤] 無法取得前景視窗")
            return None
        
        try:
            window = auto.WindowControl(NativeWindowHandle=fg)
            return self.scan_element(window)
        except Exception as e:
            print(f"[錯誤] {e}")
            return None
    
    def scan_element(self, element, max_depth=5, max_children=50):
        """遞迴掃描 UI 元素"""
        self.results = []
        self._scan_recursive(element, 0, max_depth, max_children)
        return self.results
    
    def _scan_recursive(self, element, depth, max_depth, max_children):
        if depth > max_depth:
            return
        
        try:
            # 取得基本資訊
            info = {
                "depth": depth,
                "name": element.Name or "(無名稱)",
                "type": str(element.ControlTypeName),
                "automation_id": element.AutomationId or "",
                "class_name": element.ClassName or "",
            }
            
            # 取得位置資訊
            rect = element.BoundingRectangle
            if rect and rect.width > 0:
                info["bounds"] = {
                    "x": rect.left,
                    "y": rect.top,
                    "width": rect.width,
                    "height": rect.height,
                    "center_x": (rect.left + rect.right) // 2,
                    "center_y": (rect.top + rect.bottom) // 2
                }
            
            # 取得數值（如果是 Edit/ComboBox）
            try:
                value = element.Current.Value
                if value:
                    info["value"] = value
            except:
                pass
            
            # 取得狀態
            try:
                info["is_enabled"] = element.Current.IsEnabled
                info["is_focused"] = element.Current.HasKeyboardFocus
            except:
                pass
            
            self.results.append(info)
            
            # 遞迴掃描子元素
            children = list(element.GetChildren())[:max_children]
            for child in children:
                self._scan_recursive(child, depth + 1, max_depth, max_children)
                
        except Exception as e:
            pass  # 忽略存取錯誤
    
    def print_summary(self, title="UI 掃描結果"):
        """輸出摘要"""
        print("\n" + "="*60)
        print(title)
        print("="*60)
        
        if not self.results:
            print("無結果")
            return
        
        # 按類型分組
        by_type = {}
        for r in self.results:
            t = r.get("type", "Unknown")
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(r)
        
        # 輸出統計
        print(f"\n總控件數: {len(self.results)}")
        print("\n按類型統計:")
        for t, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
            print(f"  {t}: {len(items)}")
        
        # 輸出所有控件
        print("\n" + "-"*60)
        print("控件清單:")
        print("-"*60)
        
        for r in self.results:
            depth = r.get("depth", 0)
            indent = "  " * depth
            
            name = r.get("name", "?")[:30]
            ctype = r.get("type", "?")
            
            extra = ""
            if r.get("automation_id"):
                extra = f" [ID: {r['automation_id'][:20]}]"
            if r.get("value"):
                val = str(r.get("value"))[:20]
                extra += f" = '{val}'"
            
            bounds = r.get("bounds", {})
            if bounds:
                pos = f"(@{bounds['center_x']},{bounds['center_y']})"
            else:
                pos = ""
            
            print(f"{indent}[{ctype}] {name}{extra}{pos}")
    
    def save_to_file(self, filename=None):
        """儲存結果"""
        if not filename:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ui_scan_{ts}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({
                "scanned_at": datetime.now().isoformat(),
                "total_controls": len(self.results),
                "controls": self.results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n[儲存] {filename}")
        return filename
    
    def find_buttons(self):
        """找出所有按鈕"""
        return [r for r in self.results if "Button" in r.get("type", "")]
    
    def find_edits(self):
        """找出所有編輯框"""
        return [r for r in self.results if "Edit" in r.get("type", "")]
    
    def find_menus(self):
        """找出所有選單"""
        return [r for r in self.results if "Menu" in r.get("type", "")]
    
    def find_dropdowns(self):
        """找出所有下拉選單"""
        return [r for r in self.results if "ComboBox" in r.get("type", "")]
    
    def interactive_explore(self):
        """互動式探索"""
        print("\n" + "="*60)
        print("互動式 UI 探索")
        print("="*60)
        print("操作說明:")
        print("  按 Tab 切換控制項")
        print("  按 Enter 點擊目前的控制項")
        print("  按 S 儲存目前結果")
        print("  按 Q 離開")
        print("="*60)
        
        fg = auto.GetForegroundWindow()
        if not fg:
            print("[錯誤] 無法取得前景視窗")
            return
        
        window = auto.WindowControl(NativeWindowHandle=fg)
        print(f"\n視窗: {window.Name}\n")
        
        # 取得所有可交互的元素
        controls = []
        
        def get_interactive(ctrl, depth=0):
            if depth > 3:
                return
            try:
                ct = str(ctrl.ControlTypeName)
                if any(t in ct for t in ["Button", "Edit", "MenuItem", "CheckBox", "RadioButton", "ComboBox"]):
                    rect = ctrl.BoundingRectangle
                    if rect and rect.width > 0:
                        controls.append({
                            "element": ctrl,
                            "name": ctrl.Name or ctrl.AutomationId or "?",
                            "type": ct,
                            "x": (rect.left + rect.right) // 2,
                            "y": (rect.top + rect.bottom) // 2
                        })
            except:
                pass
            
            try:
                for child in list(ctrl.GetChildren())[:20]:
                    get_interactive(child, depth + 1)
            except:
                pass
        
        get_interactive(window)
        
        if not controls:
            print("[警告] 找不到可交互的控制項")
            return
        
        print(f"找到 {len(controls)} 個可交互控制項:\n")
        
        for i, c in enumerate(controls[:30]):
            print(f"  {i+1:2}. [{c['type']}] {c['name']}")
        
        print(f"\n共 {len(controls)} 個控制項")


# ===== CLI =====
def main():
    import argparse
    parser = argparse.ArgumentParser(description="WinAgent UI Explorer")
    parser.add_argument("--name", "-n", metavar="NAME", help="掃描指定名稱的視窗")
    parser.add_argument("--pid", "-p", type=int, metavar="PID", help="掃描指定 PID 的視窗")
    parser.add_argument("--foreground", "-f", action="store_true", help="掃描前景視窗")
    parser.add_argument("--depth", "-d", type=int, default=5, help="掃描深度")
    parser.add_argument("--output", "-o", metavar="FILE", help="輸出檔案")
    parser.add_argument("--buttons", action="store_true", help="只顯示按鈕")
    parser.add_argument("--edits", action="store_true", help="只顯示編輯框")
    parser.add_argument("--menus", action="store_true", help="只顯示選單")
    parser.add_argument("--dropdowns", action="store_true", help="只顯示下拉選單")
    parser.add_argument("--interactive", "-i", action="store_true", help="互動式探索")
    parser.add_argument("--launch", metavar="APP", help="啟動應用程式後掃描")
    
    args = parser.parse_args()
    
    explorer = UIExplorer()
    
    # 啟動應用程式
    if args.launch:
        print(f"[啟動] {args.launch}")
        proc = subprocess.Popen(args.launch)
        time.sleep(3)  # 等待視窗出現
    
    # 執行掃描
    if args.name:
        result = explorer.scan_window_by_name(args.name)
    elif args.pid:
        result = explorer.scan_window_by_pid(args.pid)
    elif args.foreground or args.launch:
        result = explorer.scan_foreground()
    else:
        print("用法:")
        print("  --foreground, -f      掃描前景視窗")
        print("  --name NAME, -n      掃描指定視窗")
        print("  --pid PID             掃描指定 PID")
        print("  --launch APP          啟動應用程式後掃描")
        print("  --interactive, -i    互動式探索")
        print("")
        print("範例:")
        print("  python ui_explorer.py --foreground")
        print("  python ui_explorer.py --launch notepad.exe")
        print("  python ui_explorer.py -n \"Notepad\"")
        return
    
    if result:
        explorer.results = result
        
        # 過濾顯示
        if args.buttons:
            items = explorer.find_buttons()
            title = f"按鈕清單 ({len(items)} 個)"
        elif args.edits:
            items = explorer.find_edits()
            title = f"編輯框清單 ({len(items)} 個)"
        elif args.menus:
            items = explorer.find_menus()
            title = f"選單清單 ({len(items)} 個)"
        elif args.dropdowns:
            items = explorer.find_dropdowns()
            title = f"下拉選單清單 ({len(items)} 個)"
        else:
            items = result
            title = "UI 掃描結果"
        
        # 顯示
        explorer.results = items
        explorer.print_summary(title)
        
        # 儲存
        if args.output:
            explorer.save_to_file(args.output)
        else:
            # 預設儲存
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            explorer.save_to_file(f"ui_scan_{ts}.json")
    
    elif args.interactive:
        explorer.interactive_explore()

if __name__ == "__main__":
    main()
