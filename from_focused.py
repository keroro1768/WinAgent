import uiautomation as auto

# Get the focused control and traverse from there

def get_tree(elem, depth=0, max_depth=8):
    if depth > max_depth:
        return []
    
    results = []
    try:
        name = (elem.Name or elem.AutomationId or '')[:50]
        ctype = str(elem.ControlTypeName)
        
        rect = elem.BoundingRectangle
        bounds = {}
        if rect and rect.width > 0:
            bounds = {'x': rect.left, 'y': rect.top, 'w': rect.width, 'h': rect.height}
        
        results.append({
            'depth': depth,
            'type': ctype,
            'name': name,
            'bounds': bounds
        })
    except:
        pass
    
    try:
        for child in list(elem.GetChildren())[:80]:
            results.extend(get_tree(child, depth + 1, max_depth))
    except:
        pass
    
    return results

# Start from GetFocusedControl
print("=== Starting from GetFocusedControl ===")
fg = auto.GetFocusedControl()
print(f"Focused: [{fg.ControlTypeName}] {fg.Name}")

# Traverse from focused
tree = get_tree(fg)
print(f"Total from focused: {len(tree)}")

# Search for tabs
tabs = [c for c in tree if 'Tab' in c['type']]
print(f"Tab controls: {len(tabs)}")

for t in tabs[:20]:
    pos = ""
    if t['bounds']:
        pos = f"@({t['bounds']['x']},{t['bounds']['y']})"
    print(f"  [{t['type']}] {t['name']} {pos}")

# Search by keyword
keywords = ['home', 'view', 'break', 'time', 'model', 'script', 'source', 'memory', 'ext', 'document', 'file']
print("\n=== Search by keyword ===")
for kw in keywords:
    matches = [c for c in tree if kw in c['name'].lower()]
    if matches:
        print(f"\n'{kw}':")
        for m in matches[:5]:
            pos = ""
            if m['bounds']:
                pos = f"@({m['bounds']['x']},{m['bounds']['y']})"
            print(f"  [{m['type']}] {m['name']} {pos}")

# Show first 30
print("\n=== Tree (first 30) ===")
for c in tree[:30]:
    indent = "  " * c['depth']
    print(f"{indent}[{c['type']}] {c['name']}")
