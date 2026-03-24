# -*- coding: utf-8 -*-
"""
WinAgent All Apps Scanner - 最終完成版 (修復編碼)
"""

import os
import re
import subprocess
from pathlib import Path
import json
import winreg

def clean_name(name):
    """清理名稱"""
    if not name:
        return None
    # 移除非法字元
    name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', name)
    name = name.strip()
    if len(name) < 2:
        return None
    return name

def get_startapps():
    """使用 PowerShell Get-StartApps"""
    apps = []
    try:
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', 
             'Get-StartApps | ForEach-Object { $_.Name }'],
            capture_output=True, text=False
        )
        if result.returncode == 0:
            text = result.stdout.decode('utf-8', errors='ignore')
            for line in text.split('\n'):
                line = line.strip()
                name = clean_name(line)
                if name:
                    apps.append(name)
    except:
        pass
    return apps

def get_system():
    """系統來源"""
    apps = []
    for folder in [
        os.path.expandvars(r"%AppData%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
    ]:
        if os.path.exists(folder):
            for root, dirs, files in os.walk(folder):
                for f in files:
                    if f.endswith('.lnk'):
                        name = clean_name(f.replace('.lnk', ''))
                        if name:
                            apps.append(name)
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
    try:
        import win32com.client
        shell = win32com.client.Dispatch("Shell.Application")
        folder = shell.NameSpace("shell:AppsFolder")
        if folder:
            for item in folder.Items():
                name = clean_name(item.Name)
                if name:
                    apps.append(name)
    except:
        pass
    return list(set(apps))

def main():
    print("=" * 50)
    print("WinAgent All Apps Scanner")
    print("=" * 50)
    
    startapps = get_startapps()
    print(f"\nGet-StartApps: {len(startapps)}")
    
    system = get_system()
    print(f"系統來源: {len(system)}")
    
    sa_set = set(a.lower().strip() for a in startapps)
    sys_set = set(a.lower().strip() for a in system)
    
    in_both = sa_set & sys_set
    only_sa = sa_set - sys_set
    only_sys = sys_set - sa_set
    
    print(f"\n比對:")
    print(f"  共同: {len(in_both)}")
    print(f"  僅StartApps: {len(only_sa)}")
    print(f"  僅系統: {len(only_sys)}")
    
    all_apps = sorted(list(sys_set | sa_set))
    
    result = {
        'sources': {'startapps': len(startapps), 'system': len(system)},
        'total': len(all_apps),
        'only_startapps': sorted(list(only_sa)),
        'only_system': sorted(list(only_sys))[:50],
        'all_apps': all_apps
    }
    
    with open(Path(__file__).parent / "all_apps_complete.json", 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n完成! 總數: {len(all_apps)}")
    print("結果已儲存")

if __name__ == "__main__":
    main()
