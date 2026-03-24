import uiautomation as auto

w = auto.WindowControl(ProcessId=15872)
print('Window:', w.ProcessId)

results = []

def walker(ctrl, depth):
    if depth > 5:
        return
    try:
        name = (ctrl.Name or ctrl.AutomationId or '?')[:30]
        ctype = str(ctrl.ControlTypeName)
        results.append({'d': depth, 't': ctype, 'n': name})
    except:
        pass
    try:
        for c in list(ctrl.GetChildren())[:50]:
            walker(c, depth+1)
    except:
        pass

walker(w, 0)

print('Total:', len(results))

# Stats
types = {}
for r in results:
    t = r['t']
    types[t] = types.get(t, 0) + 1

print('Types:', types)

# Show all
for r in results[:40]:
    indent = '  ' * r['d']
    print(f"{indent}[{r['t']}] {r['n']}")
