namespace WinAgent.Services;

public static class Logger
{
    private static readonly object _lock = new();
    private static readonly string _logFilePath;
    private static readonly Queue<string> _recentLogs = new();
    private const int MaxRecentLogs = 100;

    static Logger()
    {
        string logDir = Path.Combine(AppContext.BaseDirectory, "logs");
        Directory.CreateDirectory(logDir);
        _logFilePath = Path.Combine(logDir, $"winagent_{DateTime.Now:yyyyMMdd}.log");
    }

    public static void Log(string message, LogLevel level = LogLevel.Info)
    {
        string timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss.fff");
        string logEntry = $"[{timestamp}] [{level}] {message}";

        lock (_lock)
        {
            Console.WriteLine(logEntry);
            
            try
            {
                File.AppendAllText(_logFilePath, logEntry + Environment.NewLine);
            }
            catch { }

            _recentLogs.Enqueue(logEntry);
            while (_recentLogs.Count > MaxRecentLogs)
            {
                _recentLogs.Dequeue();
            }
        }
    }

    public static void LogError(string message, Exception? ex = null)
    {
        string fullMessage = ex != null ? $"{message}: {ex.Message}\n{ex.StackTrace}" : message;
        Log(fullMessage, LogLevel.Error);
    }

    public static void LogWarning(string message)
    {
        Log(message, LogLevel.Warning);
    }

    public static List<string> GetRecentLogs(int count = 50)
    {
        lock (_lock)
        {
            return _recentLogs.TakeLast(count).ToList();
        }
    }

    public static string LogFilePath => _logFilePath;
}

public enum LogLevel
{
    Debug,
    Info,
    Warning,
    Error
}