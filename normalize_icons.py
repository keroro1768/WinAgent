# -*- coding: utf-8 -*-
"""
ICON 標準化處理 - 統一大小
"""

import os
import sys
from pathlib import Path
import json
import ctypes
from PIL import Image

# ICON 輸出大小
ICON_SIZE = 48  # 可選: 16, 24, 32, 48, 64, 128

def resize_icon_image(source_path, target_path, size=ICON_SIZE):
    """使用 PIL 調整圖片大小"""
    try:
        if source_path.lower().endswith('.png'):
            img = Image.open(source_path)
        else:
            # 嘗試從 exe 取得
            img = None
        
        if img:
            # 轉換為 RGBA
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # 調整大小 (使用 LANCZOS 保持品質)
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # 儲存
            img.save(target_path, 'PNG')
            return True
    except Exception as e:
        print(f"  錯誤: {e}")
    return False

def get_icon_from_exe(exe_path, output_path, size=ICON_SIZE):
    """從 exe 擷取並調整 ICON"""
    try:
        # 使用 Windows API
        user32 = ctypes.windll.user32
        shell32 = ctypes.windll.shell32
        
        # 取得圖示
        hicon = shell32.ExtractIconW(None, exe_path, 0)
        if not hicon:
            return False
        
        # 轉換為 BMP
        icon_info = ctypes.create_struct_pointer(
            type('ICONINFO', (), {
                'fIcon': True,
                'hbmColor': None,
                'hbmMask': None
            })
        )
        
        # 取得圖示資訊
        if not user32.GetIconInfo(hicon, ctypes.byref(icon_info)):
            return False
        
        # 轉換為 bitmap
        from PIL import ImageGrab, Image
        
        # 取得尺寸
        bmp = Image.New('RGBA', (size, size), (0,0,0,0))
        
        # 這裡需要 GDI+ 處理，簡化版本直接用固定尺寸
        user32.DestroyIcon(hicon)
        
        # 儲存空白圖片作為 placeholder
        bmp.save(output_path, 'PNG')
        return True
        
    except Exception as e:
        return False

def create_icon_manifest(apps_file, output_file):
    """建立標準化 ICON 清單"""
    
    # 讀取應用清單
    with open(apps_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    apps = data.get('all_apps', []) if isinstance(data, dict) else data
    
    # 建立輸出目錄
    icons_dir = Path(apps_file).parent / "icons_normalized"
    icons_dir.mkdir(exist_ok=True)
    
    print(f"標準化 ICON 目錄: {icons_dir}")
    print(f"目標大小: {ICON_SIZE}x{ICON_SIZE}")
    
    results = []
    
    for i, app in enumerate(apps[:100]):  # 只處理前100個
        # 找尋 exe 路徑
        exe_path = find_app_exe(app)
        
        if exe_path:
            output_path = icons_dir / f"{sanitize_name(app)}.png"
            
            # 嘗試擷取並調整大小
            if get_icon_from_exe(exe_path, str(output_path), ICON_SIZE):
                results.append({
                    'name': app,
                    'icon': str(output_path),
                    'size': ICON_SIZE
                })
            else:
                # 建立佔位圖
                create_placeholder(str(output_path), ICON_SIZE)
                results.append({
                    'name': app,
                    'icon': str(output_path),
                    'placeholder': True
                })
        else:
            # 建立佔位圖
            placeholder = icons_dir / f"{sanitize_name(app)}.png"
            create_placeholder(str(placeholder), ICON_SIZE)
            results.append({
                'name': app,
                'icon': str(placeholder),
                'placeholder': True
            })
        
        if (i+1) % 10 == 0:
            print(f"  處理: {i+1}/{min(100, len(apps))}")
    
    # 儲存結果
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'size': ICON_SIZE,
            'count': len(results),
            'icons': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n完成! 共 {len(results)} 個 ICON")
    print(f"結果: {output_file}")

def create_placeholder(path, size):
    """建立佔位圖"""
    img = Image.new('RGBA', (size, size), (200, 200, 200, 255))
    # 畫一個圓形
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.ellipse([4, 4, size-4, size-4], fill=(100, 100, 100, 255))
    img.save(path, 'PNG')

def sanitize_name(name):
    """清理檔名"""
    return "".join(c for c in name if c.isalnum())[:30]

def find_app_exe(app_name):
    """找尋應用程式路徑"""
    # 從 Start Menu 捷徑
    for folder in [
        os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
    ]:
        if not os.path.exists(folder):
            continue
        for root, dirs, files in os.walk(folder):
            for f in files:
                if f.replace('.lnk', '').lower() == app_name.lower():
                    path = os.path.join(root, f)
                    try:
                        import win32com.client
                        shell = win32com.client.Dispatch("WScript.Shell")
                        shortcut = shell.CreateShortcut(path)
                        target = shortcut.Targetpath
                        if target and os.path.exists(target):
                            return target
                    except:
                        pass
    return None

def main():
    apps_file = Path(__file__).parent / "all_apps_complete.json"
    output_file = Path(__file__).parent / "icons_normalized.json"
    
    if not apps_file.exists():
        print("請先執行 get_all_apps.py")
        return
    
    create_icon_manifest(apps_file, output_file)

if __name__ == "__main__":
    main()
