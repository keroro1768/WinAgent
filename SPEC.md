# WinAgent 完整規格書 v2.0

> 版本：2.0
> 更新日期：2026-03-21

---

## 1. 專案目標

建立一個 Windows 桌面監控與自動化工具，常駐於系統 Tray，可執行外部程式並進行互動控制。

---

## 2. 功能需求

### 2.1 核心功能

| 功能 | 說明 | 優先級 |
|------|------|--------|
| **開機常駐** | 開機後自動啟動並縮小到 Tray | P0 |
| **Tray Icon** | 常駐右下角，點擊打開主畫面 | P0 |
| **前景視窗監控** | 即時取得最前景視窗的標題、處理程序 | P0 |
| **執行外部程式** | 啟動並管理外部應用程式 | P0 |
| **程式輸出監控** | 即時擷取程式的 stdout/stderr 輸出 | P0 |
| **鍵盤模擬** | 發送按鍵到目標視窗 | P1 |
| **輸入法識別** | 偵測目前輸入法，避免亂碼 | P1 |
| **程序管理** | 維持最多 N 個實體（目前 2 個 Claude） | P1 |

### 2.2 Claude 管理

| 功能 | 說明 |
|------|------|
| **最多實體數** | 2 個 Claude Code 同時運行 |
| **自動重啟** | 如果崩潰自動重啟 |
| **輸出監控** | 即時顯示 Claude 的輸出 |
| **互動輸入** | 可發送指令到 Claude |

---

## 3. 系統架構

### 3.1 模組架構

```
┌─────────────────────────────────────────────────────────────┐
│                        WinAgent                             │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │  Tray Icon  │    │   Process   │    │   Input    │ │
│  │  Manager    │    │   Manager   │    │   Method   │ │
│  └──────────────┘    └──────────────┘    └────────────┘ │
│         │                   │                   │           │
│         └───────────────────┼───────────────────┘           │
│                             │                               │
│                             ▼                               │
│                   ┌──────────────────┐                    │
│                   │   CLI / API      │                    │
│                   └──────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 執行流程

```
┌─────────────────────────────────────────────────────────────┐
│                     啟動流程                               │
└─────────────────────────────────────────────────────────────┘

1. WinAgent.exe 啟動
       │
       ▼
2. 註冊 Windows 開機啟動 (Registry)
       │
       ▼
3. 隱藏主視窗，顯示 Tray Icon
       │
       ▼
4. 初始化各模組
       │    │    │
       ▼    ▼    ▼
   [Tray] [Process] [InputMethod]
       │    │    │
       └────┴────┘
             │
             ▼
      [等待命令/事件]
```

---

## 4. 核心模組設計

### 4.1 Tray Icon 模組

| 功能 | 說明 |
|------|------|
| 顯示圖示 | 顯示 WinAgent 圖標 |
| 右鍵選單 | 開啟/設定/狀態/離開 |
| 點擊打開 | 單擊顯示主視窗 |
| 狀態顯示 | 圖標顏色表示狀態 |

### 4.2 Process Manager 模組

```csharp
class ProcessManager {
    // 啟動程式
    Task<int> SpawnProcess(string path, string args);
    
    // 取得輸出
    event Action<string> OnOutput;
    
    // 發送輸入
    void SendInput(string text);
    
    // 發送按鍵
    void SendKey(Keys key);
    
    // 取得程序列表
    List<ProcessInfo> GetProcesses();
    
    // 終止程序
    void KillProcess(int pid);
    
    // 維持 N 個實體
    void MaintainCount(int count, string processPath);
}
```

### 4.3 Input Method 模組

```csharp
class InputMethodManager {
    // 取得目前輸入法
    string GetCurrentInputMethod();
    
    // 取得輸入法語言
    string GetInputMethodLanguage();
    
    // 切換到英文
    void SwitchToEnglish();
    
    // 檢查是否為英文
    bool IsEnglish();
    
    // 等待變成英文
    Task<bool> WaitForEnglish(int timeoutMs);
}
```

### 4.4 Claude Manager (繼承 Process Manager)

```csharp
class ClaudeManager : ProcessManager {
    // 維持 N 個 Claude 實體
    void MaintainClaudeInstances(int count = 2);
    
    // 取得 Claude 狀態
    List<ClaudeStatus> GetClaudeStatuses();
    
    // 發送指令到指定的 Claude
    void SendToClaude(int instanceId, string command);
    
    // 監控輸出
    event Action<int, string> OnClaudeOutput;
}
```

---

## 5. 實作技術

### 5.1 Win32 API

| API | 用途 |
|-----|------|
| `GetForegroundWindow()` | 取得前景視窗 |
| `GetWindowText()` | 取得視窗標題 |
| `SetWinEventHook()` | 監控視窗事件 |
| `Shell_NotifyIcon()` | 系統 Tray Icon |
| `SendMessage()` | 發送訊息到視窗 |
| `PostMessage()` | 發送按鍵 |
| `ImmGetDefaultIMEWnd()` | 取得輸入法資訊 |

### 5.2 程序輸出監控

```csharp
// 使用 OutputDataReceived 事件
process.OutputDataReceived += (sender, e) => {
    if (e.Data != null) {
        Console.WriteLine($"[OUT] {e.Data}");
    }
};

process.ErrorDataReceived += (sender, e) => {
    if (e.Data != null) {
        Console.WriteLine($"[ERR] {e.Data}");
    }
};
```

### 5.3 鍵盤模擬

```csharp
// 發送到目標視窗
[DllImport("user32.dll")]
static extern IntPtr FindWindow(string lpClassName, string lpWindowName);

[DllImport("user32.dll")]
static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);

// 按鍵碼
const uint WM_KEYDOWN = 0x0100;
const uint WM_KEYUP = 0x0101;
const int VK_RETURN = 0x0D;
```

---

## 6. 驗證方法

### 6.1 功能測試清單

| 測試項目 | 預期結果 | 驗證方式 |
|----------|----------|----------|
| 開機自動啟動 | 登入後自動執行 | 重啟電腦測試 |
| Tray Icon 顯示 | 圖標出現在右下角 | 視覺檢查 |
| 點擊 Tray 開啟 | 顯示主視窗 | 點擊測試 |
| 執行 Claude | Claude 正常啟動 | 執行指令 |
| 輸出監控 | 即時顯示輸出 | 觀察輸出 |
| 發送輸入 | 文字送到 Claude | 發送指令 |
| 維持 2 個實體 | 永遠只有 2 個 | 多次啟動測試 |
| 輸入法切換 | 自動切到英文 | 觸發測試 |

### 6.2 錯誤處理策略

| 錯誤類型 | 處理方式 | 記錄 |
|----------|----------|------|
| 程序崩潰 | 自動重啟 | 記錄崩潰次數、時間 |
| 輸出超時 | 發出警告 | 記錄超時時間 |
| 輸入法失敗 | 嘗試切換 | 記錄失敗次數 |
| 記憶體過高 | 終止最舊實體 | 記錄記憶體使用 |

---

## 7. 記錄系統

### 7.1 日誌格式

```
[2026-03-21 14:30:00] [INFO] WinAgent 啟動
[2026-03-21 14:30:01] [INFO] 註冊開機啟動: 成功
[2026-03-21 14:30:02] [INFO] Claude #1 啟動中...
[2026-03-21 14:30:05] [INFO] Claude #1 啟動成功 (PID: 12345)
[2026-03-21 14:30:06] [WARN] 輸入法非英文，切換中...
[2026-03-21 14:30:07] [INFO] 輸入法切換成功
[2026-03-21 14:31:00] [ERROR] Claude #1 崩潰，自動重啟中...
```

### 7.2 失敗紀錄

```json
{
  "timestamp": "2026-03-21T14:31:00Z",
  "event": "process_crash",
  "process": "Claude #1",
  "pid": 12345,
  "exit_code": -1073741819,
  "retry_count": 3,
  "last_error": "Access violation"
}
```

---

## 8. CLI 命令

```
winagent status              # 顯示狀態
winagent start claude      # 啟動 Claude
winagent stop claude       # 停止 Claude
winagent list              # 列出執行的程序
winagent send <pid> <cmd>  # 發送命令
winagent input <text>      # 發送文字
winagent key enter         # 發送 Enter
winagent ime check          # 檢查輸入法
winagent ime switch        # 切換到英文
winagent logs              # 顯示日誌
```

---

## 9. 風險與對策

| 風險 | 影響 | 對策 |
|------|------|------|
| 輸入法切換失敗 | 文字變亂碼 | 記錄失敗，發出警告 |
| Claude 頻繁崩潰 | 無法使用 | 限制重啟次數 |
| 記憶體不足 | 系統不穩 | 限制程序數量 |
| 權限不足 | 功能失效 | 請求管理員權限 |

---

## 10. 未來擴展

- [ ] 支援更多輸入法（日文、韓文）
- [ ] 圖形化介面
- [ ] 遠端控制 API
- [ ] 腳本自動化

---

*最後更新：2026-03-21*
