import uiautomation as auto
import json
import time

# Retry function
def scan_with_retry(pid, max_retries=3):
    for attempt in range(max_retries):
        print(f'Attempt {attempt + 1}...')
        
        w = auto.WindowControl(ProcessId=pid)
        
        # Try to access
        try:
            test = w.GetFirstChild()
        except:
            time.sleep(0.5)
            continue
        
        controls = []
        
        def walker(ctrl, depth):
            if depth > 6:
                return
            try:
                name = (ctrl.Name or ctrl.AutomationId or '')[:40]
                ctype = str(ctrl.ControlTypeName)
                
                rect = ctrl.BoundingRectangle
                bounds = {}
                if rect and rect.width > 0:
                    bounds = {'x': rect.left, 'y': rect.top, 'w': rect.width, 'h': rect.height}
                
                controls.append({'d': depth, 't': ctype, 'n': name, 'b': bounds})
            except:
                pass
            try:
                for c in list(ctrl.GetChildren())[:80]:
                    walker(c, depth+1)
            except:
                pass
        
        walker(w, 0)
        
        if len(controls) > 0:
            return controls
        
        time.sleep(0.5)
    
    return controls

controls = scan_with_retry(15872)

# Stats
types = {}
for c in controls:
    t = c['t']
    types[t] = types.get(t, 0) + 1

buttons = [c for c in controls if 'Button' in c['t']]

print('\nTotal:', len(controls))
print('By type:', types)
print('\nButtons:', len(buttons))

for b in buttons[:25]:
    indent = '  ' * b['d']
    pos = f"@({b['b'].get('x',0)},{b['b'].get('y',0)})" if b['b'] else ""
    print(f"{indent}[{b['t']}] {b['n']} {pos}")

# Save
with open('D:/Project/WinAgent/windbg_scan.json', 'w', encoding='utf-8', errors='ignore') as f:
    json.dump({'app': 'WinDBG', 'pid': 15872, 'total': len(controls), 'by_type': types, 'buttons': buttons, 'all': controls}, f, ensure_ascii=False, indent=2)

print('\nSaved')
