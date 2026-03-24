Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$point = New-Object System.Windows.Point(237, 167)
$element = [System.Windows.Automation.AutomationElement]::FromPoint($point)

if ($element) {
    Write-Host "Element found!"
    Write-Host "Name:" $element.Current.Name
    Write-Host "Type:" $element.Current.ControlType.ProgrammaticName
    Write-Host "ID:" $element.Current.AutomationId
}
else {
    Write-Host "No element found"
}
