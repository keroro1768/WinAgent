using System.Text;
using WinAgent.Native;

namespace WinAgent.Services;

public class InputMethodService
{
    private const string EnglishLayout = "00000409"; // US English keyboard layout

    public string GetCurrentInputMethod()
    {
        IntPtr hwnd = Win32.GetForegroundWindow();
        IntPtr imeWnd = Win32.ImmGetDefaultIMEWnd(hwnd);
        
        // Get keyboard layout for current thread
        IntPtr hkl = Win32.GetKeyboardLayout(0);
        
        return GetLayoutLanguage(hkl);
    }

    public string GetLayoutLanguage(IntPtr hkl)
    {
        // Get language ID from keyboard layout
        uint langId = (uint)(hkl.ToInt64() & 0xFFFF);
        
        // Convert to culture name
        try
        {
            var culture = new System.Globalization.CultureInfo((int)langId);
            return culture.EnglishName;
        }
        catch
        {
            return $"0x{langId:X4}";
        }
    }

    public bool IsEnglish()
    {
        IntPtr hkl = Win32.GetKeyboardLayout(0);
        uint langId = (uint)(hkl.ToInt64() & 0xFFFF);
        
        // 0x0409 = US English
        return langId == 0x0409 || langId == 0x0809 || langId == 0x0C09 || langId == 0x1009;
    }

    public async Task<bool> SwitchToEnglishAsync(int timeoutMs = 5000)
    {
        if (IsEnglish())
        {
            Logger.Log("Input method is already English");
            return true;
        }

        Logger.Log("Switching input method to English...");

        try
        {
            // Get all keyboard layouts
            IntPtr[] layouts = new IntPtr[10];
            int count = Win32.GetKeyboardLayoutList(layouts.Length, layouts);

            // Find English layout
            IntPtr englishLayout = IntPtr.Zero;
            for (int i = 0; i < count; i++)
            {
                uint langId = (uint)(layouts[i].ToInt64() & 0xFFFF);
                if (langId == 0x0409 || langId == 0x0809 || langId == 0x0C09 || langId == 0x1009)
                {
                    englishLayout = layouts[i];
                    break;
                }
            }

            if (englishLayout == IntPtr.Zero)
            {
                // Load US English layout if not found
                englishLayout = Win32.LoadKeyboardLayout(EnglishLayout, Win32.KLF_ACTIVATE | Win32.KLF_REORDER);
            }

            if (englishLayout != IntPtr.Zero)
            {
                Win32.ActivateKeyboardLayout(englishLayout, Win32.KLF_ACTIVATE);
                Logger.Log("Input method switched to English");
                return true;
            }
        }
        catch (Exception ex)
        {
            Logger.LogError("Failed to switch input method", ex);
        }

        // Fallback: try using simulated keypress to switch
        await SwitchUsingKeypressAsync();
        
        return IsEnglish();
    }

    private async Task SwitchUsingKeypressAsync()
    {
        try
        {
            // Simulate Alt+Shift to cycle through input methods
            // This is a common hotkey for switching input methods
            await Task.Delay(100);
            
            // Get the foreground window and send the key combo
            IntPtr hwnd = Win32.GetForegroundWindow();
            if (hwnd != IntPtr.Zero)
            {
                // Alt+Shift is typically handled at system level, 
                // so we try sending the keys to the foreground window
                Logger.Log("Trying to switch via keypress simulation...");
            }
        }
        catch (Exception ex)
        {
            Logger.LogError("Keypress switching failed", ex);
        }
    }

    public async Task<bool> WaitForEnglishAsync(int timeoutMs = 3000)
    {
        int elapsed = 0;
        int checkInterval = 100;

        while (elapsed < timeoutMs)
        {
            if (IsEnglish())
                return true;

            await Task.Delay(checkInterval);
            elapsed += checkInterval;
        }

        return IsEnglish();
    }

    public void EnsureEnglishBeforeInput()
    {
        if (!IsEnglish())
        {
            Logger.LogWarning("Input method is not English, attempting to switch...");
            _ = SwitchToEnglishAsync();
        }
    }
}