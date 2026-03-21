# WinAgent - Windows Window Monitor Agent

A Windows desktop monitoring tool that runs in the system tray, monitors foreground windows, executes external programs (like Claude Code), and manages input methods.

## Features

- **System Tray Icon**: Runs in the background, click to show window
- **Foreground Window Monitoring**: Uses Win32 API to monitor active windows
- **External Program Execution**: Spawn and manage external processes with real-time output capture
- **Keyboard Input**: Send keyboard input to target windows
- **Input Method Detection**: Detect and switch to English input method
- **Claude Code Management**: Maintains exactly 2 Claude Code instances running
- **Startup Registration**: Runs automatically at Windows boot

## Project Structure

```
winagent/
├── WinAgent.csproj           # Project file
├── Program.cs               # Main entry point
├── Models/
│   ├── WindowInfo.cs         # Window information model
│   └── ProcessInfo.cs        # Process information model
├── Services/
│   ├── WindowService.cs      # Foreground window monitoring
│   ├── TrayService.cs        # System tray functionality
│   ├── ProcessManager.cs    # External process management
│   ├── ClaudeManager.cs     # Claude Code instance manager
│   ├── InputMethodService.cs # Input method detection/switching
│   ├── StartupService.cs    # Windows startup registration
│   └── Logger.cs            # Logging service
├── Native/
│   └── Win32.cs             # Win32 P/Invoke declarations
└── bin/Release/net8.0-windows/
    └── WinAgent.exe         # Built executable
```

## Requirements

- .NET 8.0 SDK
- Windows 10/11

## Building

```bash
cd winagent
dotnet restore
dotnet build --configuration Release
```

The executable will be at `bin\Release\net8.0-windows\WinAgent.exe`

## Usage

```
WinAgent.exe                 # Start normally
WinAgent.exe --minimized     # Start minimized to tray
WinAgent.exe --no-claude     # Start without Claude instances
```

### System Tray Options
- **Left Click**: Show main window
- **Right Click**: Context menu
  - Show Window
  - Status
  - Exit

## Command Line Arguments

| Argument | Description |
|----------|-------------|
| `--minized`, `-m` | Start minimized to system tray |
| `--no-claude` | Don't start Claude Code instances |

## Features Implemented

1. ✅ System tray icon with context menu
2. ✅ Foreground window monitoring using Win32 API
3. ✅ External program execution with real-time output
4. ✅ Keyboard input to target windows
5. ✅ Input method detection and switching to English
6. ✅ Maintain 2 Claude Code instances
7. ✅ Windows startup registration

## Logs

Logs are stored at: `%LOCALAPPDATA%\WinAgent\logs\winagent_YYYYMMDD.log`