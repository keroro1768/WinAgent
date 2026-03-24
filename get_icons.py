# -*- coding: utf-8 -*-
"""
WinAgent All Apps Scanner - 含 ICON 取得
"""

import os
import re
import subprocess
from pathlib import Path
import json
import winreg
import ctypes
from PIL import Image

# 取得 ICON 的函數
def get_icon_from_file(file_path, icon_index=0):
    """從 exe/dll/ico 檔案取得 ICON"""
    try:
        import win32ui, win32con
        ico = win32ui.CreateIconFromFile(file_path, icon_index)
        if ico:
            # 轉換為 bitmap
            hdc = win32ui.CreateDC()
            memdc = hdc.CreateCompatibleDC()
            bmp = win32ui.CreateBitmap()
            bmp.CreateCompatibleBitmap(hdc, 32, 32)
            memdc.SelectObject(bmp)
            memdc.DrawIcon((0, 0), ico)
            
            # 儲存
            bmp.SaveBitmapFile(memdc, str(Path(__file__).parent / "temp.bmp"))
            return True
    except:
        pass
    return False

def get_icon_extracticon(file_path):
    """使用 ExtractIcon API"""
    try:
        user32 = ctypes.windll.user32
        shell32 = ctypes.windll.shell32
        
        # 取得圖示
        hicon = shell32.ExtractIconW(None, file_path, 0)
        if hicon:
            # 轉換為圖片
            icon = ctypes.windll.user32.CopyImage(hicon, 1, 0, 0, 0)
            return icon
    except:
        pass
    return None

def get_app_icon_from_startmenu(app_name):
    """從 Start Menu 捷徑取得 ICON"""
    folders = [
        os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
    ]
    
    for folder in folders:
        if not os.path.exists(folder):
            continue
        for root, dirs, files in os.walk(folder):
            for f in files:
                if f.endswith('.lnk'):
                    name = f.replace('.lnk', '')
                    if name.lower() == app_name.lower():
                        full_path = os.path.join(root, f)
                        # 嘗試讀取捷徑
                        try:
                            import win32com.client
                            shell = win32com.client.Dispatch("WScript.Shell")
                            shortcut = shell.CreateShortcut(full_path)
                            target = shortcut.Targetpath
                            if target and os.path.exists(target):
                                return target
                        except:
                            pass
    return None

def get_store_app_icon(package_name):
    """從 Windows Store App 取得 ICON"""
    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', 
             f'(Get-AppxPackage -Name "{package_name}").InstallLocation'],
            capture_output=True, text=False
        )
        if result.returncode == 0:
            path = result.stdout.decode('utf-8', errors='ignore').strip()
            if path:
                # 尋找圖示檔案
                for root, dirs, files in os.walk(path):
                    for f in files:
                        if 'app' in f.lower() and f.endswith('.png'):
                            return os.path.join(root, f)
    except:
        pass
    return None

def generate_icon_manifest(apps):
    """產生 ICON 清單"""
    icons = []
    
    for app in apps[:50]:  # 只處理前50個
        # 嘗試從 Start Menu 取得
        exe_path = get_app_icon_from_startmenu(app)
        
        icons.append({
            'name': app,
            'exe_path': exe_path,
            'icon_extracted': False
        })
    
    return icons

def main():
    print("=" * 60)
    print("WinAgent All Apps Scanner - with ICON")
    print("=" * 60)
    
    # 讀取現有清單
    json_file = Path(__file__).parent / "all_apps_complete.json"
    if json_file.exists():
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        all_apps = data.get('all_apps', [])
        print(f"\n總應用: {len(all_apps)}")
        
        # 產生 ICON 清單
        print("\n產生 ICON 清單...")
        icons = generate_icon_manifest(all_apps)
        
        # 儲存
        icon_file = Path(__file__).parent / "app_icons.json"
        with open(icon_file, 'w', encoding='utf-8') as f:
            json.dump(icons, f, ensure_ascii=False, indent=2)
        
        print(f"ICON 清單已儲存: {icon_file}")
        print(f"共 {len(icons)} 個")
    else:
        print("請先執行 get_all_apps.py")

if __name__ == "__main__":
    main()
