# WinAgent 研究：Windows Taskbar 系統圖示與 Pen Menu

*Branch: winagent/pen-icon-research*
*Date: 2026-03-23*

---

## 1. 研究目標

找出 Windows Taskbar 系統Tray圖示的執行來源，特別是 Pen Menu (觸控筆選單)。

---

## 2. 系統 Tray 圖示Registry位置

### 2.1 NotifyIconSettings（用戶自行安裝的 App）

```
HKCU:\Control Panel\NotifyIconSettings
```

每個圖示對應一個 GUID，包含：
- ExecutablePath：執行檔路徑
- Arguments：啟動參數
- AppID：App ID

### 2.2 Taskband（釘選的圖示）

```
HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\Taskband
```

### 2.3 ShellIconCache（圖示快取）

```
C:\Users\<用户名>\AppData\Local\IconCache.db
```

---

## 3. 已識別的 Taskbar 系統圖示

| 圖示 | 執行檔路徑 |
|------|-----------|
| OneDrive | `OneDrive.exe` |
| 向日葵 (AweSun) | `AweSun.exe` |
| Windows 安全 | `SecurityHealthSystray.exe` |
| 輸入法 | `imecfmui.exe` |
| 工作管理員 | `Taskmgr.exe` |
| Copilot | `Copilot.exe` |
| WinAgent | `WinAgent.exe` |
| Outlook | `olk.exe` |
| M365 Copilot | `M365Copilot.exe` |

---

## 4. Pen Menu 研究結果

### 4.1 核心服務

| 服務名稱 | 狀態 | 說明 |
|----------|------|------|
| PenService_77d7a | 執行中 | Windows Ink 觸控筆服務 |

### 4.2 Registry 設定

```
HKCU:\Software\Microsoft\Windows\CurrentVersion\PenWorkspace
├── PenWorkspaceButtonDesiredVisibility = 1  (顯示/隱藏)
└── Notes = Microsoft.MicrosoftStickyNotes_8wekyb3d8bbwe!App
```

### 4.3 顯示條件

1. **PenService 服務運行中** ✅
2. **Registry 設定 enabled** (PenWorkspaceButtonDesiredVisibility = 1) ✅
3. **偵測到觸控筆靠近** ❌ (無法手動觸發)

### 4.4 啟動方法

| 方法 | 指令 |
|------|------|
| 快捷鍵 | `Win + W` (開啟 Windows Ink Workspace) |
| 系統設定 | `ms-settings:pen` |
| Registry | `HKCU:\Software\Microsoft\Windows\CurrentVersion\PenWorkspace` |

### 4.5 結論

Pen Menu 是 Windows 11 內建的系統服務 UI，**沒有單獨的執行檔**。它：
- 由 PenService_77d7a 服務管理
- 透過 ms-settings:pen 頁面配置
- 自動在偵測到觸控筆靠近時顯示

---

## 5. Windows Ink 相關 Registry 位置

| Registry 位置 | 功能 |
|---------------|------|
| `HKCU:\Software\Microsoft\Windows\CurrentVersion\PenWorkspace` | Pen Menu 設定 |
| `HKCU:\Software\Microsoft\Windows\CurrentVersion\PenWorkspace\Notes` | 備忘錄 App |
| `HKLM:\SOFTWARE\Policies\Microsoft\WindowsInkWorkspace` | 群組原則/原則設定 |
| `HKCU:\Control Panel\NotifyIconSettings` | 通知區域圖示 |

### 5.1 WindowsInkWorkspace 詳細設定

| 機碼 | 類型 | 值 | 功能 |
|------|------|-----|------|
| `AllowWindowsInkWorkspace` | DWORD | 0 | 停用 |
| `AllowWindowsInkWorkspace` | DWORD | 1 | 啟用 |
| `AllowSuggestedAppsInWindowsInkWorkspace` | DWORD | 0/1 | 允許建議的 App |

### 5.2 控制 Pen Menu 顯示

```powershell
# 顯示 Pen Menu
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\PenWorkspace' -Name 'PenWorkspaceButtonDesiredVisibility' -Value 1

# 隱藏 Pen Menu
Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\PenWorkspace' -Name 'PenWorkspaceButtonDesiredVisibility' -Value 0

# 停用 Windows Ink Workspace
New-Item -Path 'HKLM:\SOFTWARE\Policies\Microsoft\WindowsInkWorkspace' -Force
Set-ItemProperty -Path 'HKLM:\SOFTWARE\Policies\Microsoft\WindowsInkWorkspace' -Name 'AllowWindowsInkWorkspace' -Value 0
```

---

## 6. 下一步

1. 監控 PenService 狀態
2. 監控觸控筆事件
3. 實作快捷鍵切換輸入法
4. 研究其他 Taskbar 圖示的 Registry

---

*記錄時間：2026-03-23 06:48*
