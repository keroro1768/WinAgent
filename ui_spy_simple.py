"""
WinAgent UI Spy - 簡化版 即時監控
"""

import time
import sys

try:
    import uiautomation as auto
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "uiautomation"])
    import uiautomation as auto

def get_all_buttons(root):
    """遞迴取得所有按鈕"""
    buttons = []
    
    def walk(ctrl, depth):
        if depth > 4:
            return
        try:
            ctype = str(ctrl.ControlTypeName)
            if "Button" in ctype:
                name = ctrl.Name or ctrl.AutomationId or "(無名)"
                rect = ctrl.BoundingRectangle
                if rect and rect.width > 0:
                    buttons.append({
                        "name": name,
                        "type": ctype,
                        "rect": (rect.left, rect.top, rect.right, rect.bottom)
                    })
        except:
            pass
            
        try:
            for child in list(ctrl.GetChildren())[:20]:
                walk(child, depth + 1)
        except:
            pass
            
    walk(root, 0)
    return buttons

def main():
    print("=" * 60)
    print("WinAgent UI Spy - 即時監控")
    print("=" * 60)
    print("按 Ctrl+C 停止\n")
    
    last_hwnd = 0
    
    try:
        while True:
            # 取得前景視窗
            fg = auto.GetForegroundWindow()
            if not fg or fg == last_hwnd:
                time.sleep(0.5)
                continue
                
            last_hwnd = fg
            
            # 取得視窗名稱
            try:
                win = auto.WindowControl(NativeWindowHandle=fg)
                title = win.Name or "Unknown"
            except:
                title = "Unknown"
                
            print(f"\n[{time.strftime('%H:%M:%S')}] 視窗: {title}")
            print("-" * 40)
            
            # 取得按鈕
            buttons = get_all_buttons(win)
            
            if buttons:
                print(f"找到 {len(buttons)} 個按鈕:")
                for b in buttons[:15]:
                    print(f"  • {b['name']} ({b['type']})")
            else:
                print("未找到按鈕")
                
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n[停止]")

if __name__ == "__main__":
    main()
