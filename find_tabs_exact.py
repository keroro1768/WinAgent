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

# Search for specific tab names
tab_names = ['Home', 'View', 'Breakpoints', 'Time Travel', 'Model', 'Scripting', 'Source', 'Memory', 'Extensions', '文件']

found = []

for c in controls:
    name_lower = c['n'].lower()
    for tab in tab_names:
        if tab.lower() in name_lower:
            pos = ''
            if c['b']:
                pos = f"@({c['b']['x']},{c['b']['y']})"
            found.append({'name': c['n'], 'type': c['t'], 'pos': pos})
            print(f"Found: [{c['t']}] {c['n']} {pos}")

if not found:
    print('No tabs found')
    
    # Show all items that might be tabs
    print('\nAll items with relevant keywords:')
    keywords = ['home','view','break','time','model','script','source','memory','ext','note','command']
    for c in controls:
        if any(x in c['n'].lower() for x in keywords):
            print(f"  [{c['t']}] {c['n']}")

# Save
with open('D:/Project/WinAgent/windbg_tabs2.json', 'w', encoding='utf-8', errors='ignore') as f:
    json.dump({'found': found, 'all': controls[:150]}, f, ensure_ascii=False, indent=2)
