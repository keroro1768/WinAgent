# -*- coding: utf-8 -*-
"""
WinAgent All Apps Scanner - 使用 PowerShell Get-StartApps
"""

import sys
import os
import subprocess
from pathlib import Path
import json
import winreg

def get_startapps_powershell():
    """使用 PowerShell Get-StartApps 取得"""
    apps = []
    
    try:
        result = subprocess.run(
            ['powershell', '-Command', 'Get-StartApps | ConvertTo-Json'],
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        if result.returncode == 0:
            data = result.stdout
            if data.strip():
                import json as j
                try:
                    items = j.loads(data)
                    if isinstance(items, list):
                        for item in items:
                            name = item.get('Name', '')
                            if name:
                                apps.append(name)
                    elif isinstance(items, dict):
                        name = items.get('Name', '')
                        if name:
                            apps.append(name)
                except:
                    # 如果解析失敗，手動解析
                    for line in data.split('\n'):
                        if '"Name"' in line:
                            try:
                                name = line.split('"Name"')[1].split(':')[1].strip().strip(',').strip('"')
                                if name:
                                    apps.append(name)
                            except:
                                pass
    except Exception as e:
        print(f"  PowerShell錯誤: {e}")
    
    return apps

def get_system_apps():
    """取得系統來源"""
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

def main():
    print("=" * 60)
    print("WinAgent All Apps Scanner - PowerShell 版本")
    print("=" * 60)
    
    # PowerShell Get-StartApps
    print("\n[1] PowerShell Get-StartApps...")
    startapps = get_startapps_powershell()
    print(f"  Get-StartApps: {len(startapps)}")
    if startapps:
        print("  樣本:")
        for a in startapps[:10]:
            print(f"    - {a}")
    
    # 系統來源
    print("\n[2] 系統來源...")
    system = get_system_apps()
    print(f"  系統: {len(system)}")
    
    # 比對
    print("\n[3] 比對...")
    
    startapps_set = set(a.lower().strip() for a in startapps)
    system_set = set(a.lower().strip() for a in system)
    
    in_both = startapps_set & system_set
    only_startapps = startapps_set - system_set
    only_system = system_set - startapps_set
    
    print(f"  共同: {len(in_both)}")
    print(f"  僅在StartApps: {len(only_startapps)}")
    print(f"  僅在系統: {len(only_system)}")
    
    # 合併最終清單
    all_apps = sorted(list(system_set | startapps_set))
    
    result = {
        'sources': {
            'startapps': len(startapps),
            'system': len(system)
        },
        'total': len(all_apps),
        'in_both': len(in_both),
        'only_startapps': sorted(list(only_startapps)),
        'only_system': sorted(list(only_system))[:50],
        'all_apps': all_apps
    }
    
    # 儲存
    output = Path(__file__).parent / "all_apps_complete.json"
    with open(output, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n完成! 總數: {len(all_apps)}")
    print(f"結果: {output}")

if __name__ == "__main__":
    main()
