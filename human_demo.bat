@echo off
REM WinAgent Human-Like Demo - Batch Version
REM 使用 PowerShell + SendKeys 模擬人類操作

echo ============================================
echo WinAgent Human-Like Demo (Batch)
echo ============================================

REM Step 1: Launch Notepad
echo.
echo [1] Launching Notepad...
start notepad

REM Wait for startup
timeout /t 2 /nobreak >nul

REM Step 2: Type message
echo [2] Typing message...
powershell -Command "$w = Start-Process notepad -PassThru; Start-Sleep 1; Add-Type -AssemblyName 'System.Windows.Forms'; [System.Windows.Forms.SendKeys]::SendWait('Hi, I win - %date% %time:~0,5%'); $w.Id"

timeout /t 1 /nobreak >nul

REM Step 3: Save As (Ctrl+Shift+S)
echo [3] Save As (Ctrl+Shift+S)...
powershell -Command "Add-Type -AssemblyName 'System.Windows.Forms'; [System.Windows.Forms.SendKeys]::SendWait('^+(s)')"

timeout /t 2 /nobreak >nul

REM Step 4: Type filename
echo [4] Typing filename...
for /f "tokens=1-4 delims=/: " %%a in ('time /t') do set timestr=%%a%%b%%c%%d
set fname=WinTest_%timestr:~0,-1%.txt
echo Filename: %fname%

powershell -Command "Add-Type -AssemblyName 'System.Windows.Forms'; [System.Windows.Forms.SendKeys]::SendWait('%fname%')"

timeout /t 1 /nobreak >nul

REM Step 5: Press Enter to save
echo [5] Saving...
powershell -Command "Add-Type -AssemblyName 'System.Windows.Forms'; [System.Windows.Forms.SendKeys]::SendWait('{ENTER}')"

timeout /t 2 /nobreak >nul

echo.
echo ============================================
echo [Done] Check Documents folder for file
echo ============================================

REM Close notepad after delay
timeout /t 3 /nobreak >nul
taskkill /IM notepad.exe /F 2>nul
