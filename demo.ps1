Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms

$notepad = Start-Process notepad -PassThru
Start-Sleep -Seconds 2

$root = [System.Windows.Automation.AutomationElement]::FromHandle($notepad.MainWindowHandle)
Write-Host "Root:" $root.Current.Name

$edit = $root.FindFirst("descendant", [System.Windows.Automation.Condition]::TrueCondition)
if ($edit) {
    $edit.SetFocus()
    Start-Sleep -Milliseconds 300
    
    $text = "Hi, I win - " + (Get-Date -Format "yyyy/MM/dd HH:mm")
    [System.Windows.Forms.SendKeys]::SendWait($text)
    
    Write-Host "Typed:" $text
    
    Start-Sleep -Milliseconds 500
    [System.Windows.Forms.SendKeys]::SendWait("^(+s)")
    Start-Sleep -Seconds 1
    
    $fname = "WinTest_" + (Get-Date -Format "HHmmss") + ".txt"
    [System.Windows.Forms.SendKeys]::SendWait($fname)
    Start-Sleep -Milliseconds 500
    [System.Windows.Forms.SendKeys]::SendWait("{ENTER}")
    
    Start-Sleep -Seconds 1
    
    $path = Join-Path $env:USERPROFILE "Documents" $fname
    if (Test-Path $path) {
        Write-Host "SUCCESS:" $path
        Get-Content $path
    }
}

Stop-Process -Id $notepad.Id -Force -ErrorAction SilentlyContinue