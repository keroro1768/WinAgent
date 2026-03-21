# Windows Window Monitor Agent - 專案計畫

> 專案名稱：WinAgent (Windows Window Monitor Agent)
> 計畫日期：2026-03-21

---

## 1. 專案概述

### 1.1 目標

建立一個 Windows 桌面監控工具，常駐於系統 Tray Icon，監控最前景 (Foreground) 視窗的狀態與彈出訊息。

### 1.2 功能需求

| 功能 | 說明 |
|------|------|
| **前景視窗監控** | 即時取得最前景視窗的標題、內容 |
| **Tray Icon** | 常駐右下角，點擊打開主畫面 |
| **訊息攔截** | 監控彈出訊息 (Toast/Balloon) |
| **CLI 介面** | 可用指令快速查詢視窗狀態 |
| **API 輸出** | 提供 JSON API 供其他程式呼叫 |

---

## 2. 技術架構

### 2.1 開發環境

| 項目 | 選擇 |
|------|------|
| **語言** | C# (.NET 8) |
| **框架** | WPF 或 Console App + WinForms |
| **IDE** | Visual Studio 2022 |
| **目標 OS** | Windows 10/11 |

### 2.2 核心 API

| API | 用途 |
|-----|------|
| `GetForegroundWindow()` | 取得最前景視窗 |
| `GetWindowText()` | 取得視窗標題 |
| `Shell_NotifyIcon()` | 建立系統 Tray Icon |
| `WinEventHook()` | 監控視窗變化 |
| `ToastNotificationManager` | 監控 Windows 通知 |

### 2.3 系統架構

```
┌─────────────────────────────────────────────────────────────┐
│                      WinAgent                            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │  Tray Icon   │    │  Window      │    │  Message   │ │
│  │  Manager    │    │  Monitor     │    │  Sniffer   │ │
│  └──────────────┘    └──────────────┘    └────────────┘ │
│         │                   │                   │           │
│         └───────────────────┼───────────────────┘           │
│                             │                               │
│                             ▼                               │
│                   ┌──────────────────┐                    │
│                   │   JSON API / CLI │                    │
│                   └──────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 功能模組

### 3.1 Tray Icon 模組

| 功能 | 說明 |
|------|------|
| 啟動時隱藏 | 開機後自動縮小到 Tray |
| 右鍵選單 | 開啟/關閉/設定/離開 |
| 點擊打開 | 點擊 Tray Icon 顯示主畫面 |
| 顯示狀態 | Icon 顯示監控狀態 |

### 3.2 Window Monitor 模組

```csharp
// 取得最前景視窗
public class WindowInfo {
    public IntPtr Handle;      // 視窗 handle
    public string Title;       // 視窗標題
    public string ProcessName; // 處理程序名稱
    public int ProcessId;     // PID
}
```

### 3.3 Message Sniffer 模組

| 監控類型 | 說明 |
|----------|------|
| 視窗建立/銷毀 | WinEventHook (EVENT_OBJECT_CREATE/DESTROY) |
| 前景變化 | WinEventHook (EVENT_SYSTEM_FOREGROUND) |
| Toast 訊息 | Windows.UI.Notifications |

### 3.4 CLI/API 模組

```
命令列用法：
  winagent status              # 取得目前前景視窗
  winagent list               # 列出所有視窗
  winagent watch              # 持續監控模式
  winagent api                # 啟動 API 伺服器
```

---

## 4. 實作步驟

### Phase 1: 基礎建設

1. **建立 .NET Console 專案**
2. **實作 Tray Icon 功能**
3. **實作 GetForegroundWindow 監控**

### Phase 2: 監控功能

4. **Hook 視窗事件**
5. **記錄視窗歷史**
6. **JSON API 輸出**

### Phase 3: 進階功能

7. **Toast 訊息監控**
8. **Webhook 通知**
9. **OpenClaw 整合**

---

## 5. 程式碼結構

```
WinAgent/
├── WinAgent.sln
├── src/
│   └── WinAgent/
│       ├── Program.cs           # 進入點
│       ├── Services/
│       │   ├── WindowService.cs    # 視窗監控
│       │   ├── TrayService.cs      # Tray Icon
│       │   └── NotificationService.cs
│       ├── Models/
│       │   └── WindowInfo.cs
│       ├── Native/
│       │   └── Win32.cs           # P/Invoke
│       └── cli/
│           └── Commands.cs        # CLI 處理
├── assets/
│   └── icon.ico
└── README.md
```

---

## 6. 關鍵技術點

### 6.1 P/Invoke 宣告

```csharp
[DllImport("user32.dll")]
static extern IntPtr GetForegroundWindow();

[DllImport("user32.dll")]
static extern int GetWindowText(IntPtr hWnd, StringBuilder text, int count);

[DllImport("shell32.dll")]
static extern bool Shell_NotifyIcon(uint dwMessage, ref NOTIFYICONDATA pnid);
```

### 6.2 WinEventHook

```csharp
SetWinEventHook(
    EVENT_SYSTEM_FOREGROUND,  // 監控前景變化
    EVENT_SYSTEM_FOREGROUND,
    IntPtr.Zero,
    WinEventProc,
    0, 0,
    WINEVENT_OUTOFCONTEXT);
```

---

## 7. 與 OpenClaw 整合

### 7.1 整合方式

| 方式 | 說明 |
|------|------|
| **Webhook** | 視窗變化時發送到 OpenClaw |
| **CLI 呼叫** | OpenClaw 執行 winagent status |
| **IPC** | 共享記憶體/命名管道 |

### 7.2 使用情境

```
場景：瀏覽器彈出錯誤訊息
1. WinAgent 偵測到新視窗
2. 擷取視窗標題/內容
3. 發送到 OpenClaw
4. OpenClaw 分析並回應
```

---

## 8. 參考資源

| 資源 | 連結 |
|------|------|
| GetForegroundWindow | https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getforegroundwindow |
| System Tray | https://learn.microsoft.com/en-us/windows/win32/shell/notification-area |
| WinEventHook | https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setwineventhook |
| Toast Notifications | https://learn.microsoft.com/en-us/windows/apps/develop/notifications/app-notifications/ |

---

## 9. 下一步

1. ✅ 完成專案計畫
2. ⏳ 建立 GitHub Repo
3. ⏳ 設定 OpenCode + MiniMax LLM
4. ⏳ 開始實作 Phase 1

---

*最後更新：2026-03-21*
