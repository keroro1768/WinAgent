namespace WinAgent.Models;

public class WindowInfo
{
    public IntPtr Handle { get; set; }
    public string Title { get; set; } = string.Empty;
    public string ClassName { get; set; } = string.Empty;
    public string ProcessName { get; set; } = string.Empty;
    public int ProcessId { get; set; }

    public override string ToString()
    {
        return $"[{ProcessId}] {ProcessName}: {Title}";
    }
}