namespace WinAgent.Models;

public class ProcessInfo
{
    public int InstanceId { get; set; }
    public int ProcessId { get; set; }
    public string Name { get; set; } = string.Empty;
    public string ExecutablePath { get; set; } = string.Empty;
    public string Arguments { get; set; } = string.Empty;
    public ProcessStatus Status { get; set; } = ProcessStatus.Stopped;
    public DateTime StartTime { get; set; }
    public DateTime? LastOutputTime { get; set; }
    public int RestartCount { get; set; }
}

public enum ProcessStatus
{
    Starting,
    Running,
    Stopped,
    Crashed
}