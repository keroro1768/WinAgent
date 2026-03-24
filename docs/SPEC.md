# WinAgent 功能規格說明書 (更新版)

## 📋 專案概述

**WinAgent** 是一個 Windows 桌面自動化框架，目標是讓 AI 能夠操控任何 Windows 應用程式的 UI 控件。

---

## 🏗️ 系統架構

```
WinAgent
├── CLI 工具
│   ├── action_rpa.py      - 動作錄製/播放
│   ├── mouse_click.py     - 滑鼠控制
│   ├── combo.py           - 組合計系統
│   ├── scanner_v2.py      - UI 掃描器 (OCR)
│   └── ocr_click.py       - OCR 點擊
│
├── WinAgentOCR/           - OCR 引擎 (.NET)
│   └── WinAgentOCR.csproj - Windows.Media.Ocr
│
├── combos/                 - 預設組合計
└── scans/                  - 掃描結果
```

---

## 🔧 功能狀態

| 功能 | 狀態 | 說明 |
|------|------|------|
| **座標點擊** | ✅ 完成 | 使用 Win32 API |
| **動作錄製** | ✅ 完成 | 記錄點擊位置 |
| **Combo 組合計** | ✅ 完成 | 自動化流程 |
| **OCR 文字辨識** | ✅ 完成 | Windows.Media.Ocr |
| **WPF UI 掃描** | 🔄 進行中 | OCR + 座標映射 |
| **UIAutomation** | ⚠️ 有限 | WPF 應用不支援 |

---

## 🎯 核心技術

### 1. OCR 文字辨識

使用 Windows 內建的 **Windows.Media.Ocr** API：

```csharp
// .NET 範例
var ocrEngine = OcrEngine.TryCreateFromUserProfileLanguages();
var result = await ocrEngine.RecognizeAsync(softwareBitmap);
```

### 2. 座標點擊

```python
# Python + ctypes
user32.SetCursorPos(x, y)
user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
```

### 3. Combo 組合計

```json
{
  "name": "開啟並存檔",
  "steps": [
    {"action": "launch", "params": {"app": "notepad.exe"}},
    {"action": "type", "params": {"text": "Hello"}},
    {"action": "click", "params": {"x": 100, "y": 200}}
  ]
}
```

---

## 📁 關鍵檔案

| 檔案 | 功能 |
|------|------|
| `scanner_v2.py` | UI 掃描器 (OCR + 座標) |
| `combo.py` | 組合計執行器 |
| `action_rpa.py` | 動作錄製/播放 |
| `mouse_click.py` | 滑鼠控制 |
| `WinAgentOCR/` | OCR 引擎 |

---

## 🚀 使用方式

### 掃描 UI

```bash
python scanner_v2.py --scan DbgX
```

### 點擊元素

```bash
python scanner_v2.py --scan DbgX --click memory
```

### 執行組合計

```bash
python combo.py --run notepad_save
```

---

## 🔬 WPF 應用程式支援

### 挑戰

- **UIAutomation** 無法穿透 WPF 自定義控件
- **EnumChildWindows** 回傳空結果
- 需要使用 **OCR** 來識別 UI 元素

### 解決方案

1. **OCR 截圖** → 識別文字 + 位置
2. **座標映射** → 建立 UI 地圖
3. **點擊執行** → 自動化操作

---

## 📝 開發日誌

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-03-24 | 0.1 | UI 掃描基礎 |
| 2026-03-24 | 0.2 | OCR 整合 |
| 2026-03-24 | 0.3 | Combo 系統 |
| 2026-03-24 | 0.4 | WinDBG OCR 測試 |

---

*持續更新中...*
