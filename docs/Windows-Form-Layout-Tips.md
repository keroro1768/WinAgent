# Windows Form UI Layout 設計技巧報告

> 報告日期：2026-03-21
> 來源：Microsoft Learn, Stack Overflow, C# Corner

---

## 1. 概述

Windows Form 提供多種 Layout 面板來實現彈性 UI設計。主要包括：

| 面板 | 用途 |
|------|------|
| **FlowLayoutPanel** | 水平/垂直流動排列 |
| **TableLayoutPanel** | 表格網格排列 |
| **SplitContainer** | 可調整分隔面板 |
| **Panel** | 基本容器 |

---

## 2. FlowLayoutPanel

### 2.1 特性

- 內容依據流動方向排列（水平或垂直）
- 內容會自動換行
- 類似 HTML 的 flex-wrap

### 2.2 程式碼範例

```csharp
FlowLayoutPanel flowPanel = new FlowLayoutPanel
{
    Dock = DockStyle.Fill,
    FlowDirection = FlowDirection.TopDown,
    WrapContents = true,
    AutoScroll = true
};

// 加入控制項
flowPanel.Controls.Add(button1);
flowPanel.Controls.Add(button2);
```

### 2.3 優點

- ✅ 簡單易用
- ✅ 自動換行
- ✅ 適合按鈕群組

---

## 3. TableLayoutPanel (推薦)

### 3.1 特性

- 類似 HTML `<table>`
- 網格佈局，可設定行列
- 支援百分比/絕對尺寸
- **可巢狀使用**

### 3.2 程式碼範例

```csharp
TableLayoutPanel table = new TableLayoutPanel
{
    Dock = DockStyle.Fill,
    RowCount = 3,
    ColumnCount = 2
};

// 設定行列樣式
table.RowStyles.Add(new RowStyle(SizeType.AutoSize));
table.RowStyles.Add(new RowStyle(SizeType.Percent, 50F));
table.RowStyles.Add(new RowStyle(SizeType.Percent, 50F));

table.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50F));
table.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 50F));

// 加入控制項
table.Controls.Add(textBox, 0, 0);  // column, row
table.Controls.Add(button, 1, 0);
```

### 3.3 最佳實踐

| 建議 | 說明 |
|------|------|
| **保持簡單** | 不要使用太多行列 |
| **使用 AutoSize** | 讓內容自動調整 |
| **巢狀面板** | 複雜佈局用多個小面板 |
| **設定 Min/Max** | 防止過度縮放 |

---

## 4. Dock 與 Anchor

### 4.1 Dock 屬性

| 屬性 | 行為 |
|------|------|
| `DockStyle.Top` | 停在頂部 |
| `DockStyle.Bottom` | 停在底部 |
| `DockStyle.Left` | 停在左側 |
| `DockStyle.Right` | 停在右側 |
| `DockStyle.Fill` | 填滿剩餘空間 |

### 4.2 Anchor 屬性

```csharp
// 控制項錨定到四邊
button.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;

// 常見組合
button.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right | AnchorStyles.Bottom;  // Fill
button.Anchor = AnchorStyles.Left | AnchorStyles.Right;  // 水平拉伸
```

---

## 5. 推薦的 WinAgent 佈局

### 5.1 使用 TableLayoutPanel (3列 x 3行)

```
┌─────────────────────────────────────────────┐
│ TableLayoutPanel (3x3)                    │
├──────────────┬──────────────┬──────────────┤
│  Row 0      │  (Top)     │              │
├──────────────┼──────────────┼──────────────┤
│              │            │              │
│  TreeView   │  (Middle)  │   Options    │
│  (Fill)     │            │   Panel      │
│              │            │              │
├──────────────┼──────────────┼──────────────┤
│  Row 2      │ (Bottom)   │              │
└──────────────┴──────────────┴──────────────┘
```

### 5.2 程式碼範例

```csharp
TableLayoutPanel mainTable = new TableLayoutPanel
{
    Dock = DockStyle.Fill,
    RowCount = 3,
    ColumnCount = 1,
    Padding = new Padding(5)
};

// 設定列比例
mainTable.RowStyles.Add(new RowStyle(SizeType.AutoSize));  // Top: 自動
mainTable.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));  // Middle: 100%
mainTable.RowStyles.Add(new RowStyle(SizeType.AutoSize));  // Bottom: 自動

// Top Panel
Panel topPanel = new Panel { Height = 50, Dock = DockStyle.Fill };
topPanel.Controls.Add(chkAlwaysOnTop);
topPanel.Controls.Add(btnHide);
mainTable.Controls.Add(topPanel, 0, 0);

// Middle - TreeView
TreeView tree = new TreeView { Dock = DockStyle.Fill };
mainTable.Controls.Add(tree, 0, 1);

// Bottom Panel  
FlowLayoutPanel bottomPanel = new FlowLayoutPanel 
{ 
    Dock = DockStyle.Fill,
    FlowDirection = FlowDirection.LeftToRight,
    Height = 100
};
mainTable.Controls.Add(bottomPanel, 0, 2);
```

---

## 6. 巢狀範例

```csharp
// 主面板 - 2列
TableLayoutPanel mainPanel = new TableLayoutPanel
{
    Dock = DockStyle.Fill,
    ColumnCount = 2,
    RowCount = 1
};
mainPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 70F));  // 70%
mainPanel.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 30F));  // 30%

// 左側 - TreeView (巢狀 TableLayoutPanel)
TableLayoutPanel leftPanel = new TableLayoutPanel
{
    Dock = DockStyle.Fill,
    RowCount = 2,
    ColumnCount = 1
};
leftPanel.RowStyles.Add(new RowStyle(SizeType.AutoSize));  // 工具列
leftPanel.RowStyles.Add(new RowStyle(SizeType.Percent, 100F));  // TreeView

leftPanel.Controls.Add(toolPanel, 0, 0);
leftPanel.Controls.Add(treeView, 0, 1);

mainPanel.Controls.Add(leftPanel, 0, 0);

// 右側 - 選項面板
Panel rightPanel = new Panel { Dock = DockStyle.Fill };
mainPanel.Controls.Add(rightPanel, 1, 0);

this.Controls.Add(mainPanel);
```

---

## 7. 常見錯誤與解決

| 問題 | 原因 | 解決 |
|------|------|------|
| 控制項不見 | 被其他控制項覆蓋 | 檢查 Dock/Z-Order |
| 自動調整失敗 | 沒設定 SizeType | 正確設定 SizeType |
| 顯示不出來 | 面板沒設定 Dock | 設定 DockStyle.Fill |
| 尺寸不對 | 直接設 Size | 使用 RowStyle/ColumnStyle |

---

## 8. 參考資源

| 來源 | 連結 |
|------|------|
| Microsoft TableLayoutPanel | https://learn.microsoft.com/dotnet/desktop/winforms/controls/tablelayoutpanel-control-overview |
| Microsoft FlowLayoutPanel | https://learn.microsoft.com/dotnet/desktop/winforms/controls/flowlayoutpanel-control-overview |
| 最佳實踐 | https://learn.microsoft.com/dotnet/desktop/winforms/controls/best-practices-for-the-tablelayoutpanel-control |
| C# Corner 教學 | https://www.c-sharpcorner.com/UploadFile/mahesh/flowlayoutpanel-in-C-Sharp/ |

---

## 9. 結論

### WinAgent 建議佈局

1. **最外層**：使用 `TableLayoutPanel` 控制整體比例
2. **中間層**：使用 `FlowLayoutPanel` 處理按鈕排列
3. **內層**：個別控制項設定 Anchor/Dock

### 關鍵原則

- ✅ **保持簡單** - 不要過度巢狀
- ✅ **使用 AutoSize** - 讓內容決定大小
- ✅ **設定 MinSize** - 防止過度縮小
- ✅ **巢狀面板** - 複雜 UI 拆分成小面板

---

*報告完成*
