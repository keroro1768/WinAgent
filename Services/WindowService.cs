using System.Diagnostics;
using System.Text;
using WinAgent.Native;
using WinAgent.Models;

namespace WinAgent.Services;

public class WindowService
{
    private const uint EVENT_MIN = Win32.EVENT_SYSTEM_FOREGROUND;
    private const uint EVENT_MAX = Win32.EVENT_SYSTEM_FOREGROUND;

    private IntPtr _winEventHook = IntPtr.Zero;
    private Win32.WinEventProc? _winEventProc;
    private WindowInfo? _lastForegroundWindow;
    private readonly object _lock = new();

    public event Action<WindowInfo>? ForegroundWindowChanged;

    public WindowInfo GetForegroundWindow()
    {
        IntPtr hwnd = Win32.GetForegroundWindow();
        return GetWindowInfo(hwnd);
    }

    public WindowInfo GetWindowInfo(IntPtr hwnd)
    {
        var info = new WindowInfo { Handle = hwnd };

        if (hwnd == IntPtr.Zero)
            return info;

        // Get window text
        int length = Win32.GetWindowTextLength(hwnd);
        if (length > 0)
        {
            StringBuilder sb = new StringBuilder(length + 1);
            Win32.GetWindowText(hwnd, sb, sb.Capacity);
            info.Title = sb.ToString();
        }

        // Get class name
        StringBuilder className = new StringBuilder(256);
        Win32.GetClassName(hwnd, className, className.Capacity);
        info.ClassName = className.ToString();

        // Get process info
        Win32.GetWindowThreadProcessId(hwnd, out uint processId);
        info.ProcessId = (int)processId;

        try
        {
            var process = Process.GetProcessById(info.ProcessId);
            info.ProcessName = process.ProcessName;
        }
        catch
        {
            info.ProcessName = "Unknown";
        }

        return info;
    }

    public void StartMonitoring()
    {
        if (_winEventHook != IntPtr.Zero)
            return;

        _winEventProc = OnWinEvent;
        _winEventHook = Win32.SetWinEventHook(
            EVENT_MIN,
            EVENT_MAX,
            IntPtr.Zero,
            _winEventProc,
            0,
            0,
            Win32.WINEVENT_OUTOFCONTEXT | Win32.WINEVENT_SKIPOWNPROCESS
        );

        Logger.Log($"Window monitoring started");
    }

    public void StopMonitoring()
    {
        if (_winEventHook != IntPtr.Zero)
        {
            Win32.UnhookWinEvent(_winEventHook);
            _winEventHook = IntPtr.Zero;
            Logger.Log($"Window monitoring stopped");
        }
    }

    private void OnWinEvent(IntPtr hWinEventHook, uint eventType, IntPtr hwnd, int idObject, int idChild, uint dwEventThread, uint dwmsEventTime)
    {
        if (eventType == Win32.EVENT_SYSTEM_FOREGROUND && hwnd != IntPtr.Zero)
        {
            var windowInfo = GetWindowInfo(hwnd);
            
            lock (_lock)
            {
                if (_lastForegroundWindow?.Handle != windowInfo.Handle)
                {
                    _lastForegroundWindow = windowInfo;
                    ForegroundWindowChanged?.Invoke(windowInfo);
                    Logger.Log($"Foreground window changed: {windowInfo}");
                }
            }
        }
    }
}