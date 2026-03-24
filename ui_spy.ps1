# WinAgent UI Spy - 最終版

Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

Write-Host "WinAgent UI Spy - Press Ctrl+C to stop"
Write-Host ""

function Get-ElementTree {
    param([System.Windows.Automation.AutomationElement]$elem, [int]$depth=0)
    
    if ($depth -gt 4) { return @() }
    
    $results = @()
    
    try {
        $ct = $elem.Current.ControlType.ProgrammaticName -replace 'ControlType.', ''
        $name = $elem.Current.Name
        if (-not $name) { $name = $elem.Current.AutomationId }
        if (-not $name) { $name = '(none)' }
        
        if ($ct -match 'Button|Pane|Menu|Edit|List|Tree') {
            $results += @{
                Depth = $depth
                Type = $ct
                Name = $name
            }
        }
        
        $walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
        $child = $walker.GetFirstChild($elem)
        
        while ($child) {
            $results += Get-ElementTree -elem $child -depth ($depth + 1)
            $child = $walker.GetNextSibling($child)
        }
    }
    catch { }
    
    return $results
}

# 先啟動 Notepad 測試
Write-Host "[1] Starting Notepad..."
$notepad = Start-Process notepad -PassThru
Start-Sleep 2

Write-Host "[2] Scanning Notepad window..."
Write-Host ""

# 取得 Notepad 視窗
$notepadWin = Get-Process -Id $notepad.Id -ErrorAction SilentlyContinue

if ($notepadWin) {
    $element = [System.Windows.Automation.AutomationElement]::FromProcessId($notepad.Id)
    
    Write-Host "=== Notepad UI Structure ==="
    Write-Host ""
    
    $all = Get-ElementTree -elem $element
    
    # 按類型分組顯示
    $byType = $all | Group-Object -Property Type
    
    foreach ($group in $byType) {
        Write-Host "[$($group.Name)] - $($group.Count) items:"
        $group.Group | ForEach-Object {
            $indent = "  " * ($_.Depth + 1)
            Write-Host "$indent$($_.Name)"
        }
        Write-Host ""
    }
    
    Write-Host "=== 可點擊按鈕列表 ==="
    $buttons = $all | Where-Object { $_.Type -eq 'Button' }
    if ($buttons) {
        $buttons | ForEach-Object { Write-Host "  * $($_.Name)" }
    }
    else {
        Write-Host "  (No buttons found)"
    }
}

# 關閉
Start-Sleep 2
Stop-Process -Id $notepad.Id -Force -ErrorAction SilentlyContinue
Write-Host ""
Write-Host "[Done]"
