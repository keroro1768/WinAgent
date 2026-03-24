import uiautomation as auto

w = auto.WindowControl(ProcessId=15872)

all_with_bounds = []

def scan(ctrl, depth=0):
    if depth > 6:
        return
    try:
        rect = ctrl.BoundingRectangle
        if rect and rect.width > 0:
            name = (ctrl.Name or '')[:25]
            ctype = str(ctrl.ControlTypeName)
            all_with_bounds.append({
                'depth': depth,
                'type': ctype,
                'name': name,
                'x': rect.left,
                'y': rect.top,
                'w': rect.width,
                'h': rect.height
            })
    except:
        pass
    try:
        for child in list(ctrl.GetChildren())[:80]:
            scan(child, depth+1)
    except:
        pass

scan(w)

print(f'Total elements with bounds: {len(all_with_bounds)}')

# Show all
for item in all_with_bounds[:20]:
    indent = '  ' * item['depth']
    print(f"{indent}[{item['type']}] {item['name']} @({item['x']},{item['y']}) {item['w']}x{item['h']}")
