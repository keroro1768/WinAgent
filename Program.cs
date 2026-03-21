using System;
using System.Drawing;
using System.Windows.Forms;
using System.Runtime.InteropServices;
using System.Diagnostics;
using System.Text;
using System.Windows.Automation;
using System.Collections.Generic;
using InvokePattern = System.Windows.Automation.InvokePattern;

namespace WinAgent
{
    static class Program
    {
        [DllImport("user32.dll")]
        static extern IntPtr GetForegroundWindow();

        [DllImport("user32.dll")]
        static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

        [DllImport("user32.dll")]
        static extern int GetWindowTextLength(IntPtr hWnd);

        [DllImport("user32.dll")]
        static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

        [DllImport("user32.dll")]
        static extern bool EnumChildWindows(IntPtr hWnd, EnumWindowsProc lpEnumFunc, IntPtr lParam);

        [DllImport("user32.dll")]
        static extern bool IsWindowVisible(IntPtr hWnd);

        [DllImport("user32.dll")]
        static extern IntPtr GetWindow(IntPtr hWnd, uint uCmd);

        [DllImport("user32.dll")]
        static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);

        [DllImport("user32.dll")]
        static extern int GetClassName(IntPtr hWnd, char[] lpClassName, int nMaxCount);

        [DllImport("user32.dll")]
        static extern bool GetWindowRect(IntPtr hWnd, out RECT lpRect);

        [DllImport("user32.dll")]
        static extern void mouse_event(uint dwFlags, int dx, int dy, int dwData, int dwExtraInfo);

        [DllImport("user32.dll")]
        static extern IntPtr FindWindow(string? lpClassName, string? lpWindowName);

        [DllImport("user32.dll")]
        static extern IntPtr FindWindowEx(IntPtr hwndParent, IntPtr hwndChildAfter, string? lpszClass, string? lpszWindow);

        [DllImport("user32.dll")]
        static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

        [DllImport("user32.dll")]
        static extern IntPtr SendMessage(IntPtr hWnd, int Msg, IntPtr wParam, StringBuilder lParam);

        [DllImport("user32.dll")]
        static extern IntPtr SendMessage(IntPtr hWnd, int Msg, IntPtr wParam, IntPtr lParam);

        [DllImport("user32.dll")]
        static extern IntPtr SendMessage(IntPtr hWnd, int Msg, IntPtr wParam, ref TBBUTTON lParam);

        [DllImport("kernel32.dll")]
        static extern IntPtr GetStdHandle(int nStdHandle);

        [DllImport("kernel32.dll")]
        static extern bool ReadConsoleOutputCharacter(IntPtr hConsoleOutput, [Out] StringBuilder lpCharacter, int nLength, COORD dwReadCoord, out int lpNumberOfCharsRead);

        [DllImport("kernel32.dll")]
        static extern bool GetConsoleScreenBufferInfo(IntPtr hConsoleOutput, out CONSOLE_SCREEN_BUFFER_INFO lpConsoleScreenBufferInfo);

        delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

        [StructLayout(LayoutKind.Sequential)]
        struct RECT { public int Left, Top, Right, Bottom; }

        [StructLayout(LayoutKind.Sequential)]
        struct COORD { public short X, Y; }

        [StructLayout(LayoutKind.Sequential)]
        struct CONSOLE_SCREEN_BUFFER_INFO
        {
            public COORD dwSize;
            public COORD dwCursorPosition;
            public short wAttributes;
            public RECT srWindow;
            public COORD dwMaximumWindowSize;
        }

        const int STD_OUTPUT_HANDLE = -11;
        const int WM_GETTEXT = 0x000D;
        const int WM_GETTEXTLENGTH = 0x000E;
        const int WM_LBUTTONDOWN = 0x0201;
        const int WM_LBUTTONUP = 0x0202;
        const int SW_HIDE = 0;
        const int SW_SHOW = 1;
        const int GW_ENABLEDPOPUP = 0x28;
        
        // Toolbar messages
        const int TB_GETBUTTONCOUNT = 0x0418 + 24; // 0x0418 = WM_USER = 1054, +24 = 1078
        const int TB_GETBUTTON = 0x0418 + 23;      // 0x0418 + 23 = 1077
        const int TB_GETTEXT = 0x0418 + 45;         // 0x0418 + 45 = 1099
        const int TB_GETTOOLTIPS = 0x0418 + 12;     // 0x0418 + 12 = 1066
        
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
        struct TBBUTTON
        {
            public int iBitmap;
            public int idCommand;
            public int fsState;
            public int fsStyle;
            public IntPtr bmpData;
            public int iString;
            public IntPtr dwData;
        }

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
            private Button btnTaskbar;
            private TreeView treeControls;
            private TextBox txtInput;
            private Button btnSendText;
            private Button btnClick;
            private Button btnKeyEnter;
            private Button btnKeyTab;
            private Button btnGetText;
            private Label lblStatus;
            private TableLayoutPanel mainTable;
            private Panel topPanel;
            private Panel bottomPanel;
            private bool isVisible = true;
            private IntPtr targetWindowHandle = IntPtr.Zero;
            private System.Windows.Forms.Timer foregroundTimer;
            private ListView listIcons;

            public MainForm()
            {
                InitializeComponent();
                StartForegroundMonitoring();
                LoadSettings();
            }

            private void InitializeComponent()
            {
                this.Text = "WinAgent - UI Spy";
                this.Size = new Size(600, 750);
                this.MinimumSize = new Size(500, 600);
                this.FormBorderStyle = FormBorderStyle.Sizable;
                this.StartPosition = FormStartPosition.CenterScreen;

                mainTable = new TableLayoutPanel
                {
                    Dock = DockStyle.Fill,
                    RowCount = 4,
                    ColumnCount = 1,
                    Padding = new Padding(5)
                };
                mainTable.RowStyles.Add(new RowStyle(SizeType.AutoSize));
                mainTable.RowStyles.Add(new RowStyle(SizeType.AutoSize));
                mainTable.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));
                mainTable.RowStyles.Add(new RowStyle(SizeType.AutoSize));

                topPanel = new Panel { Dock = DockStyle.Fill, Height = 45 };

                chkAlwaysOnTop = new CheckBox
                {
                    Text = "Always on Top",
                    AutoSize = true,
                    Font = new Font("Arial", 11, FontStyle.Bold),
                    Location = new Point(10, 10)
                };
                chkAlwaysOnTop.CheckedChanged += (s, e) => { this.TopMost = chkAlwaysOnTop.Checked; SaveSettings(); };

                btnHide = new Button { Text = "Hide (Ctrl+H)", AutoSize = true, Location = new Point(150, 8) };
                btnHide.Click += (s, e) => ToggleVisibility();

                btnTaskbar = new Button { Text = "Scan Tray Icons", AutoSize = true, Location = new Point(270, 8) };
                btnTaskbar.Click += (s, e) => ScanTaskbarIcons();

                topPanel.Controls.Add(chkAlwaysOnTop);
                topPanel.Controls.Add(btnHide);
                topPanel.Controls.Add(btnTaskbar);

                listIcons = new ListView
                {
                    Height = 100,
                    Dock = DockStyle.Fill,
                    View = View.Details,
                    FullRowSelect = true,
                    MultiSelect = false
                };
                listIcons.Columns.Add("Window Title / Class", 350);
                listIcons.Columns.Add("Handle", 80);
                listIcons.DoubleClick += (s, e) => ClickSelectedWindow();

                treeControls = new TreeView
                {
                    Dock = DockStyle.Fill,
                    Font = new Font("Consolas", 9),
                    BackColor = Color.White
                };
                treeControls.Nodes.Add("Switch to another window...");
                treeControls.AfterSelect += TreeControls_AfterSelect;

                bottomPanel = new Panel { Dock = DockStyle.Fill, Height = 130 };

                FlowLayoutPanel btnPanel = new FlowLayoutPanel
                {
                    Dock = DockStyle.Top,
                    FlowDirection = FlowDirection.LeftToRight,
                    AutoSize = true,
                    Height = 35
                };

                btnSendText = new Button { Text = "Send", AutoSize = true, Margin = new Padding(3) };
                btnSendText.Click += BtnSendText_Click;

                btnClick = new Button { Text = "Click", AutoSize = true, Margin = new Padding(3) };
                btnClick.Click += BtnClick_Click;

                btnKeyEnter = new Button { Text = "Enter", AutoSize = true, Margin = new Padding(3) };
                btnKeyEnter.Click += (s, e) => { SendKeys.SendWait("{ENTER}"); lblStatus.Text = "Enter sent"; };

                btnKeyTab = new Button { Text = "Tab", AutoSize = true, Margin = new Padding(3) };
                btnKeyTab.Click += (s, e) => { SendKeys.SendWait("{TAB}"); lblStatus.Text = "Tab sent"; };

                btnGetText = new Button { Text = "Get Text", AutoSize = true, Margin = new Padding(3) };
                btnGetText.Click += BtnGetText_Click;

                btnPanel.Controls.Add(btnSendText);
                btnPanel.Controls.Add(btnClick);
                btnPanel.Controls.Add(btnKeyEnter);
                btnPanel.Controls.Add(btnKeyTab);
                btnPanel.Controls.Add(btnGetText);

                Label lblInput = new Label { Text = "Input:", AutoSize = true, Location = new Point(10, 45) };
                txtInput = new TextBox { Location = new Point(70, 42), Size = new Size(300, 25), Anchor = AnchorStyles.Left };

                lblStatus = new Label { Text = "Ready", AutoSize = true, Location = new Point(10, 75), ForeColor = Color.Gray };

                bottomPanel.Controls.Add(btnPanel);
                bottomPanel.Controls.Add(lblInput);
                bottomPanel.Controls.Add(txtInput);
                bottomPanel.Controls.Add(lblStatus);

                mainTable.Controls.Add(topPanel, 0, 0);
                mainTable.Controls.Add(listIcons, 0, 1);
                mainTable.Controls.Add(treeControls, 0, 2);
                mainTable.Controls.Add(bottomPanel, 0, 3);

                this.Controls.Add(mainTable);

                this.KeyPreview = true;
                this.KeyDown += (s, e) => { if (e.Control && e.KeyCode == Keys.H) ToggleVisibility(); else if (e.Control && e.KeyCode == Keys.T) chkAlwaysOnTop.Checked = !chkAlwaysOnTop.Checked; };
                this.FormClosing += (s, e) => { e.Cancel = true; this.Hide(); };
                
                // 啟動時自動掃描工作列圖示
                this.Shown += (s, e) => ScanTaskbarIcons();
            }

            private void ToggleVisibility()
            {
                if (isVisible) { this.Hide(); isVisible = false; }
                else { this.Show(); this.Activate(); isVisible = true; }
            }

            private void ScanTaskbarIcons()
            {
                listIcons.Items.Clear();
                StringBuilder logSb = new StringBuilder();
                logSb.AppendLine("=== UI Automation Taskbar Scan ===");

                try
                {
                    // 找到工作列的 AutomationElement
                    IntPtr shellTray = FindWindow("Shell_TrayWnd", null);
                    if (shellTray == IntPtr.Zero)
                    {
                        lblStatus.Text = "Cannot find Shell_TrayWnd";
                        return;
                    }

                    logSb.AppendLine($"Shell_TrayWnd: {shellTray}");

                    AutomationElement trayElement = AutomationElement.FromHandle(shellTray);
                    if (trayElement != null)
                    {
                        // 不使用過濾條件，直接取得所有後代
                        Condition condition = Condition.TrueCondition;
                        AutomationElementCollection elements = trayElement.FindAll(TreeScope.Descendants, condition);

                        logSb.AppendLine($"Total elements: {elements.Count}");

                        foreach (AutomationElement element in elements)
                        {
                            try
                            {
                                string name = element.Current.Name;
                                string controlType = element.Current.ControlType?.ProgrammaticName?.Replace("ControlType.", "") ?? "Unknown";
                                
                                // 只顯示有名字的元素
                                if (!string.IsNullOrWhiteSpace(name) && name.Length > 1)
                                {
                                    // 避免重複
                                    bool exists = false;
                                    foreach (ListViewItem existing in listIcons.Items)
                                    {
                                        if (existing.Text.Contains(name)) { exists = true; break; }
                                    }
                                    if (!exists)
                                    {
                                        ListViewItem item = new ListViewItem($"[{controlType}] {name}");
                                        // 保存 AutomationElement 以便點擊
                                        item.Tag = element;
                                        string hwndStr = "0";
                                        try { hwndStr = ((IntPtr)element.Current.NativeWindowHandle).ToString(); } catch { }
                                        item.SubItems.Add(hwndStr);
                                        listIcons.Items.Add(item);
                                        logSb.AppendLine($"Found: [{controlType}] {name}");
                                    }
                                }
                            }
                            catch { }
                        }
                    }
                }
                catch (Exception ex)
                {
                    logSb.AppendLine($"Error: {ex.Message}");
                }

                lblStatus.Text = $"Found {listIcons.Items.Count} items";
                
                // 寫入結果
                string logPath = System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Desktop), "tray_icons.log");
                System.IO.File.WriteAllText(logPath, logSb.ToString());
            }

            private void ScanAllWindows()
            {
                listIcons.Items.Clear();
                
                List<IntPtr> windows = new List<IntPtr>();
                
                EnumWindows((hWnd, lParam) =>
                {
                    if (IsWindowVisible(hWnd))
                    {
                        int len = GetWindowTextLength(hWnd);
                        if (len > 0)
                        {
                            StringBuilder sb = new StringBuilder(len + 1);
                            GetWindowText(hWnd, sb, sb.Capacity);
                            string title = sb.ToString();
                            
                            char[] classBuffer = new char[256];
                            GetClassName(hWnd, classBuffer, 256);
                            string className = new string(classBuffer).TrimEnd('\0');
                            
                            // 過濾掉一些系統視窗
                            if (!string.IsNullOrEmpty(title) && 
                                !title.Contains("Program Manager") &&
                                !title.Contains("Windows Input Experience") &&
                                !title.Contains("Microsoft Text Input"))
                            {
                                ListViewItem item = new ListViewItem(title.Length > 50 ? title.Substring(0, 50) : title);
                                item.SubItems.Add(hWnd.ToString());
                                item.Tag = hWnd;
                                listIcons.Items.Add(item);
                            }
                        }
                    }
                    return true;
                }, IntPtr.Zero);

                lblStatus.Text = $"Found {listIcons.Items.Count} windows";
            }

            private void ClickSelectedWindow()
            {
                if (listIcons.SelectedItems.Count > 0)
                {
                    var selectedItem = listIcons.SelectedItems[0];
                    string name = selectedItem.Text;
                    
                    // 嘗試使用 UI Automation 點擊
                    if (selectedItem.Tag is AutomationElement element)
                    {
                        try
                        {
                            // 嘗試使用 InvokePattern 點擊
                            var invokePattern = element.GetCurrentPattern(InvokePattern.Pattern) as InvokePattern;
                            if (invokePattern != null)
                            {
                                invokePattern.Invoke();
                                lblStatus.Text = $"Clicked: {name}";
                                
                                // 如果點擊了"顯示隱藏的圖示"，延遲後重新掃描
                                if (name.Contains("顯示隱藏的圖示"))
                                {
                                    lblStatus.Text = "Clicked! Rescanning in 1 second...";
                                    System.Windows.Forms.Timer rescanTimer = new System.Windows.Forms.Timer { Interval = 1500 };
                                    rescanTimer.Tick += (s, e) => { rescanTimer.Stop(); ScanTaskbarIcons(); };
                                    rescanTimer.Start();
                                }
                                return;
                            }
                        }
                        catch { }
                    }
                    
                    // 回退到滑鼠點擊
                    if (selectedItem.Tag is IntPtr hwnd && hwnd != IntPtr.Zero)
                    {
                        RECT rect;
                        if (GetWindowRect(hwnd, out rect))
                        {
                            int x = (rect.Left + rect.Right) / 2;
                            int y = (rect.Top + rect.Bottom) / 2;
                            Cursor.Position = new Point(x, y);
                            mouse_event(0x0002, 0, 0, 0, 0);
                            mouse_event(0x0004, 0, 0, 0, 0);
                            lblStatus.Text = $"Clicked: {name}";
                        }
                    }
                    else
                    {
                        lblStatus.Text = $"Cannot click: {name}";
                    }
                }
            }

            private void StartForegroundMonitoring()
            {
                foregroundTimer = new System.Windows.Forms.Timer { Interval = 800 };
                foregroundTimer.Tick += (s, e) => UpdateForegroundWindow();
                foregroundTimer.Start();
            }

            private void UpdateForegroundWindow()
            {
                try
                {
                    IntPtr hwnd = GetForegroundWindow();
                    if (hwnd == this.Handle) return;

                    int len = GetWindowTextLength(hwnd);
                    if (len == 0) return;

                    var sb = new StringBuilder(len + 1);
                    GetWindowText(hwnd, sb, sb.Capacity);
                    string title = sb.ToString();

                    if (title.Contains("NotifyIconOverflowWindow") || title == "Window Worker")
                        return;

                    targetWindowHandle = hwnd;
                    
                    this.Invoke(new Action(() => { lblStatus.Text = title.Length > 40 ? title.Substring(0, 40) + "..." : title; }));
                    UpdateControlTreeUI(hwnd);
                }
                catch { }
            }

            private void UpdateControlTreeUI(IntPtr hwnd)
            {
                treeControls.Nodes.Clear();
                
                try
                {
                    string consoleText = TryGetConsoleText(hwnd);
                    
                    AutomationElement windowElement = AutomationElement.FromHandle(hwnd);
                    if (windowElement == null) return;

                    string windowTitle = windowElement.Current.Name ?? "Window";
                    var rootNode = new TreeNode($"Window: {windowTitle}");
                    rootNode.Tag = hwnd;

                    if (!string.IsNullOrEmpty(consoleText))
                    {
                        var consoleNode = new TreeNode($"[Console] {consoleText.Substring(0, Math.Min(60, consoleText.Length))}...");
                        rootNode.Nodes.Add(consoleNode);
                    }

                    TreeWalker walker = TreeWalker.ControlViewWalker;
                    AutomationElement? child = walker.GetFirstChild(windowElement);

                    int count = 0;
                    while (child != null && count < 80)
                    {
                        AddElementToTree(child, walker, rootNode, ref count);
                        child = walker.GetNextSibling(child);
                    }

                    treeControls.Nodes.Add(rootNode);
                    rootNode.Expand();
                    lblStatus.Text = $"Found {count} controls";
                }
                catch (Exception ex)
                {
                    treeControls.Nodes.Add($"Error: {ex.Message}");
                }
            }

            private string TryGetConsoleText(IntPtr hwnd)
            {
                try
                {
                    GetWindowThreadProcessId(hwnd, out uint processId);
                    if (processId == 0) return "";

                    IntPtr consoleHandle = GetStdHandle(STD_OUTPUT_HANDLE);
                    if (consoleHandle == (IntPtr)(-1)) return "";

                    if (!GetConsoleScreenBufferInfo(consoleHandle, out CONSOLE_SCREEN_BUFFER_INFO csbi)) return "";

                    int totalChars = csbi.dwSize.X * csbi.dwSize.Y;
                    if (totalChars <= 0 || totalChars > 8000) return "";

                    StringBuilder sb = new StringBuilder(totalChars);
                    COORD coord = new COORD { X = 0, Y = 0 };

                    if (ReadConsoleOutputCharacter(consoleHandle, sb, totalChars, coord, out int charsRead))
                    {
                        string text = sb.ToString().TrimEnd('\0');
                        text = text.Replace("\r", "").Replace("\n", " | ");
                        if (text.Length > 100) text = text.Substring(0, 100);
                        return text;
                    }
                }
                catch { }
                return "";
            }

            private string GetTextFromWindow(IntPtr hwnd)
            {
                try
                {
                    int length = (int)SendMessage(hwnd, WM_GETTEXTLENGTH, IntPtr.Zero, null);
                    if (length <= 0) return "";
                    StringBuilder sb = new StringBuilder(length + 1);
                    SendMessage(hwnd, WM_GETTEXT, (IntPtr)(length + 1), sb);
                    return sb.ToString();
                }
                catch { return ""; }
            }

            private void AddElementToTree(AutomationElement element, TreeWalker walker, TreeNode parentNode, ref int count)
            {
                if (element == null || count >= 80) return;

                try
                {
                    string controlType = "";
                    try { controlType = element.Current.ControlType?.ProgrammaticName?.Replace("ControlType.", "") ?? "Unknown"; } catch { controlType = "Unknown"; }

                    string name = "";
                    try { name = element.Current.Name ?? ""; if (string.IsNullOrWhiteSpace(name)) name = element.Current.AutomationId ?? ""; } catch { name = ""; }

                    string nodeText = string.IsNullOrWhiteSpace(name) ? $"[{controlType}]" : $"[{controlType}] {name}";
                    if (nodeText.Length > 45) nodeText = nodeText.Substring(0, 45);

                    var node = new TreeNode(nodeText);
                    try { node.Tag = element.Current.NativeWindowHandle; } catch { }

                    try
                    {
                        IntPtr handle = element.Current.NativeWindowHandle;
                        if (handle != IntPtr.Zero)
                        {
                            string text = GetTextFromWindow(handle);
                            if (!string.IsNullOrEmpty(text) && text.Length > 2)
                            {
                                var textNode = new TreeNode($"Text: {text.Substring(0, Math.Min(35, text.Length))}");
                                node.Nodes.Add(textNode);
                            }
                        }
                    }
                    catch { }

                    AutomationElement? child = walker.GetFirstChild(element);
                    while (child != null && count < 80)
                    {
                        AddElementToTree(child, walker, node, ref count);
                        child = walker.GetNextSibling(child);
                    }

                    parentNode.Nodes.Add(node);
                    count++;
                }
                catch { }
            }

            private void TreeControls_AfterSelect(object? sender, TreeViewEventArgs e)
            {
                if (e.Node?.Tag is IntPtr handle && handle != IntPtr.Zero)
                {
                    targetWindowHandle = handle;
                    lblStatus.Text = "Selected: " + e.Node.Text.Substring(0, Math.Min(20, e.Node.Text.Length));
                }
            }

            private void BtnSendText_Click(object? sender, EventArgs e)
            {
                if (targetWindowHandle != IntPtr.Zero && !string.IsNullOrEmpty(txtInput.Text))
                {
                    SendKeys.SendWait(txtInput.Text);
                    lblStatus.Text = "Sent: " + txtInput.Text;
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
                    lblStatus.Text = "Clicked";
                }
            }

            private void BtnGetText_Click(object? sender, EventArgs e)
            {
                if (targetWindowHandle != IntPtr.Zero)
                {
                    string text = GetTextFromWindow(targetWindowHandle);
                    if (!string.IsNullOrEmpty(text))
                    {
                        lblStatus.Text = "Text: " + text.Substring(0, Math.Min(35, text.Length));
                        MessageBox.Show(text, "Window Text", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                    else lblStatus.Text = "No text found";
                }
            }

            private void LoadSettings()
            {
                try
                {
                    string path = System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "WinAgent", "settings.txt");
                    if (System.IO.File.Exists(path))
                        foreach (var line in System.IO.File.ReadAllLines(path))
                            if (line.StartsWith("AlwaysOnTop="))
                                chkAlwaysOnTop.Checked = line.Contains("True");
                }
                catch { }
            }

            private void SaveSettings()
            {
                try
                {
                    string folder = System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData), "WinAgent");
                    System.IO.Directory.CreateDirectory(folder);
                    System.IO.File.WriteAllText(System.IO.Path.Combine(folder, "settings.txt"), $"AlwaysOnTop={chkAlwaysOnTop.Checked}");
                }
                catch { }
            }
        }
    }
}
