using System.Diagnostics;
using System.Text;
using WinAgent.Models;

namespace WinAgent.Services;

/// <summary>
/// Manages Claude Code CLI instances.
/// Approach A: Interactive mode — long-running process with stdin/stdout via --input-format stream-json
/// Approach B: One-shot mode — single `claude -p "prompt"` calls per task
/// </summary>
public class ClaudeManager : ProcessManager
{
    private readonly string _claudePath;
    private readonly string _workingDirectory;
    private readonly int _targetCount;
    private System.Timers.Timer? _maintenanceTimer;
    private bool _isMaintaining = false;

    public event Action<int, string>? OnClaudeOutput;

    public ClaudeManager(string? claudePath = null, string? workingDirectory = null, int targetCount = 1)
    {
        _claudePath = claudePath ?? FindClaudePath();
        _workingDirectory = workingDirectory ?? AppContext.BaseDirectory;
        _targetCount = targetCount;

        OnOutput += (instanceId, output) =>
        {
            OnClaudeOutput?.Invoke(instanceId, output);
            Logger.Log($"[Claude #{instanceId}] {output}");
        };

        OnError += (instanceId, error) =>
        {
            Logger.LogWarning($"[Claude #{instanceId}] STDERR: {error}");
        };

        OnProcessExited += async (instanceId, exitCode) =>
        {
            Logger.LogWarning($"Claude instance {instanceId} exited with code {exitCode}");
        };
    }

    // ============================================
    // Approach A: Interactive long-running process
    // ============================================

    /// <summary>
    /// Start interactive Claude instances that stay alive and accept stdin input.
    /// Uses --input-format stream-json for programmatic I/O.
    /// </summary>
    public async Task StartInteractiveAsync()
    {
        Logger.Log($"Starting ClaudeManager (interactive mode, target={_targetCount})...");

        for (int i = 0; i < _targetCount; i++)
        {
            await SpawnInteractiveAsync();
        }

        // Maintenance timer to keep target instance count
        _maintenanceTimer = new System.Timers.Timer(10000);
        _maintenanceTimer.Elapsed += async (s, e) => await MaintainInstancesAsync();
        _maintenanceTimer.Start();

        Logger.Log($"ClaudeManager started with {GetRunningCount()} interactive instances");
    }

    private async Task<ProcessInfo> SpawnInteractiveAsync()
    {
        if (!File.Exists(_claudePath))
        {
            Logger.LogError($"Claude executable not found: {_claudePath}");
            throw new FileNotFoundException("Claude CLI not found", _claudePath);
        }

        // Interactive mode: use stream-json for programmatic stdin/stdout
        string args = string.Join(" ",
            "--print",
            "--output-format stream-json",
            "--input-format stream-json",
            "--dangerously-skip-permissions",
            "--verbose"
        );

        var info = await SpawnProcessAsync(
            _claudePath,
            args,
            captureOutput: true,
            redirectInput: true,
            workingDirectory: _workingDirectory
        );

        Logger.Log($"Spawned interactive Claude instance {info.InstanceId} (PID: {info.ProcessId})");
        return info;
    }

    /// <summary>
    /// Send a prompt to a specific interactive instance via stdin.
    /// </summary>
    public void SendPrompt(int instanceId, string prompt)
    {
        // For stream-json input format, wrap as JSON
        string json = System.Text.Json.JsonSerializer.Serialize(new { type = "user_message", content = prompt });
        SendInput(instanceId, json);
        Logger.Log($"Sent prompt to Claude #{instanceId}: {prompt.Substring(0, Math.Min(80, prompt.Length))}...");
    }

    /// <summary>
    /// Send a prompt to all running interactive instances.
    /// </summary>
    public void SendPromptToAll(string prompt)
    {
        var processes = GetAllProcesses().Where(p => p.Status == ProcessStatus.Running).ToList();
        foreach (var p in processes)
        {
            SendPrompt(p.InstanceId, prompt);
        }
    }

    private async Task MaintainInstancesAsync()
    {
        if (_isMaintaining) return;
        _isMaintaining = true;

        try
        {
            int currentCount = GetAllProcesses().Count(p => p.Status == ProcessStatus.Running);

            if (currentCount < _targetCount)
            {
                int toStart = _targetCount - currentCount;
                Logger.Log($"Maintenance: starting {toStart} more Claude instances...");
                for (int i = 0; i < toStart; i++)
                {
                    await SpawnInteractiveAsync();
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

    // ============================================
    // Approach B: One-shot mode (simple & reliable)
    // ============================================

    /// <summary>
    /// Execute a single Claude prompt and return the output.
    /// This spawns a new process, waits for completion, and returns the result.
    /// Most reliable approach — no interactive session management needed.
    /// </summary>
    public async Task<ClaudeResult> ExecuteOneShotAsync(
        string prompt,
        int timeoutSeconds = 120,
        string? outputFormat = "text",
        string? permissionMode = "bypassPermissions")
    {
        if (!File.Exists(_claudePath))
        {
            return new ClaudeResult
            {
                Success = false,
                Error = $"Claude CLI not found: {_claudePath}"
            };
        }

        Logger.Log($"ExecuteOneShot: path={_claudePath}, prompt={prompt.Substring(0, Math.Min(100, prompt.Length))}...");

        var args = new StringBuilder();
        args.Append("--print ");
        args.Append($"--output-format {outputFormat} ");
        args.Append("--dangerously-skip-permissions ");
        args.Append($"-p \"{EscapeArgument(prompt)}\"");

        Logger.Log($"ExecuteOneShot args: {args}");

        var result = new ClaudeResult();
        var outputBuilder = new StringBuilder();
        var errorBuilder = new StringBuilder();

        try
        {
            var startInfo = new ProcessStartInfo
            {
                FileName = _claudePath,
                Arguments = args.ToString(),
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
                WorkingDirectory = _workingDirectory
            };

            using var process = new Process { StartInfo = startInfo };

            process.OutputDataReceived += (s, e) =>
            {
                if (e.Data != null)
                {
                    Logger.Log($"[OneShot stdout] {e.Data}");
                    outputBuilder.AppendLine(e.Data);
                }
            };

            process.ErrorDataReceived += (s, e) =>
            {
                if (e.Data != null)
                {
                    Logger.Log($"[OneShot stderr] {e.Data}");
                    errorBuilder.AppendLine(e.Data);
                }
            };

            process.Start();
            Logger.Log($"OneShot process started, PID={process.Id}");
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();

            bool exited = await Task.Run(() => process.WaitForExit(timeoutSeconds * 1000));

            if (!exited)
            {
                process.Kill(entireProcessTree: true);
                result.Success = false;
                result.Error = $"Timed out after {timeoutSeconds}s";
                Logger.LogWarning($"Claude one-shot timed out after {timeoutSeconds}s");
            }
            else
            {
                result.ExitCode = process.ExitCode;
                result.Success = process.ExitCode == 0;
                result.Output = outputBuilder.ToString().TrimEnd();
                result.Error = errorBuilder.ToString().TrimEnd();

                Logger.Log($"Claude one-shot completed (exit={process.ExitCode}, output={result.Output.Length} chars)");
            }
        }
        catch (Exception ex)
        {
            result.Success = false;
            result.Error = ex.Message;
            Logger.LogError("Claude one-shot execution failed", ex);
        }

        return result;
    }

    /// <summary>
    /// Convenience: execute a prompt and return just the text output.
    /// </summary>
    public async Task<string?> AskClaudeAsync(string prompt, int timeoutSeconds = 120)
    {
        var result = await ExecuteOneShotAsync(prompt, timeoutSeconds);
        if (result.Success)
            return result.Output;

        Logger.LogWarning($"AskClaude failed: {result.Error}");
        return null;
    }

    // ============================================
    // Shared utilities
    // ============================================

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

    public List<ProcessInfo> GetClaudeStatuses() => GetAllProcesses();

    private static string FindClaudePath()
    {
        string home = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
        string appData = Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData);
        string localAppData = Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData);

        string[] candidates = new[]
        {
            Path.Combine(home, ".local", "bin", "claude.exe"),
            Path.Combine(appData, "npm", "claude.cmd"),
            Path.Combine(appData, "npm", "claude"),
            Path.Combine(localAppData, "Programs", "claude", "claude.exe"),
            @"C:\Program Files\nodejs\claude.cmd",
        };

        Logger.Log($"FindClaudePath: searching in {candidates.Length} locations (home={home})");

        foreach (var path in candidates)
        {
            if (File.Exists(path))
            {
                Logger.Log($"Found Claude at: {path}");
                return path;
            }
        }

        // Try PATH via where command
        try
        {
            var psi = new ProcessStartInfo("where", "claude")
            {
                UseShellExecute = false,
                RedirectStandardOutput = true,
                CreateNoWindow = true
            };
            using var proc = Process.Start(psi);
            string? output = proc?.StandardOutput.ReadLine();
            proc?.WaitForExit(3000);
            if (!string.IsNullOrEmpty(output) && File.Exists(output))
            {
                Logger.Log($"Found Claude via PATH: {output}");
                return output;
            }
        }
        catch { }

        Logger.LogWarning("Claude not found, using fallback 'claude'");
        return "claude";
    }

    private static string EscapeArgument(string arg)
    {
        return arg
            .Replace("\\", "\\\\")
            .Replace("\"", "\\\"")
            .Replace("\n", "\\n")
            .Replace("\r", "");
    }
}

public class ClaudeResult
{
    public bool Success { get; set; }
    public string Output { get; set; } = string.Empty;
    public string Error { get; set; } = string.Empty;
    public int ExitCode { get; set; }
}
