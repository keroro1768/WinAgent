using System;
using System.Drawing;
using System.Windows.Forms;
using System.Runtime.InteropServices;
using System.Diagnostics;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using WinAgent.Services;

namespace WinAgent
{
    static class Program
    {
        [DllImport("user32.dll")]
        static extern IntPtr GetForegroundWindow();

        [DllImport("user32.dll")]
        static extern int GetWindowText(IntPtr hWnd, System.Text.StringBuilder text, int count);

        [DllImport("user32.dll")]
        static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

        [DllImport("user32.dll")]
        static extern bool SetWindowPos(IntPtr hWnd, IntPtr hWndInsertAfter, int X, int Y, int cx, int cy, uint uFlags);

        [DllImport("user32.dll")]
        static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

        [DllImport("user32.dll")]
        static extern IntPtr FindWindow(string? lpClassName, string lpWindowName);

        [DllImport("user32.dll")]
        static extern IntPtr FindWindowEx(IntPtr hwndParent, IntPtr hwndChildAfter, string? lpszClass, string? lpszWindow);

        [DllImport("user32.dll")]
        static extern IntPtr GetDlgItem(IntPtr hDlg, int nIDDlgItem);

        [DllImport("user32.dll")]
        static extern int GetWindowTextLength(IntPtr hWnd);

        [DllImport("user32.dll")]
        static extern bool EnumChildWindows(IntPtr hWnd, EnumWindowsProc lpEnumFunc, IntPtr lParam);

        [DllImport("user32.dll")]
        static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

        [DllImport("user32.dll")]
        static extern IntPtr GetAncestor(IntPtr hwnd, uint gaFlags);

        delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

        [StructLayout(LayoutKind.Sequential)]
        struct RECT
        {
            public int Left, Top, Right, Bottom;
        }

        const uint SWP_NOSIZE = 0x0001;
        const uint SWP_NOMOVE = 0x0002;
        const uint SWP_NOZORDER = 0x0004;
        const uint SWP_SHOWWINDOW = 0x0040;
        const int SW_HIDE = 0;
        const int SW_SHOW = 5;
        const uint GA_ROOT = 2;

        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new MainForm());
        }

        public class MainForm : Form
        {
            private CheckBox chkAlwaysOnTop;
            private Button btnHide;
            private TreeView treeControls;
            private TextBox txtInput;
            private Button btnSendText;
            private Button btnClick;
            private Button btnKeyEnter;
            private Button btnKeyTab;
            private Label lblInputMethod;
            private SplitContainer splitContainer;
            private Panel topPanel;
            private Panel bottomPanel;
            private bool isVisible = true;

            private IntPtr targetWindowHandle = IntPtr.Zero;
            private System.Windows.Forms.Timer foregroundTimer;

            public MainForm()
            {
                InitializeComponent();
                StartForegroundMonitoring();
                LoadSettings();
            }

            private void InitializeComponent()
            {
                this.Text = "WinAgent - UI Spy";
                this.Size = new Size(500, 700);
                this.MinimumSize = new Size(450, 600);
                this.FormBorderStyle = FormBorderStyle.Sizable;
                this.MaximizeBox = true;
                this.StartPosition = FormStartPosition.CenterScreen;

                // Top Panel
                topPanel = new Panel
                {
                    Dock = DockStyle.Top,
                    Height = 50,
                    Padding = new Padding(10)
                };

                chkAlwaysOnTop = new CheckBox
                {
                    Text = "Always on Top",
                    AutoSize = true,
                    Font = new Font("Arial", 12, FontStyle.Bold),
                    Location = new Point(10, 10)
                };
                chkAlwaysOnTop.CheckedChanged += (s, e) => 
                {
                    this.TopMost = chkAlwaysOnTop.Checked;
                    SaveSettings();
                };

                btnHide = new Button
                {
                    Text = "Hide/Show (Ctrl+H)",
                    AutoSize = true,
                    Location = new Point(200, 8),
                    Padding = new Padding(10, 5, 10, 5)
                };
                btnHide.Click += (s, e) => ToggleVisibility();

                topPanel.Controls.Add(chkAlwaysOnTop);
                topPanel.Controls.Add(btnHide);

                // Bottom Panel
                bottomPanel = new Panel
                {
                    Dock = DockStyle.Bottom,
                    Height = 120,
                    Padding = new Padding(10)
                };

                int yPos = 10;
                int labelY = 10;
                
                var lblInput = new Label { Text = "Input:", Location = new Point(10, labelY), AutoSize = true };
                bottomPanel.Controls.Add(lblInput);

                txtInput = new TextBox
                {
                    Location = new Point(70, yPos),
                    Size = new Size(250, 25),
                    PlaceholderText = "Enter text to send..."
                };
                bottomPanel.Controls.Add(txtInput);

                int btnX = 330;
                btnSendText = new Button { Text = "Send", Location = new Point(btnX, yPos - 2), Size = new Size(60, 28) };
                btnSendText.Click += BtnSendText_Click;
                bottomPanel.Controls.Add(btnSendText);

                yPos = 38;
                int btnY = 38;
                btnClick = new Button { Text = "Click", Location = new Point(10, btnY), Size = new Size(80, 28) };
                btnClick.Click += BtnClick_Click;
                bottomPanel.Controls.Add(btnClick);

                btnKeyEnter = new Button { Text = "Enter", Location = new Point(100, btnY), Size = new Size(80, 28) };
                btnKeyEnter.Click += BtnKeyEnter_Click;
                bottomPanel.Controls.Add(btnKeyEnter);

                btnKeyTab = new Button { Text = "Tab", Location = new Point(190, btnY), Size = new Size(80, 28) };
                btnKeyTab.Click += BtnKeyTab_Click;
                bottomPanel.Controls.Add(btnKeyTab);

                lblInputMethod = new Label 
                { 
                    Text = "IME: Checking...", 
                    Location = new Point(10, 75), 
                    AutoSize = true,
                    ForeColor = Color.Gray
                };
                bottomPanel.Controls.Add(lblInputMethod);

                // TreeView
                treeControls = new TreeView
                {
                    Dock = DockStyle.Fill,
                    Font = new Font("Consolas", 10),
                    FullRowSelect = true,
                    HideSelection = false
                };
                treeControls.AfterSelect += TreeControls_AfterSelect;

                // SplitContainer
                splitContainer = new SplitContainer
                {
                    Dock = DockStyle.Fill,
                    Orientation = Orientation.Vertical,
                    SplitterDistance = this.Height - 200
                };
                splitContainer.Panel1.Controls.Add(treeControls);
                splitContainer.Panel2.Controls.Add(bottomPanel);

                this.Controls.Add(topPanel);
                this.Controls.Add(splitContainer);

                // Keyboard shortcuts
                this.KeyPreview = true;
                this.KeyDown += MainForm_KeyDown;

                this.FormClosing += (s, e) => 
                {
                    e.Cancel = true;
                    this.Hide();
                };
            }

            private void MainForm_KeyDown(object? sender, KeyEventArgs e)
            {
                if (e.Control && e.KeyCode == Keys.H)
                {
                    ToggleVisibility();
                }
                else if (e.Control && e.KeyCode == Keys.T)
                {
                    chkAlwaysOnTop.Checked = !chkAlwaysOnTop.Checked;
                }
            }

            private void ToggleVisibility()
            {
                if (isVisible)
                {
                    this.Hide();
                    isVisible = false;
                }
                else
                {
                    this.Show();
                    this.Activate();
                    isVisible = true;
                }
            }

            private void StartForegroundMonitoring()
            {
                foregroundTimer = new System.Windows.Forms.Timer { Interval = 500 };
                foregroundTimer.Tick += (s, e) => UpdateForegroundWindow();
                foregroundTimer.Start();
            }

            private void UpdateForegroundWindow()
            {
                try
                {
                    IntPtr hwnd = GetForegroundWindow();
                    
                    if (hwnd == this.Handle) return;

                    // Check if it's our window or system tray
                    int len = GetWindowTextLength(hwnd);
                    if (len == 0) return;

                    var sb = new System.Text.StringBuilder(len + 1);
                    GetWindowText(hwnd, sb, sb.Capacity);
                    string title = sb.ToString();

                    // Skip if it's our window or system tray overflow
                    if (title == "WinAgent" || title.Contains("NotifyIconOverflowWindow") || title == "Window Worker")
                        return;

                    targetWindowHandle = hwnd;
                    
                    this.Invoke(new Action(() =>
                    {
                        lblInputMethod.Text = $"Window: {title.Substring(0, Math.Min(30, title.Length))}";
                    }));

                    // Enumerate controls
                    UpdateControlTree(hwnd);
                }
                catch { }
            }

            private void UpdateControlTree(IntPtr hwnd)
            {
                treeControls.Nodes.Clear();
                var root = new TreeNode($"Window: {GetWindowTitle(hwnd)}");
                root.Tag = hwnd;
                EnumChildWindows(hwnd, (child, _) =>
                {
                    try
                    {
                        string className = GetClassName(child);
                        string text = GetWindowTitle(child);
                        string nodeText = string.IsNullOrEmpty(text) 
                            ? $"[{className}]" 
                            : $"[{className}] {text}";
                        
                        var node = new TreeNode(nodeText);
                        node.Tag = child;
                        root.Nodes.Add(node);
                    }
                    catch { }
                    return true;
                }, IntPtr.Zero);

                treeControls.Nodes.Add(root);
                if (root.Nodes.Count > 0) root.Expand();
            }

            private string GetClassName(IntPtr hwnd)
            {
                char[] buffer = new char[256];
                GetClassName(hwnd, buffer, buffer.Length);
                return new string(buffer).TrimEnd('\0');
            }

            [DllImport("user32.dll", CharSet = CharSet.Auto)]
            static extern int GetClassName(IntPtr hWnd, char[] lpClassName, int nMaxCount);

            private string GetWindowTitle(IntPtr hwnd)
            {
                int len = GetWindowTextLength(hwnd);
                if (len == 0) return "";
                var sb = new System.Text.StringBuilder(len + 1);
                GetWindowText(hwnd, sb, sb.Capacity);
                return sb.ToString();
            }

            private void TreeControls_AfterSelect(object? sender, TreeViewEventArgs e)
            {
                if (e.Node?.Tag is IntPtr handle)
                {
                    targetWindowHandle = handle;
                }
            }

            private void BtnSendText_Click(object? sender, EventArgs e)
            {
                if (targetWindowHandle != IntPtr.Zero && !string.IsNullOrEmpty(txtInput.Text))
                {
                    SendKeys.SendWait(txtInput.Text);
                    txtInput.Clear();
                }
            }

            private void BtnClick_Click(object? sender, EventArgs e)
            {
                if (targetWindowHandle != IntPtr.Zero)
                {
                    RECT rect;
                    GetWindowRect(targetWindowHandle, out rect);
                    int x = (rect.Left + rect.Right) / 2;
                    int y = (rect.Top + rect.Bottom) / 2;
                    
                    Cursor.Position = new Point(x, y);
                    mouse_event(0x0002, 0, 0, 0, 0);
                    mouse_event(0x0004, 0, 0, 0, 0);
                }
            }

            [DllImport("user32.dll")]
            static extern void mouse_event(uint dwFlags, int dx, int dy, int dwData, int dwExtraInfo);

            private void BtnKeyEnter_Click(object? sender, EventArgs e)
            {
                SendKeys.SendWait("{ENTER}");
            }

            private void BtnKeyTab_Click(object? sender, EventArgs e)
            {
                SendKeys.SendWait("{TAB}");
            }

            private void LoadSettings()
            {
                try
                {
                    string path = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "WinAgent", "settings.txt");
                    if (File.Exists(path))
                    {
                        var lines = File.ReadAllLines(path);
                        foreach(var line in lines)
                        {
                            if (line.StartsWith("AlwaysOnTop="))
                            {
                                chkAlwaysOnTop.Checked = line.Contains("True");
                            }
                        }
                    }
                }
                catch { }
            }

            private void SaveSettings()
            {
                try
                {
                    string folder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "WinAgent");
                    Directory.CreateDirectory(folder);
                    File.WriteAllText(Path.Combine(folder, "settings.txt"), $"AlwaysOnTop={chkAlwaysOnTop.Checked}");
                }
                catch { }
            }
        }
    }
}
