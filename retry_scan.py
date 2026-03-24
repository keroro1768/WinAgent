import uiautomation as auto
import time

# Retry function with consistent results
def scan_with_wait():
    # Wait a bit for UI to stabilize
    time.sleep(0.5)
    
    # Get window
    w = auto.WindowControl(ProcessId=15872)
    
    # Get focused
    fg = auto.GetFocusedControl()
    
    print(f"Focused: [{fg.ControlTypeName}] {fg.Name}")
    
    # Try to get children from focused
    results = []
    
    def get_kids(elem, depth=0):
        if depth > 6:
            return
        try:
            name = (elem.Name or elem.AutomationId or '')[:40]
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
            for child in list(elem.GetChildren())[:100]:
                get_kids(child, depth+1)
        except:
            pass
    
    get_kids(fg)
    return results

# Try multiple times
print("Attempt 1:")
tree1 = scan_with_wait()
print(f"  Found: {len(tree1)}")

print("\nAttempt 2:")
tree2 = scan_with_wait()
print(f"  Found: {len(tree2)}")

# Use the one with results
tree = tree1 if len(tree1) > len(tree2) else tree2
if len(tree) == 0:
    tree = tree1

print(f"\nUsing: {len(tree)} controls")

# Show all
print("\n=== All Controls ===")
for c in tree[:50]:
    indent = "  " * c['depth']
    pos = ""
    if c['bounds']:
        pos = f"@({c['bounds']['x']},{c['bounds']['y']})"
    print(f"{indent}[{c['type']}] {c['name']} {pos}")

# Search for tabs
print("\n=== Tab-like ===")
for c in tree:
    if 'Tab' in c['type'] or 'Item' in c['type']:
        pos = ""
        if c['bounds']:
            pos = f"@({c['bounds']['x']},{c['bounds']['y']})"
        print(f"  [{c['type']}] {c['name']} {pos}")

# Search by keyword
print("\n=== By Keyword ===")
for kw in ['home', 'view', 'break', 'memory', 'source', 'script']:
    for c in tree:
        if kw in c['name'].lower():
            pos = ""
            if c['bounds']:
                pos = f"@({c['bounds']['x']},{c['bounds']['y']})"
            print(f"  [{c['type']}] {c['name']} {pos}")
            break
