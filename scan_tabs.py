import uiautomation as auto
import json

w = auto.WindowControl(ProcessId=15872)

controls = []

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
        
        controls.append({
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

# Find all Tab and TabItem
tabs = [c for c in controls if 'Tab' in c['t']]

print('Found tabs:')
for t in tabs:
    pos = ''
    if t['b']:
        pos = f"@({t['b']['x']},{t['b']['y']})"
    print(f"  [{t['t']}] {t['n']} {pos}")

# Save all
with open('D:/Project/WinAgent/windbg_tabs.json', 'w', encoding='utf-8', errors='ignore') as f:
    json.dump({'tabs': tabs, 'all': controls[:150]}, f, ensure_ascii=False, indent=2)

print(f'\nTotal: {len(tabs)} tabs')
print('Saved to windbg_tabs.json')
