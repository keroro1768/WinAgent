import uiautomation as auto
import ctypes
import time

user32 = ctypes.windll.user32
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

def click_at(x, y):
    user32.SetCursorPos(x, y)
    time.sleep(0.05)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

w = auto.WindowControl(ProcessId=15872)

# Find all buttons with coordinates
def find_all_buttons(ctrl, depth=0):
    results = []
    if depth > 6:
        return results
    
    try:
        ctype = str(ctrl.ControlTypeName)
        name = (ctrl.Name or '')[:30]
        rect = ctrl.BoundingRectangle
        
        if rect and rect.width > 0 and ('Button' in ctype or 'Tab' in ctype):
            cx = (rect.left + rect.right) // 2
            cy = (rect.top + rect.bottom) // 2
            results.append({'type': ctype, 'name': name, 'x': cx, 'y': cy})
    except:
        pass
    
    try:
        for child in list(ctrl.GetChildren())[:80]:
            results.extend(find_all_buttons(child, depth+1))
    except:
        pass
    
    return results

buttons = find_all_buttons(w)
print(f'Found {len(buttons)} clickable items')

# Show first 15
for b in buttons[:15]:
    print(f"  [{b['type']}] {b['name']} @({b['x']},{b['y']})")

# Click on a tab - Command tab
target = None
for b in buttons:
    if 'Command' in b['name']:
        target = b
        break

if not target and buttons:
    # Click first available button
    target = buttons[0]

if target:
    print(f'\nClicking: {target["name"]} @({target["x"]},{target["y"]})')
    click_at(target['x'], target['y'])
    print('Done!')
else:
    print('No clickable items found')
