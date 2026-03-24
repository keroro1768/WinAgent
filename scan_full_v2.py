import uiautomation as auto
import json

w = auto.WindowControl(ProcessId=15872)

all_controls = []

def walker(ctrl, depth=0):
    if depth > 6:
        return
    try:
        name = (ctrl.Name or ctrl.AutomationId or '')[:50]
        ctype = str(ctrl.ControlTypeName)
        
        rect = ctrl.BoundingRectangle
        bounds = {}
        if rect and rect.width > 0:
            bounds = {'x': rect.left, 'y': rect.top, 'w': rect.width, 'h': rect.height}
        
        all_controls.append({
            'd': depth,
            't': ctype,
            'n': name,
            'b': bounds
        })
    except:
        pass
    try:
        for c in list(ctrl.GetChildren())[:100]:
            walker(c, depth+1)
    except:
        pass

walker(w)

# Search for specific tabs
tabs_to_find = ['Home', 'View', 'Breakpoints', 'Time Travel', 'Model', 'Scripting', 'Source', 'Memory', 'Extensions']

print("=== Searching for Tabs ===\n")

for tab_name in tabs_to_find:
    for c in all_controls:
        if tab_name.lower() in c['n'].lower():
            pos = ""
            if c['b']:
                pos = f"@({c['b']['x']},{c['b']['y']})"
            print(f"Found: [{c['t']}] {c['n']} {pos}")

# Show all Tab/TabItem
print("\n=== All Tab Controls ===")
for c in all_controls:
    if 'Tab' in c['t']:
        pos = ""
        if c['b']:
            pos = f"@({c['b']['x']},{c['b']['y']})"
        print(f"[{c['t']}] {c['n']} {pos}")

# Save
with open('D:/Project/WinAgent/windbg_full_scan.json', 'w', encoding='utf-8', errors='ignore') as f:
    json.dump(all_controls, f, ensure_ascii=False, indent=2)

print(f"\nTotal controls: {len(all_controls)}")
print("Saved to windbg_full_scan.json")
