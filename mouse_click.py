"""
WinAgent Mouse Click Simulator
使用 Win32 API 模擬滑鼠點擊，可以點擊任何 UI 元素
"""

import time
import sys
import ctypes
from ctypes import wintypes
import subprocess

try:
    import uiautomation as auto
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "uiautomation"])
    import uiautomation as auto

# Win32 API
user32 = ctypes.windll.user32

# 滑鼠事件常數
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_MOVE = 0x0001

# 鍵盤事件常數
KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002

def move_mouse(x, y):
    """移動滑鼠到指定位置"""
    user32.SetCursorPos(x, y)
    time.sleep(0.05)

def click_mouse(x=None, y=None):
    """點擊滑鼠左鍵"""
    if x is not None and y is not None:
        move_mouse(x, y)
        time.sleep(0.1)
    
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

def double_click(x, y):
    """雙擊"""
    move_mouse(x, y)
    time.sleep(0.1)
    click_mouse()
    time.sleep(0.1)
    click_mouse()

def find_button_by_name(parent_window, name_pattern):
    """根據名稱尋找按鈕"""
    buttons = []
    
    def search(control, depth):
        if depth > 4:
            return
        try:
            ctype = str(control.ControlTypeName)
            if "Button" in ctype:
                name = control.Name or control.AutomationId or ""
                if name_pattern.lower() in name.lower() or name.lower() in name_pattern.lower():
                    rect = control.BoundingRectangle
                    if rect:
                        center_x = (rect.left + rect.right) // 2
                        center_y = (rect.top + rect.bottom) // 2
                        buttons.append({
                            "name": name,
                            "x": center_x,
                            "y": center_y,
                            "rect": rect
                        })
        except:
            pass
            
        try:
            for child in list(control.GetChildren())[:15]:
                search(child, depth + 1)
        except:
            pass
    
    search(parent_window, 0)
    return buttons

def click_element(element):
    """點擊 UIA 元素"""
    try:
        rect = element.BoundingRectangle
        if not rect:
            return False
            
        center_x = (rect.left + rect.right) // 2
        center_y = (rect.top + rect.bottom) // 2
        
        click_mouse(center_x, center_y)
        return True
    except Exception as e:
        print(f"點擊失敗: {e}")
        return False

def demo_click_notepad_button():
    """示範：點擊 Notepad 的按鈕"""
    print("=" * 60)
    print("WinAgent Mouse Click Demo")
    print("=" * 60)
    
    # 1. 啟動 Notepad
    print("\n[1] 啟動 Notepad")
    proc = subprocess.Popen("notepad.exe")
    time.sleep(2)
    
    # 2. 取得 Notepad 視窗
    notepad = auto.WindowControl(searchDepth=1, ProcessId=proc.pid)
    print(f"    PID: {proc.pid}")
    
    # 3. 尋找所有按鈕
    print("\n[2] 掃描 UI 按鈕")
    buttons = find_button_by_name(notepad, "")
    
    if not buttons:
        print("    未找到按鈕，嘗試其他控制項...")
        # 擴大搜尋範圍
        all_controls = []
        def walk_all(ctrl, d):
            if d > 3: return
            try:
                ct = str(ctrl.ControlTypeName)
                nm = ctrl.Name or ctrl.AutomationId or "?"
                rect = ctrl.BoundingRectangle
                if rect and rect.width > 0:
                    all_controls.append({
                        "type": ct,
                        "name": nm,
                        "rect": rect
                    })
            except: pass
            try:
                for c in list(ctrl.GetChildren())[:10]:
                    walk_all(c, d+1)
            except: pass
        walk_all(notepad, 0)
        
        print(f"    找到 {len(all_controls)} 個控制項:")
        for c in all_controls[:20]:
            print(f"      [{c['type']}] {c['name']}")
            
        buttons = all_controls  # 使用所有控制項
    
    print(f"\n[3] 找到 {len(buttons)} 個可點擊元素")
    
    # 4. 示範點擊第一個按鈕
    if buttons:
        # 點擊第一個
        target = buttons[0]
        print(f"\n[4] 點擊: {target['name']}")
        
        if 'x' in target:
            click_mouse(target['x'], target['y'])
        else:
            # 計算中心點
            r = target['rect']
            click_mouse((r[0]+r[2])//2, (r[1]+r[3])//2)
            
        print("    [完成] 點擊已發送")
        
        # 5. 嘗試點擊其他按鈕
        if len(buttons) > 1:
            time.sleep(0.5)
            target2 = buttons[1]
            print(f"\n[5] 點擊第二個: {target2['name']}")
            
            if 'x' in target2:
                click_mouse(target2['x'], target2['y'])
            else:
                r = target2['rect']
                click_mouse((r[0]+r[2])//2, (r[1]+r[3])//2)
                
            print("    [完成]")
    
    print("\n" + "=" * 60)
    print("[示範完成]")
    print("=" * 60)
    
    # 清理
    time.sleep(1)
    proc.terminate()

def click_at_coordinates(x, y):
    """直接點擊指定座標"""
    print(f"[點擊] ({x}, {y})")
    click_mouse(x, y)

def click_by_uia():
    """點擊 UIA 元素"""
    # 取得目前滑鼠位置的元素
    mx, my = wintypes.DWORD(), wintypes.DWORD()
    user32.GetCursorPos(ctypes.byref(mx), ctypes.byref(my))
    
    element = auto.ElementFromPoint(mx.value, my.value)
    if element:
        print(f"目前滑鼠位置的元素: {element.Name} ({element.ControlTypeName})")
        click_element(element)

# 命令列介面
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="WinAgent Mouse Click Simulator")
    parser.add_argument("--click", nargs=2, type=int, metavar=("X", "Y"), help="點擊指定座標")
    parser.add_argument("--demo", action="store_true", help="執行示範")
    parser.add_argument("--find", metavar="NAME", help="尋找並點擊名稱包含 NAME 的按鈕")
    
    args = parser.parse_args()
    
    if args.click:
        click_at_coordinates(args.click[0], args.click[1])
    elif args.find:
        # 尋找並點擊
        print(f"尋找按鈕: {args.find}")
        # 這需要目標視窗，這裡簡化處理
        print("請配合 --demo 使用")
    elif args.demo:
        demo_click_notepad_button()
    else:
        # 預設示範
        demo_click_notepad_button()
