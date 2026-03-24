import uiautomation as auto

# Get focused control and explore the tree from there

print("=== Focused Control ===")
fg = auto.GetFocusedControl()
print(f"Focused: [{fg.ControlTypeName}] {fg.Name}")

# Get all children from focused
print("\n=== Children of Focused ===")

def get_children(elem, depth=0, max_depth=5):
    if depth > max_depth:
        return []
    
    results = []
    try:
        children = list(elem.GetChildren())[:50]
        for child in children:
            try:
                name = child.Name or child.AutomationId or ""
                ctype = str(child.ControlTypeName)
                results.append({
                    'depth': depth,
                    'type': ctype,
                    'name': name[:40]
                })
                results.extend(get_children(child, depth+1, max_depth))
            except:
                pass
    except:
        pass
    
    return results

children = get_children(fg)
print(f"Total: {len(children)}")

# Show all
for c in children[:40]:
    indent = "  " * c['depth']
    print(f"{indent}[{c['type']}] {c['name']}")

# Also try from the root
print("\n=== From Root Window ===")
w = auto.WindowControl(ProcessId=15872)

# Try GetFirstChild / GetNextSibling
print("\n=== First Children ===")
try:
    walker = auto.TreeWalkerControlViewWalker
    if walker:
        child = walker.GetFirstChild(w)
        print(f"First child: {child}")
        if child:
            print(f"  Type: {child.ControlTypeName}")
            print(f"  Name: {child.Name}")
except Exception as e:
    print(f"Error: {e}")
