import uiautomation as auto
import time

# Get focused
fg = auto.GetFocusedControl()
print(f"Focused: [{fg.ControlTypeName}] {fg.Name}")

# Get children
time.sleep(0.2)
kids = list(fg.GetChildren())

for k in kids:
    print(f"\n=== {k.ControlTypeName}: {k.Name} ===")
    
    # Get subchildren
    try:
        subkids = list(k.GetChildren())
        print(f"Sub-children count: {len(subkids)}")
        
        # Try to get each item
        for i, sk in enumerate(subkids):
            try:
                name = sk.Name or ""
                if not name:
                    name = sk.AutomationId or ""
                ctype = str(sk.ControlTypeName)
                
                rect = sk.BoundingRectangle
                pos = ""
                if rect and rect.width > 0:
                    pos = f"@({rect.left},{rect.top})"
                
                print(f"  {i}: [{ctype}] '{name}' {pos}")
            except Exception as e:
                print(f"  {i}: Error - {e}")
    except Exception as e:
        print(f"Error getting children: {e}")

# Also try with indexing
print("\n\n=== Try GetChild method ===")
try:
    tab = kids[0]
    print(f"Tab: {tab.ControlTypeName}")
    
    # Try different ways to get children
    for i in range(10):
        try:
            child = tab.GetChild(i)
            if child:
                name = child.Name or child.AutomationId or ""
                print(f"  Child {i}: [{child.ControlTypeName}] {name}")
        except:
            pass
except Exception as e:
    print(f"Error: {e}")
