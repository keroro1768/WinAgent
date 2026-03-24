# -*- coding: utf-8 -*-
"""
WinAgent All Apps Scanner - 優化版
支援增量掃描、快取、變更監控
"""

import os
import time
import subprocess
from pathlib import Path
import json
import winreg
import hashlib
from datetime import datetime

# 快取檔案
CACHE_FILE = Path(__file__).parent / "app_cache.json"
LAST_SCAN_FILE = Path(__file__).parent / "last_scan.timestamp"

def get_file_hash(content):
    """取得內容雜湊"""
    return hashlib.md5(str(content).encode()).hexdigest()[:8]

def load_cache():
    """載入快取"""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'apps': [], 'hash': '', 'timestamp': 0}

def save_cache(apps):
    """儲存快取"""
    content = json.dumps(apps, ensure_ascii=False)
    cache = {
        'apps': apps,
        'hash': get_file_hash(content),
        'timestamp': time.time(),
        'count': len(apps)
    }
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def quick_scan():
    """快速增量掃描 - 只檢查變更"""
    print("=== 快速掃描 (增量模式) ===")
    
    # 檢查最後掃描時間
    if LAST_SCAN_FILE.exists():
        with open(LAST_SCAN_FILE, 'r') as f:
            last_time = float(f.read())
            print(f"上次掃描: {datetime.fromtimestamp(last_time)}")
    else:
        last_time = 0
    
    # 檢查關鍵位置是否有變更
    changed = False
    paths_to_check = [
        os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
    ]
    
    for path in paths_to_check:
        if os.path.exists(path):
            mtime = os.path.getmtime(path)
            if mtime > last_time:
                changed = True
                print(f"  發現變更: {path}")
    
    if changed:
        print("  需要完整掃描...")
        return full_scan()
    else:
        print("  無變更，使用快取")
        cache = load_cache()
        return cache.get('apps', [])

def full_scan():
    """完整掃描"""
    print("\n=== 完整掃描 ===")
    start_time = time.time()
    
    apps = set()
    
    # 1. Start Menu (快速)
    print("[1] Start Menu...")
    for folder in [
        os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
    ]:
        if os.path.exists(folder):
            for f in os.listdir(folder):
                if f.endswith('.lnk'):
                    apps.add(f.replace('.lnk', ''))
    print(f"  找到: {len(apps)}")
    
    # 2. PowerShell Get-StartApps (快速)
    print("[2] Get-StartApps...")
    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', 
             'Get-StartApps | ForEach-Object { $_.Name }'],
            capture_output=True, text=False, timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.decode('utf-8', errors='ignore').split('\n'):
                line = line.strip()
                if line:
                    apps.add(line)
    except:
        pass
    print(f"  找到: {len(apps)}")
    
    # 3. Shell AppsFolder (快速)
    print("[3] AppsFolder...")
    try:
        import win32com.client
        shell = win32com.client.Dispatch("Shell.Application")
        folder = shell.NameSpace("shell:AppsFolder")
        if folder:
            for item in folder.Items():
                apps.add(item.Name)
    except:
        pass
    print(f"  找到: {len(apps)}")
    
    # 4. Registry (較慢，可選)
    # 這裡略過，因為最耗時
    
    # 儲存結果
    apps_list = sorted(list(apps))
    save_cache(apps_list)
    
    # 記錄時間
    with open(LAST_SCAN_FILE, 'w') as f:
        f.write(str(time.time()))
    
    elapsed = time.time() - start_time
    print(f"\n完成! 耗時: {elapsed:.2f}秒, 總數: {len(apps_list)}")
    
    return apps_list

def main():
    import sys
    
    mode = sys.argv[1] if len(sys.argv) > 1 else "quick"
    
    if mode == "full":
        apps = full_scan()
    elif mode == "quick":
        apps = quick_scan()
    elif mode == "watch":
        watch_mode()
    else:
        apps = full_scan()
    
    print(f"\n總應用: {len(apps)}")

def watch_mode():
    """監控模式 - 持續監看變更"""
    print("=== 監控模式 (按 Ctrl+C 結束) ===")
    print("監控中...每次偵測到變更會自動更新")
    
    import threading
    
    apps = full_scan()
    
    while True:
        time.sleep(60)  # 每分鐘檢查
        new_apps = quick_scan()
        if set(new_apps) != set(apps):
            print(f"\n偵測到變更! {len(new_apps)} 個應用")
            apps = new_apps

if __name__ == "__main__":
    main()
