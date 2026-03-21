using Microsoft.Win32;

namespace WinAgent.Services;

public static class StartupService
{
    private const string AppName = "WinAgent";
    private const string RegistryKey = @"SOFTWARE\Microsoft\Windows\CurrentVersion\Run";

    public static bool IsRegistered()
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(RegistryKey, false);
            return key?.GetValue(AppName) != null;
        }
        catch (Exception ex)
        {
            Logger.LogError("Failed to check startup registration", ex);
            return false;
        }
    }

    public static bool RegisterStartup()
    {
        try
        {
            string exePath = Environment.ProcessPath ?? System.Reflection.Assembly.GetExecutingAssembly().Location;
            
            using var key = Registry.CurrentUser.OpenSubKey(RegistryKey, true);
            if (key == null)
            {
                Logger.LogError("Failed to open registry key");
                return false;
            }

            key.SetValue(AppName, $"\"{exePath}\"");
            Logger.Log("Registered startup: " + exePath);
            return true;
        }
        catch (Exception ex)
        {
            Logger.LogError("Failed to register startup", ex);
            return false;
        }
    }

    public static bool UnregisterStartup()
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(RegistryKey, true);
            if (key == null)
            {
                return true;
            }

            if (key.GetValue(AppName) != null)
            {
                key.DeleteValue(AppName);
                Logger.Log("Unregistered startup");
            }

            return true;
        }
        catch (Exception ex)
        {
            Logger.LogError("Failed to unregister startup", ex);
            return false;
        }
    }

    public static void EnsureRegistered()
    {
        if (!IsRegistered())
        {
            RegisterStartup();
        }
    }
}