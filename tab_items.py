import uiautomation as auto
import time

# Get focused
fg = auto.GetFocusedControl()
print(f"Focused: [{fg.ControlTypeName}] {fg.Name}")

# Get children using iterator
time.sleep(0.2)

# Try getting children properly
children = []
try:
    # Using GetChildren method
    children = fg.GetChildren()
    # Convert to list
    children_list = list(children)
except Exception as e:
    print(f"Error getting children: {e}")

print(f"Children count: {len(children_list)}")

# Find TabControl
tab_control = None
for child in children_list:
    if 'Tab' in str(child.ControlTypeName):
        tab_control = child
        print(f"\nFound TabControl: {child.ControlTypeName}")
        break

if tab_control:
    # Get TabControl's children
    try:
        tab_children = list(tab_control.GetChildren())
        print(f"Tab children: {len(tab_children)}")
        
        for i, tc in enumerate(tab_children):
            try:
                name = tc.Name or tc.AutomationId or ""
                ctype = str(tc.ControlTypeName)
                
                rect = tc.BoundingRectangle
                pos = ""
                if rect and rect.width > 0:
                    pos = f"@({rect.left},{rect.top})"
                
                print(f"  {i}: [{ctype}] '{name}' {pos}")
            except Exception as e:
                print(f"  {i}: Error - {e}")
    except Exception as e:
        print(f"Error: {e}")
