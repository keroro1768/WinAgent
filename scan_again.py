import uiautomation as auto
import json

# Get window and explore all possible ways
w = auto.WindowControl(ProcessId=15872)

# Try to get direct control from window
print("=== Getting all via GetChildren ===")

controls = []

def scan(ctrl, depth=0, max_depth=8):
    if depth > max_depth:
        return
    try:
        name = (ctrl.Name or ctrl.AutomationId or '')[:50]
        ctype = str(ctrl.ControlTypeName)
        
        rect = ctrl.BoundingRectangle
        bounds = {}
        if rect and rect.width > 0:
            bounds = {'x': rect.left, 'y': rect.top, 'w': rect.width, 'h': rect.height}
        
        controls.append({
            'd': depth,
            't': ctype,
            'n': name,
            'b': bounds
        })
    except Exception as e:
        pass
    
    try:
        for c in list(ctrl.GetChildren())[:150]:
            scan(c, depth + 1, max_depth)
    except:
        pass

# Try multiple times to ensure we get data
for attempt in range(3):
    controls = []
    scan(w)
    if len(controls) > 10:
        break

print(f"Found {len(controls)} controls")

# Search for tabs
tabs = [c for c in controls if 'Tab' in c['t'] or 'Item' in c['t']]
print(f"Tab-related: {len(tabs)}")

# Show tabs
for c in tabs[:20]:
    pos = ""
    if c['b']:
        pos = f"@({c['b']['x']},{c['b']['y']})"
    print(f"  [{c['t']}] {c['n']} {pos}")

# Search by name
print("\n=== Search by Name ===")
keywords = ['home', 'view', 'break', 'time', 'model', 'script', 'source', 'memory', 'ext', 'file', 'document']
for kw in keywords:
    matches = [c for c in controls if kw in c['n'].lower()]
    if matches:
        print(f"\n'{kw}':")
        for m in matches[:5]:
            pos = ""
            if m['b']:
                pos = f"@({m['b']['x']},{m['b']['y']})"
            print(f"  [{m['t']}] {m['n']} {pos}")

# Show all controls
print("\n=== All Controls (first 30) ===")
for c in controls[:30]:
    indent = "  " * c['d']
    pos = ""
    if c['b']:
        pos = f"@({c['b']['x']},{c['b']['y']})"
    print(f"{indent}[{c['t']}] {c['n'][:30]} {pos}")
