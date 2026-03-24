import uiautomation as auto
import ctypes
from ctypes import wintypes, POINTER

# Try multiple approaches

# 1. GetFocusedControl
print("=== 1. GetFocusedControl ===")
try:
    fg = auto.GetFocusedControl()
    print(f"Focused: {fg.ControlTypeName} - {fg.Name}")
except Exception as e:
    print(f"Error: {e}")

# 2. GetAutomationId
print("\n=== 2. GetAutomationId ===")
w = auto.WindowControl(ProcessId=15872)
try:
    ids = w.GetAllAutomationIds()
    print(f"IDs count: {len(ids) if ids else 0}")
    if ids:
        for i in ids[:10]:
            print(f"  {i}")
except Exception as e:
    print(f"Error: {e}")

# 3. AccessibleObjectFromWindow (COM)
print("\n=== 3. AccessibleObjectFromWindow ===")
user32 = ctypes.windll.user32
hwnd = 0x50720

try:
    class IUnknown(ctypes.Structure):
        _fields_ = [("lpVtbl", ctypes.c_void_p)]
    
    iid = ctypes.create_string_buffer(b'{618736E0-3C3D-11CF-810C-00AA00389B71}')
    acc = ctypes.c_void_p()
    
    result = user32.AccessibleObjectFromWindow(
        hwnd,
        -4,  # OBJID_CLIENT
        ctypes.byref(iid),
        ctypes.byref(acc)
    )
    print(f"Result: {result}, Acc: {acc.value}")
except Exception as e:
    print(f"Error: {e}")

# 4. Try IUIAutomation with element array
print("\n=== 4. FindAll with condition ===")
try:
    # Try to find all elements
    condition = auto.TrueCondition
    elements = w.FindAll(auto.TreeScope.TreeScope_Descendants, condition)
    print(f"Found {len(elements)} elements")
    
    # Show first 20
    for i, elem in enumerate(elements[:20]):
        try:
            name = elem.Name or ""
            ctype = str(elem.ControlTypeName)
            print(f"  {i}: [{ctype}] {name[:30]}")
        except:
            pass
except Exception as e:
    print(f"Error: {e}")
