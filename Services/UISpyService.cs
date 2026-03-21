using System.Windows.Automation;
using WinAgent.Models;

namespace WinAgent.Services;

/// <summary>
/// Service for enumerating UI controls/elements in a window using Windows UI Automation API.
/// </summary>
public class UISpyService
{
    private readonly IntPtr _ownWindowHandle;
    private readonly string _ownProcessName;

    public UISpyService(IntPtr ownWindowHandle, string ownProcessName)
    {
        _ownWindowHandle = ownWindowHandle;
        _ownProcessName = ownProcessName;
    }

    /// <summary>
    /// Checks if the given window belongs to WinAgent itself.
    /// </summary>
    public bool IsOwnWindow(IntPtr hwnd)
    {
        return hwnd == _ownWindowHandle;
    }

    /// <summary>
    /// Checks if the given window belongs to WinAgent process.
    /// </summary>
    public bool IsOwnProcess(WindowInfo windowInfo)
    {
        return windowInfo.ProcessName.Equals(_ownProcessName, StringComparison.OrdinalIgnoreCase);
    }

    /// <summary>
    /// Enumerates all controls in the specified window and returns them as a tree structure.
    /// </summary>
    public List<UIElementInfo> EnumerateControls(IntPtr windowHandle)
    {
        var elements = new List<UIElementInfo>();

        if (windowHandle == IntPtr.Zero)
            return elements;

        try
        {
            // Get the root element for the specified window
            AutomationElement windowElement = AutomationElement.FromHandle(windowHandle);
            
            if (windowElement == null)
            {
                Logger.LogWarning($"Could not get AutomationElement for window handle: {windowHandle}");
                return elements;
            }

            // Get all descendants using TreeWalker
            TreeWalker walker = TreeWalker.ControlViewWalker;
            AutomationElement? child = walker.GetFirstChild(windowElement);

            while (child != null)
            {
                var elementInfo = ConvertToElementInfo(child, walker, 0);
                if (elementInfo != null)
                {
                    elements.Add(elementInfo);
                }
                child = walker.GetNextSibling(child);
            }
        }
        catch (Exception ex)
        {
            Logger.LogError($"Error enumerating controls for window handle {windowHandle}", ex);
        }

        return elements;
    }

    /// <summary>
    /// Recursively converts AutomationElement to UIElementInfo with tree structure.
    /// </summary>
    private UIElementInfo? ConvertToElementInfo(AutomationElement element, TreeWalker walker, int depth)
    {
        if (element == null)
            return null;

        try
        {
            var info = new UIElementInfo
            {
                ControlType = GetControlTypeName(element),
                Name = GetElementName(element),
                Handle = element.Current.NativeWindowHandle,
                Depth = depth,
                AutomationElement = element
            };

            // Get children recursively
            AutomationElement? child = walker.GetFirstChild(element);
            while (child != null)
            {
                var childInfo = ConvertToElementInfo(child, walker, depth + 1);
                if (childInfo != null)
                {
                    info.Children.Add(childInfo);
                }
                child = walker.GetNextSibling(child);
            }

            return info;
        }
        catch (Exception ex)
        {
            // Some elements may throw exceptions when accessed
            Logger.LogWarning($"Error getting element info: {ex.Message}");
            return null;
        }
    }

    /// <summary>
    /// Gets a human-readable name for the control type.
    /// </summary>
    private string GetControlTypeName(AutomationElement element)
    {
        try
        {
            if (element.Current.ControlType != null)
            {
                return element.Current.ControlType.ProgrammaticName?.Replace("ControlType.", "") ?? "Unknown";
            }
        }
        catch
        {
            // Ignore
        }
        return "Unknown";
    }

    /// <summary>
    /// Gets the name/text of the element.
    /// </summary>
    private string GetElementName(AutomationElement element)
    {
        try
        {
            string? name = element.Current.Name;
            if (!string.IsNullOrWhiteSpace(name))
                return name;

            // Try to get automation id as fallback
            string? automationId = element.Current.AutomationId;
            if (!string.IsNullOrWhiteSpace(automationId))
                return $"[{automationId}]";

            // Try to get value
            var valuePattern = element.GetCurrentPattern(ValuePattern.Pattern) as ValuePattern;
            if (valuePattern != null && !string.IsNullOrWhiteSpace(valuePattern.Current.Value))
            {
                return valuePattern.Current.Value;
            }
        }
        catch
        {
            // Ignore
        }
        return "(No name)";
    }
}

/// <summary>
/// Represents a UI element in the control tree.
/// </summary>
public class UIElementInfo
{
    public string ControlType { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public IntPtr Handle { get; set; }
    public int Depth { get; set; }
    public List<UIElementInfo> Children { get; set; } = new();

    public string DisplayText => $"[{ControlType}] {Name} (Handle: {Handle})";
    
    // Hidden reference to the AutomationElement for interaction
    public object? AutomationElement { get; set; }
}
