import uiautomation as auto
import json

# Get WinDBG by PID - try different approaches
print("Trying to find WinDBG UI...")

# Method 1: WindowControl
try:
    w = auto.WindowControl(ProcessId=3088)
    if w.Exists(2):
        print("Method 1: WindowControl found")
except Exception as e:
    print(f"Method 1 failed: {e}")

# Method 2: Desktop
try:
    desktop = auto.GetRootElement()
    print(f"Desktop: {desktop.Name}")
    
    # Find children
    children = list(desktop.GetChildren())[:20]
    print(f"Desktop children: {len(children)}")
    
    # Look for WinDBG
    for c in children:
        try:
            if c.ProcessId == 3088:
                print(f"Found by PID match: {c.ControlTypeName} - {c.Name}")
        except:
            pass
except Exception as e:
    print(f"Method 2 failed: {e}")

# Method 3: EnumWindows
print("\nEnumerating top-level windows...")
results = []

def enum_callback(hwnd, extra):
    try:
        w = auto.WindowControl(NativeWindowHandle=hwnd)
        if w.ProcessId == 3088:
            results.append({
                "hwnd": hex(hwnd),
                "name": w.Name[:30] if w.Name else "",
                "type": str(w.ControlTypeName)
            })
    except:
        pass

try:
    auto.EnumWindows(enum_callback, None)
except Exception as e:
    print(f"EnumWindows failed: {e}")

print(f"Found {len(results)} windows for PID 3088")
for r in results:
    print(f"  {r}")

# Save
with open("D:/Project/WinAgent/windbg_find.json", "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print("Saved to windbg_find.json")
