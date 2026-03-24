"""
Simple UI Scanner for WinDBG
"""

import uiautomation as auto
import json
import time

def scan_foreground():
    fg = auto.GetForegroundWindow()
    if not fg:
        print("No foreground window")
        return
    
    print(f"Foreground HWND: {hex(fg)}")
    
    # Get window
    window = auto.WindowControl(NativeWindowHandle=fg)
    print(f"Window Name: {window.Name}")
    print(f"Process ID: {window.ProcessId}")
    
    # Scan controls
    results = []
    
    def scan(ctrl, depth=0):
        if depth > 4:
            return
        
        try:
            ct = str(ctrl.ControlTypeName)
            name = ctrl.Name or ctrl.AutomationId or "(no name)"
            
            results.append({
                "depth": depth,
                "type": ct,
                "name": name[:50]
            })
        except:
            pass
        
        try:
            for child in list(ctrl.GetChildren())[:30]:
                scan(child, depth + 1)
        except:
            pass
    
    scan(window)
    
    # Group by type
    by_type = {}
    for r in results:
        t = r["type"]
        if t not in by_type:
            by_type[t] = []
        by_type[t].append(r)
    
    print(f"\nTotal: {len(results)} controls")
    print("\nBy type:")
    for t, items in sorted(by_type.items(), key=lambda x: -len(x[1])):
        print(f"  {t}: {len(items)}")
    
    # Show first 20 items
    print("\nControls (first 20):")
    for r in results[:20]:
        print(f"  [{r['type']}] {r['name']}")
    
    # Save
    with open("windbg_scan.json", "w", encoding="utf-8") as f:
        json.dump({
            "window": window.Name,
            "pid": window.ProcessId,
            "total": len(results),
            "by_type": {t: len(i) for t, i in by_type.items()},
            "controls": results
        }, f, ensure_ascii=False, indent=2)
    
    print("\nSaved to windbg_scan.json")

if __name__ == "__main__":
    scan_foreground()
