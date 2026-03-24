import uiautomation as auto
import time

# Get focused
fg = auto.GetFocusedControl()
print(f"Focused: [{fg.ControlTypeName}] {fg.Name}")

# Get children
time.sleep(0.2)
kids = list(fg.GetChildren())
print(f"Children: {len(kids)}")

for k in kids:
    print(f"\n=== {k.ControlTypeName}: {k.Name} ===")
    
    # Get children of this child
    try:
        subkids = list(k.GetChildren())[:50]
        print(f"Sub-children: {len(subkids)}")
        
        for sk in subkids[:30]:
            try:
                name = sk.Name or sk.AutomationId or ""
                ctype = sk.ControlTypeName
                
                rect = sk.BoundingRectangle
                pos = ""
                if rect and rect.width > 0:
                    pos = f"@({rect.left},{rect.top})"
                
                print(f"  [{ctype}] {name[:40]} {pos}")
            except:
                pass
    except Exception as e:
        print(f"Error: {e}")

# Also try getting TabControl directly
print("\n\n=== Searching for TabControl ===")
all_items = []

def search(ctrl, depth=0):
    if depth > 8:
        return
    try:
        ctype = str(ctrl.ControlTypeName)
        name = (ctrl.Name or ctrl.AutomationId or '')[:40]
        
        rect = ctrl.BoundingRectangle
        bounds = {}
        if rect and rect.width > 0:
            bounds = {'x': rect.left, 'y': rect.top}
        
        all_items.append({'type': ctype, 'name': name, 'bounds': bounds})
    except:
        pass
    
    try:
        for c in list(ctrl.GetChildren())[:100]:
            search(c, depth+1)
    except:
        pass

search(fg)

# Find all tabs
tabs = [i for i in all_items if 'Tab' in i['type']]
print(f"Found {len(tabs)} tab items")
for t in tabs:
    pos = f"@({t['bounds']['x']},{t['bounds']['y']})" if t['bounds'] else ""
    print(f"  [{t['type']}] {t['name']} {pos}")
