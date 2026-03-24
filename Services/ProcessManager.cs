using System.Diagnostics;
using WinAgent.Models;

namespace WinAgent.Services;

public class ProcessManager
{
    private readonly List<ProcessInfo> _processes = new();
    private readonly Dictionary<int, Process> _processHandles = new();
    private readonly object _lock = new();
    private int _nextInstanceId = 1;

    public event Action<int, string>? OnOutput;
    public event Action<int, string>? OnError;
    public event Action<int, int>? OnProcessExited;

    public async Task<ProcessInfo> SpawnProcessAsync(
        string executablePath,
        string arguments = "",
        bool captureOutput = true,
        bool redirectInput = false,
        string? workingDirectory = null)
    {
        var processInfo = new ProcessInfo
        {
            InstanceId = _nextInstanceId++,
            ExecutablePath = executablePath,
            Arguments = arguments,
            Status = ProcessStatus.Starting,
            StartTime = DateTime.Now,
            Name = Path.GetFileNameWithoutExtension(executablePath)
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
                RedirectStandardInput = redirectInput,
                CreateNoWindow = true,
                WorkingDirectory = workingDirectory
                    ?? Path.GetDirectoryName(executablePath)
                    ?? AppContext.BaseDirectory
            };

            var process = new Process { StartInfo = startInfo };

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
                    _processHandles.Remove(processInfo.InstanceId);
                }
                OnProcessExited?.Invoke(processInfo.InstanceId, process.ExitCode);
                Logger.Log($"Process {processInfo.Name} (Instance {processInfo.InstanceId}) exited with code {process.ExitCode}");
            };

            process.Start();
            processInfo.ProcessId = process.Id;
            processInfo.Status = ProcessStatus.Running;

            if (captureOutput)
            {
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();
            }

            lock (_lock)
            {
                _processHandles[processInfo.InstanceId] = process;
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
        lock (_lock)
        {
            if (!_processHandles.TryGetValue(instanceId, out var process))
            {
                Logger.LogWarning($"No process handle for instance {instanceId}");
                return;
            }

            try
            {
                if (!process.HasExited && process.StartInfo.RedirectStandardInput)
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
    }

    public void KillProcess(int instanceId)
    {
        Process? process;
        ProcessInfo? processInfo;

        lock (_lock)
        {
            processInfo = _processes.FirstOrDefault(p => p.InstanceId == instanceId);
            _processHandles.TryGetValue(instanceId, out process);
        }

        if (processInfo == null) return;

        try
        {
            if (process != null && !process.HasExited)
            {
                process.Kill(entireProcessTree: true);
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
                _processHandles.Remove(instanceId);
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