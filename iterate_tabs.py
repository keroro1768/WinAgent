import uiautomation as auto
import time

# Get focused
fg = auto.GetFocusedControl()
print(f"Focused: [{fg.ControlTypeName}] {fg.Name}")

# Get children
time.sleep(0.2)

# Find TabControl
children = fg.GetChildren()
child_list = []

# Convert iterator to list manually
for child in children:
    child_list.append(child)
    if len(child_list) > 20:
        break

print(f"Children: {len(child_list)}")

# Find TabControl
for child in child_list:
    if 'Tab' in str(child.ControlTypeName):
        print(f"\nFound: {child.ControlTypeName}")
        
        # Get its children
        tab_children = child.GetChildren()
        
        # Iterate
        idx = 0
        for tc in tab_children:
            try:
                name = tc.Name or ""
                if not name:
                    name = tc.AutomationId or ""
                ctype = str(tc.ControlTypeName)
                
                rect = tc.BoundingRectangle
                pos = ""
                if rect and rect.width > 0:
                    pos = f"@({rect.left},{rect.top})"
                
                print(f"  {idx}: [{ctype}] '{name}' {pos}")
                idx += 1
                
                if idx > 20:
                    break
            except Exception as e:
                idx += 1
                if idx > 20:
                    break
        
        break
