import uiautomation as auto
import json

# Get WinDBG by PID
w = auto.WindowControl(ProcessId=3088)
print('Found window')

all_controls = []

def walk(ctrl, depth=0):
    if depth > 5:
        return
    try:
        name = ctrl.Name or ctrl.AutomationId or ""
        name = name[:50]  # Truncate
        
        ctrl_type = str(ctrl.ControlTypeName)
        
        # Get bounds
        rect = ctrl.BoundingRectangle
        bounds = None
        if rect and rect.width > 0:
            bounds = {
                "x": rect.left,
                "y": rect.top,
                "w": rect.width,
                "h": rect.height
            }
        
        all_controls.append({
            "depth": depth,
            "type": ctrl_type,
            "name": name,
            "bounds": bounds
        })
    except:
        pass
    
    try:
        for child in list(ctrl.GetChildren())[:50]:
            walk(child, depth + 1)
    except:
        pass

walk(w)

# Group by type
by_type = {}
for c in all_controls:
    t = c["type"]
    if t not in by_type:
        by_type[t] = []
    by_type[t].append(c)

# Save to file
output = {
    "app": "WinDBG",
    "pid": 3088,
    "total": len(all_controls),
    "by_type": {t: len(c) for t, c in by_type.items()},
    "controls": all_controls[:200]  # Limit
}

with open("D:/Project/WinAgent/windbg_ui.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Saved {len(all_controls)} controls")
print("Types:", list(by_type.keys()))
