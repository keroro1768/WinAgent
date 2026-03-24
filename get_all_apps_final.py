# -*- coding: utf-8 -*-
"""
WinAgent All Apps Scanner - 使用現有 hybrid_scanner
"""

import sys
import os
import time
import ctypes
from pathlib import Path
import json
import winreg

sys.path.insert(0, str(Path(__file__).parent))

# 使用現有的 hybrid_scanner
try:
    from hybrid_scanner import HybridScanner
    HYBRID_AVAILABLE = True
except:
    HYBRID_AVAILABLE = False
    print("hybrid_scanner not available")

def get_system_apps():
    """取得所有系統來源的應用"""
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

def scan_with_hybrid_scanner():
    """使用 HybridScanner 掃描"""
    if not HYBRID_AVAILABLE:
        return []
    
    apps = []
    scanner = HybridScanner()
    
    # 搜尋開始功能表
    print("  使用 HybridScanner 搜尋...")
    
    # 找到開始功能表視窗
    window = scanner.get_window("Start")
    
    if window:
        print(f"  找到視窗: {window['title']}")
        
        # 取得元素
        result = scanner.scan_uia(window)
        
        if 'elements' in result:
            for elem in result['elements']:
                name = elem.get('name', '')
                if name and len(name) > 1:
                    apps.append(name)
    
    return list(set(apps))

def capture_and_ocr_simple():
    """簡單截圖 OCR"""
    apps = []
    
    try:
        from PIL import ImageGrab
        import pytesseract
        
        # 截圖
        print("  截圖...")
        img = ImageGrab.grab()
        
        # 儲存
        img.save(Path(__file__).parent / "startmenu_capture.png")
        
        # 嘗試 OCR - 只辨識部分區域
        user32 = ctypes.windll.user32
        w, h = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
        
        # 底部區域 (開始功能表)
        bbox = (0, h-900, w, h-30)
        cropped = img.crop(bbox)
        
        # OCR
        text = pytesseract.image_to_string(cropped, lang='chi_sim+eng')
        
        # 解析行
        for line in text.split('\n'):
            line = line.strip()
            if 2 < len(line) < 50:
                lower = line.lower()
                if not any(s in lower for s in ['all apps', 'settings', 'power', 'search', 'pin', 'start']):
                    apps.append(line)
        
        apps = list(set(apps))
        print(f"  OCR 找到: {len(apps)}")
        
    except Exception as e:
        print(f"  OCR錯誤: {e}")
    
    return apps

def main():
    print("=" * 60)
    print("WinAgent All Apps Scanner - 最終版")
    print("=" * 60)
    
    # 系統來源
    print("\n[1] 系統來源...")
    system = get_system_apps()
    print(f"  系統總數: {len(system)}")
    
    # UIA (hybrid scanner)
    print("\n[2] Hybrid Scanner...")
    hybrid = scan_with_hybrid_scanner()
    print(f"  Hybrid: {len(hybrid)}")
    
    # OCR
    print("\n[3] OCR...")
    ocr = capture_and_ocr_simple()
    print(f"  OCR: {len(ocr)}")
    
    # 合併 UI 來源
    ui_all = list(set(hybrid + ocr))
    print(f"  UI 合併: {len(ui_all)}")
    
    # 比對
    print("\n[4] 比對...")
    sys_set = set(a.lower().strip() for a in system)
    ui_set = set(a.lower().strip() for a in ui_all)
    
    in_both = sys_set & ui_set
    only_ui = ui_set - sys_set
    only_sys = sys_set - ui_set
    
    print(f"  共同: {len(in_both)}")
    print(f"  僅在UI: {len(only_ui)}")
    print(f"  僅在系統: {len(only_sys)}")
    
    # 完整結果
    all_apps = sorted(list(sys_set))
    
    result = {
        'sources': {
            'system': len(system),
            'hybrid': len(hybrid),
            'ocr': len(ocr)
        },
        'total': len(all_apps),
        'in_both': len(in_both),
        'only_ui': sorted(list(only_ui))[:30],
        'only_system': sorted(list(only_sys))[:50],
        'all_apps': all_apps
    }
    
    # 儲存
    output = Path(__file__).parent / "all_apps_final.json"
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n完成! 總數: {len(all_apps)}")
    print(f"結果: {output}")

if __name__ == "__main__":
    main()
