using WinAgent.Models;

namespace WinAgent.Services;

public class ClaudeManager : ProcessManager
{
    private readonly string _claudePath;
    private readonly int _targetCount;
    private System.Timers.Timer? _maintenanceTimer;
    private readonly object _lock = new();
    private bool _isMaintaining = false;

    public event Action<int, string>? OnClaudeOutput;

    public ClaudeManager(string claudePath, int targetCount = 2)
    {
        _claudePath = claudePath;
        _targetCount = targetCount;

        OnOutput += (instanceId, output) =>
        {
            OnClaudeOutput?.Invoke(instanceId, output);
            Logger.Log($"[Claude #{instanceId}] {output}");
        };

        OnError += (instanceId, error) =>
        {
            Logger.LogWarning($"[Claude #{instanceId}] ERROR: {error}");
        };

        OnProcessExited += async (instanceId, exitCode) =>
        {
            await HandleProcessExit(instanceId, exitCode);
        };
    }

    public async Task StartAsync()
    {
        Logger.Log("Starting ClaudeManager...");
        
        // Start initial instances
        for (int i = 0; i < _targetCount; i++)
        {
            await SpawnClaudeAsync();
        }

        // Start maintenance timer to ensure we always have exactly 2 instances
        _maintenanceTimer = new System.Timers.Timer(5000); // Check every 5 seconds
        _maintenanceTimer.Elapsed += async (s, e) => await MaintainInstancesAsync();
        _maintenanceTimer.Start();

        Logger.Log($"ClaudeManager started with {_targetCount} instances");
    }

    private async Task SpawnClaudeAsync()
    {
        if (!File.Exists(_claudePath))
        {
            Logger.LogError($"Claude executable not found: {_claudePath}");
            return;
        }

        await SpawnProcessAsync(_claudePath, "--print --permission-mode bypassPermissions", captureOutput: true);
    }

    private async Task MaintainInstancesAsync()
    {
        if (_isMaintaining) return;
        _isMaintaining = true;

        try
        {
            var runningProcesses = GetAllProcesses()
                .Where(p => p.Status == ProcessStatus.Running)
                .ToList();

            int currentCount = runningProcesses.Count;

            if (currentCount < _targetCount)
            {
                int toStart = _targetCount - currentCount;
                Logger.Log($"Starting {toStart} more Claude instances...");
                
                for (int i = 0; i < toStart; i++)
                {
                    await SpawnClaudeAsync();
                }
            }
            else if (currentCount > _targetCount)
            {
                // Kill extra instances (keep the newest ones)
                var toKill = runningProcesses
                    .OrderBy(p => p.StartTime)
                    .Take(currentCount - _targetCount)
                    .ToList();

                foreach (var p in toKill)
                {
                    Logger.Log($"Stopping extra instance {p.InstanceId}");
                    KillProcess(p.InstanceId);
                }
            }
        }
        catch (Exception ex)
        {
            Logger.LogError("Error during maintenance", ex);
        }
        finally
        {
            _isMaintaining = false;
        }
    }

    private async Task HandleProcessExit(int instanceId, int exitCode)
    {
        Logger.LogWarning($"Claude instance {instanceId} exited with code {exitCode}");
        
        // Small delay before restart
        await Task.Delay(1000);
        
        // Check if we need to restart
        var runningCount = GetAllProcesses().Count(p => p.Status == ProcessStatus.Running);
        if (runningCount < _targetCount)
        {
            Logger.Log($"Restarting Claude instance {instanceId}...");
            await SpawnClaudeAsync();
        }
    }

    public void Stop()
    {
        _maintenanceTimer?.Stop();
        _maintenanceTimer?.Dispose();

        var processes = GetAllProcesses();
        foreach (var p in processes)
        {
            KillProcess(p.InstanceId);
        }

        Logger.Log("ClaudeManager stopped");
    }

    public void SendToClaude(int instanceId, string command)
    {
        SendInput(instanceId, command);
    }

    public void SendToAll(string command)
    {
        var processes = GetAllProcesses()
            .Where(p => p.Status == ProcessStatus.Running)
            .ToList();

        foreach (var p in processes)
        {
            SendInput(p.InstanceId, command);
        }
    }

    public List<ProcessInfo> GetClaudeStatuses()
    {
        return GetAllProcesses();
    }
}