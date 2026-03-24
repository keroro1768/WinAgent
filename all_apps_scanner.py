# -*- coding: utf-8 -*-
"""
使用 WinAgent UIA 取得 All Apps List
"""

import sys
import time
import subprocess
from pathlib import Path

# 確保可以引入模組
sys.path.insert(0, str(Path(__file__).parent))

try:
    import pywinauto
    from pywinauto import Application, timings, Desktop
except ImportError:
    print("需要安裝 pywinauto: pip install pywinauto")
    sys.exit(1)


def open_start_menu():
    """打開開始功能表"""
    # 按下 Windows 鍵
    subprocess.run(['powershell', '-Command', 
        '[System.Windows.Forms.SendKeys]::SendWait("^{ESC}")'], 
        capture_output=True)
    time.sleep(0.5)


def get_all_apps_list():
    """取得 All Apps List"""
    apps = []
    
    # 嘗試連接到 Start Menu 視窗
    # Windows 11/10 的開始功能表是一個 ApplicationFrameWindow
    try:
        # 搜尋開始功能表
        start_menu = None
        
        # 取得所有視窗
        windows = Desktop(backend="win32").windows()
        
        for w in windows:
            class_name = w.window_text()
            if "Start" in class_name or "ApplicationFrame" in w.class_name():
                print(f"找到視窗: {w.window_text()} - {w.class_name()}")
        
        # 嘗試找到 ApplicationFrameWindow
        app = Application(backend="win32").connect(title_re=".*Start.*", timeout=2)
        
    except Exception as e:
        print(f"無法連接到開始功能表: {e}")
    
    return apps


def scan_all_apps_uia():
    """使用 UIA 掃描 All Apps"""
    print("=== 使用 WinAgent UIA 取得 All Apps List ===\n")
    
    apps = []
    
    try:
        # 嘗試使用 find_elements 或類似功能
        from hybrid_scanner import scan_element
        
        # 讓使用者手動打開 All Apps
        input("請打開 All Apps List (按 Windows 鍵，然後點擊 'All apps')")
        print("正在掃描...")
        
        # 取得桌面
        desktop = Desktop(backend="uia")
        
        # 取得所有視窗
        windows = desktop.windows()
        
        for w in windows:
            try:
                # 檢查是否為相關視窗
                if "Start" in w.window_text() or "Application" in w.class_name():
                    print(f"\n視窗: {w.window_text()}")
                    print(f"  Class: {w.class_name()}")
                    
                    # 取得子元素
                    children = w.children()
                    print(f"  子元素數: {len(children)}")
                    
                    for child in children[:20]:  # 只顯示前20個
                        try:
                            name = child.window_text() if hasattr(child, 'window_text') else ""
                            ctrl = child.control_type() if hasattr(child, 'control_type') else ""
                            if name:
                                apps.append(name)
                                print(f"    - {name} ({ctrl})")
                        except:
                            pass
            except Exception as e:
                continue
        
    except Exception as e:
        print(f"掃描錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    return apps


def compare_with_registry():
    """與 Registry 清單比對"""
    print("\n=== 與系統應用程式比對 ===\n")
    
    # 這裡會呼叫 AppList 的功能
    # 但簡化版本我們只列出差異
    
    # Registry 中的數量
    import winreg
    apps_count = 0
    
    keys = [
        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
    ]
    
    for key_path in keys:
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
            i = 0
            while True:
                try:
                    name = winreg.EnumKey(key, i)
                    apps_count += 1
                    i += 1
                except:
                    break
            winreg.CloseKey(key)
        except:
            pass
    
    print(f"Registry 應用程式數量: {apps_count}")
    print(f"UI 應用程式數量: {len(apps)}")
    

if __name__ == "__main__":
    print("使用 WinAgent 取得 All Apps List")
    print("=" * 50)
    
    # 方法1: 嘗試自動取得
    # apps = get_all_apps_list()
    
    # 方法2: 讓使用者打開後掃描
    apps = scan_all_apps_uia()
    
    print(f"\n總共找到 {len(apps)} 個應用程式")
    
    # 與 Registry 比對
    compare_with_registry()
