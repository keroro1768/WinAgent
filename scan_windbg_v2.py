import uiautomation as auto
import json

# Get WinDBG by PID
w = auto.WindowControl(ProcessId=3088)
print('Got window control')

controls = []

def scan(ctrl, depth=0, max_depth=6, max_children=80):
    if depth > max_depth:
        return
    
    try:
        # Get info
        name = ""
        try:
            name = ctrl.Name or ""
            if not name:
                name = ctrl.AutomationId or ""
        except:
            name = "(error)"
        
        # Truncate name for safety
        name = name[:40]
        
        ctrl_type = str(ctrl.ControlTypeName)
        
        # Bounds
        bounds = {}
        try:
            rect = ctrl.BoundingRectangle
            if rect and rect.width > 0:
                bounds = {
                    "left": rect.left,
                    "top": rect.top,
                    "right": rect.right,
                    "bottom": rect.bottom,
                    "width": rect.width,
                    "height": rect.height
                }
        except:
            pass
        
        controls.append({
            "depth": depth,
            "type": ctrl_type,
            "name": name,
            "bounds": bounds
        })
        
    except Exception as e:
        pass
    
    # Children
    try:
        children = list(ctrl.GetChildren())[:max_children]
        for child in children:
            scan(child, depth + 1, max_depth, max_children)
    except:
        pass

print('Starting scan...')
scan(w)

# Stats
by_type = {}
for c in controls:
    t = c["type"]
    by_type[t] = by_type.get(t, 0) + 1

print(f'\nTotal controls: {len(controls)}')
print('\nBy type:')
for t, cnt in sorted(by_type.items(), key=lambda x: -x[1]):
    print(f'  {t}: {cnt}')

# Show all
print('\nAll controls:')
for c in controls[:50]:
    indent = "  " * c["depth"]
    b = c.get("bounds", {})
    pos = ""
    if b:
        pos = f" @({b.get('left',0)},{b.get('top',0)})"
    print(f"{indent}[{c['type']}] {c['name'][:35]}{pos}")

# Save
output = {
    "app": "WinDBG",
    "pid": 3088,
    "total": len(controls),
    "by_type": by_type,
    "controls": controls[:300]
}

with open("D:/Project/WinAgent/windbg_ui.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'\nSaved to windbg_ui.json')
