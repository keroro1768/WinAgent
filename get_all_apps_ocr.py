# -*- coding: utf-8 -*-
"""
WinAgent All Apps Scanner - OCR 版本
"""

import sys
import os
import time
import ctypes
from pathlib import Path
import json
import winreg

def click_at(x, y):
    user32 = ctypes.windll.user32
    user32.SetCursorPos(x, y)
    time.sleep(0.1)
    user32.mouse_event(0x0002, 0, 0, 0, 0)
    time.sleep(0.1)
    user32.mouse_event(0x0004, 0, 0, 0, 0)
    time.sleep(0.2)

def open_all_apps():
    """打開 All Apps 清單"""
    user32 = ctypes.windll.user32
    w, h = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    
    # 1. 點擊開始
    click_at(50, h - 50)
    print("[1] 點擊開始")
    time.sleep(1.5)
    
    # 2. 點擊 All apps (在右側)
    click_at(w - 80, h - 140)
    print("[2] 點擊 All apps")
    time.sleep(2)

def get_system_apps():
    """取得系統應用程式"""
    apps = []
    
    # Start Menu
    for folder in [
        os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
    ]:
        if os.path.exists(folder):
            for root, dirs, files in os.walk(folder):
                for f in files:
                    if f.endswith('.lnk'):
                        name = f.replace('.lnk', '')
                        if name:
                            apps.append(name)
    
    # Registry
    for hkey, path in [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]:
        try:
            key = winreg.OpenKey(hkey, path)
            i = 0
            while True:
                try:
                    subkey = winreg.EnumKey(key, i)
                    try:
                        with winreg.OpenKey(key, subkey) as sub:
                            name, _ = winreg.QueryValueEx(sub, "DisplayName")
                            if name:
                                apps.append(name)
                    except:
                        pass
                    i += 1
                except:
                    break
            winreg.CloseKey(key)
        except:
            pass
    
    # AppsFolder
    try:
        import win32com.client
        shell = win32com.client.Dispatch("Shell.Application")
        folder = shell.NameSpace("shell:AppsFolder")
        if folder:
            for item in folder.Items():
                apps.append(item.Name)
    except:
        pass
    
    return list(set(apps))

def capture_and_ocr():
    """截圖並 OCR 識別"""
    try:
        from PIL import ImageGrab, Image
        import pytesseract
        
        # 截取全螢幕
        print("[3] 截圖...")
        screenshot = ImageGrab.grab()
        
        # 儲存截圖
        screenshot.save(Path(__file__).parent / "all_apps_screenshot.png")
        print("  已儲存截圖")
        
        # 嘗試 OCR
        print("[4] OCR 識別...")
        
        # 設定 OCR 語言
        pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        
        # 只辨識上半部分（開始功能表區域）
        user32 = ctypes.windll.user32
        w, h = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        
        # 裁剪區域
        bbox = (0, h - 800, w, h - 50)  # 底部區域
        cropped = screenshot.crop(bbox)
        
        # OCR
        text = pytesseract.image_to_string(cropped, lang='chi_sim+eng')
        
        # 解析應用程式名稱
        lines = text.split('\n')
        apps = []
        
        for line in lines:
            line = line.strip()
            # 過濾太短或太長的
            if 2 < len(line) < 50:
                # 過濾非應用程式
                lower = line.lower()
                if not any(s in lower for s in ['all apps', 'settings', 'power', 'search', 'pin']):
                    apps.append(line)
        
        apps = list(set(apps))
        print(f"  OCR 找到: {len(apps)}")
        
        if apps:
            print("  前10個:")
            for a in sorted(apps)[:10]:
                print(f"    - {a}")
        
        return apps
        
    except ImportError as e:
        print(f"  缺少套件: {e}")
        print("  請安裝: pip install pillow pytesseract")
        print("  並安裝 Tesseract OCR")
    except Exception as e:
        print(f"  OCR 錯誤: {e}")
    
    return []

def main():
    print("=" * 60)
    print("WinAgent All Apps Scanner - OCR 版本")
    print("=" * 60)
    
    # 打開 All Apps
    print("\n打開 All Apps 清單...")
    open_all_apps()
    
    # OCR 取得
    ui = capture_and_ocr()
    
    # 系統來源
    print("\n取得系統應用程式...")
    system = get_system_apps()
    print(f"  系統: {len(system)}")
    
    # 比對
    if ui:
        system_set = set(a.lower().strip() for a in system)
        ui_set = set(a.lower().strip() for a in ui)
        
        only_ui = ui_set - system_set
        only_system = system_set - ui_set
        
        print(f"\n=== 比對結果 ===")
        print(f"只在 UI: {len(only_ui)}")
        print(f"只在系統: {len(only_system)}")
        
        result = {'only_ui': list(only_ui)[:30], 'only_system': list(only_system)[:30]}
        
        with open(Path(__file__).parent / "all_apps_comparison.json", 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("\n完成!")

if __name__ == "__main__":
    main()
