import uiautomation as auto
import json
import sys

# Set output encoding
sys.stdout.reconfigure(encoding='utf-8', errors='ignore')
sys.stderr.reconfigure(encoding='utf-8', errors='ignore')

# Get WinDBG
w = auto.WindowControl(ProcessId=3088)
controls = []

def scan(ctrl, depth=0, max_depth=6, max_children=100):
    if depth > max_depth:
        return
    
    try:
        name = ""
        try:
            name = ctrl.Name or ""
            if not name:
                name = ctrl.AutomationId or ""
        except:
            name = "(error)"
        
        # Clean name
        name = name[:40].replace('\n', ' ').replace('\r', '')
        
        ctrl_type = str(ctrl.ControlTypeName)
        
        bounds = {}
        try:
            rect = ctrl.BoundingRectangle
            if rect and rect.width > 0:
                bounds = {"x": rect.left, "y": rect.top, "w": rect.width, "h": rect.height}
        except:
            pass
        
        controls.append({
            "depth": depth,
            "type": ctrl_type,
            "name": name,
            "bounds": bounds
        })
    except:
        pass
    
    try:
        for child in list(ctrl.GetChildren())[:max_children]:
            scan(child, depth + 1, max_depth, max_children)
    except:
        pass

scan(w)

# Stats
by_type = {}
for c in controls:
    t = c["type"]
    by_type[t] = by_type.get(t, 0) + 1

# Save JSON first (before print to avoid encoding issues)
output = {
    "app": "WinDBG",
    "pid": 3088,
    "total": len(controls),
    "by_type": by_type,
    "controls": controls[:300]
}

with open("D:/Project/WinAgent/windbg_ui.json", "w", encoding="utf-8", errors='ignore') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Total: {len(controls)}")
print(f"Types: {by_type}")

# Now print safely
for c in controls[:30]:
    print(f"{c['depth']}: [{c['type']}] {c['name']}")
