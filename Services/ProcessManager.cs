using System.Diagnostics;
using WinAgent.Models;

namespace WinAgent.Services;

public class ProcessManager
{
    private readonly List<ProcessInfo> _processes = new();
    private readonly object _lock = new();
    private int _nextInstanceId = 1;

    public event Action<int, string>? OnOutput;
    public event Action<int, string>? OnError;
    public event Action<int, int>? OnProcessExited;

    public async Task<ProcessInfo> SpawnProcessAsync(string executablePath, string arguments = "", bool captureOutput = true)
    {
        var processInfo = new ProcessInfo
        {
            InstanceId = _nextInstanceId++,
            ExecutablePath = executablePath,
            Arguments = arguments,
            Status = ProcessStatus.Starting,
            StartTime = DateTime.Now
        };

        try
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = executablePath,
                Arguments = arguments,
                UseShellExecute = false,
                RedirectStandardOutput = captureOutput,
                RedirectStandardError = captureOutput,
                CreateNoWindow = true,
                WorkingDirectory = Path.GetDirectoryName(executablePath) ?? AppContext.BaseDirectory
            };

            var process = new Process { StartInfo = startInfo };
            processInfo.ProcessId = process.Id;
            processInfo.Name = Path.GetFileNameWithoutExtension(executablePath);

            if (captureOutput)
            {
                process.OutputDataReceived += (sender, e) =>
                {
                    if (e.Data != null)
                    {
                        processInfo.LastOutputTime = DateTime.Now;
                        OnOutput?.Invoke(processInfo.InstanceId, e.Data);
                    }
                };

                process.ErrorDataReceived += (sender, e) =>
                {
                    if (e.Data != null)
                    {
                        OnError?.Invoke(processInfo.InstanceId, e.Data);
                    }
                };
            }

            process.EnableRaisingEvents = true;
            process.Exited += (sender, e) =>
            {
                lock (_lock)
                {
                    processInfo.Status = ProcessStatus.Crashed;
                    OnProcessExited?.Invoke(processInfo.InstanceId, process.ExitCode);
                    Logger.Log($"Process {processInfo.Name} (Instance {processInfo.InstanceId}) exited with code {process.ExitCode}");
                }
            };

            process.Start();
            processInfo.ProcessId = process.Id;
            processInfo.Status = ProcessStatus.Running;

            if (captureOutput)
            {
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();
            }

            Logger.Log($"Started process {processInfo.Name} (Instance {processInfo.InstanceId}, PID: {processInfo.ProcessId})");
        }
        catch (Exception ex)
        {
            Logger.LogError($"Failed to start process: {executablePath}", ex);
            processInfo.Status = ProcessStatus.Stopped;
        }

        lock (_lock)
        {
            _processes.Add(processInfo);
        }

        return processInfo;
    }

    public void SendInput(int instanceId, string input)
    {
        var processInfo = GetProcess(instanceId);
        if (processInfo == null) return;

        try
        {
            var process = Process.GetProcessById(processInfo.ProcessId);
            if (!process.HasExited)
            {
                process.StandardInput.WriteLine(input);
                process.StandardInput.Flush();
                Logger.Log($"Sent input to instance {instanceId}: {input}");
            }
        }
        catch (Exception ex)
        {
            Logger.LogError($"Failed to send input to instance {instanceId}", ex);
        }
    }

    public void SendKeys(int instanceId, string keys)
    {
        var processInfo = GetProcess(instanceId);
        if (processInfo == null) return;

        try
        {
            var hwnd = Process.GetProcessById(processInfo.ProcessId).MainWindowHandle;
            if (hwnd != IntPtr.Zero)
            {
                Native.Win32.PostMessage(hwnd, Native.Win32.WM_CHAR, IntPtr.Zero, IntPtr.Zero);
                Logger.Log($"Sent keys to instance {instanceId}");
            }
        }
        catch (Exception ex)
        {
            Logger.LogError($"Failed to send keys to instance {instanceId}", ex);
        }
    }

    public void KillProcess(int instanceId)
    {
        var processInfo = GetProcess(instanceId);
        if (processInfo == null) return;

        try
        {
            var process = Process.GetProcessById(processInfo.ProcessId);
            if (!process.HasExited)
            {
                process.Kill();
                process.WaitForExit(5000);
                Logger.Log($"Killed process instance {instanceId}");
            }
        }
        catch (Exception ex)
        {
            Logger.LogError($"Failed to kill instance {instanceId}", ex);
        }
        finally
        {
            lock (_lock)
            {
                _processes.Remove(processInfo);
            }
        }
    }

    public ProcessInfo? GetProcess(int instanceId)
    {
        lock (_lock)
        {
            return _processes.FirstOrDefault(p => p.InstanceId == instanceId);
        }
    }

    public List<ProcessInfo> GetAllProcesses()
    {
        lock (_lock)
        {
            return _processes.ToList();
        }
    }

    public int GetRunningCount()
    {
        lock (_lock)
        {
            return _processes.Count(p => p.Status == ProcessStatus.Running);
        }
    }
}