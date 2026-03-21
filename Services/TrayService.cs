using System.Windows.Forms;
using WinAgent.Native;

namespace WinAgent.Services;

public class TrayService : IDisposable
{
    private NotifyIcon? _notifyIcon;
    private ContextMenuStrip? _contextMenu;
    private readonly Form _mainForm;
    private bool _disposed = false;
    private ToolStripMenuItem? _alwaysOnTopItem;

    public event Action? OnShowClicked;
    public event Action? OnExitClicked;
    public event Action? OnStatusClicked;
    public event Action<bool>? OnAlwaysOnTopChanged;

    public bool AlwaysOnTop
    {
        get => _alwaysOnTopItem?.Checked ?? false;
        set
        {
            if (_alwaysOnTopItem != null)
            {
                _alwaysOnTopItem.Checked = value;
                _mainForm.TopMost = value;
                OnAlwaysOnTopChanged?.Invoke(value);
                Logger.Log($"Always on Top: {value}");
            }
        }
    }

    public TrayService(Form mainForm)
    {
        _mainForm = mainForm;
    }

    public void Initialize()
    {
        // Create context menu
        _contextMenu = new ContextMenuStrip();
        
        var showItem = new ToolStripMenuItem("Show Window", null, (s, e) => OnShowClicked?.Invoke());
        _alwaysOnTopItem = new ToolStripMenuItem("Always on Top", null, (s, e) => AlwaysOnTop = !AlwaysOnTop)
        {
            CheckOnClick = true
        };
        var statusItem = new ToolStripMenuItem("Status", null, (s, e) => OnStatusClicked?.Invoke());
        var separator1 = new ToolStripSeparator();
        var hideItem = new ToolStripMenuItem("Hide Window (Ctrl+H)", null, (s, e) => OnShowClicked?.Invoke());
        var separator2 = new ToolStripSeparator();
        var exitItem = new ToolStripMenuItem("Exit", null, (s, e) => OnExitClicked?.Invoke());

        _contextMenu.Items.AddRange(new ToolStripItem[] { showItem, _alwaysOnTopItem, statusItem, separator1, hideItem, separator2, exitItem });

        // Create notify icon
        _notifyIcon = new NotifyIcon
        {
            Icon = SystemIcons.Application,
            Text = "WinAgent - Running",
            Visible = true,
            ContextMenuStrip = _contextMenu
        };

        // Handle click to show window
        _notifyIcon.Click += (s, e) => OnShowClicked?.Invoke();
        _notifyIcon.DoubleClick += (s, e) => OnShowClicked?.Invoke();

        Logger.Log("Tray service initialized");
    }

    public void UpdateStatus(string status)
    {
        if (_notifyIcon != null)
        {
            _notifyIcon.Text = $"WinAgent - {status}";
        }
    }

    public void SetIcon(bool isRunning)
    {
        if (_notifyIcon != null)
        {
            // Could set different icons based on state
            _notifyIcon.Icon = isRunning ? SystemIcons.Shield : SystemIcons.Application;
        }
    }

    public void ShowBalloon(string title, string message, ToolTipIcon icon = ToolTipIcon.Info)
    {
        _notifyIcon?.ShowBalloonTip(5000, title, message, icon);
    }

    public void Dispose()
    {
        if (_disposed) return;

        if (_notifyIcon != null)
        {
            _notifyIcon.Visible = false;
            _notifyIcon.Dispose();
            _notifyIcon = null;
        }

        _contextMenu?.Dispose();
        _disposed = true;
    }
}