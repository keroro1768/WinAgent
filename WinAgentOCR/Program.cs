using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Runtime.InteropServices;
using System.Collections.Generic;
using System.Threading.Tasks;
using Windows.Graphics.Imaging;
using Windows.Media.Ocr;
using Windows.Storage.Streams;

class Program
{
    [DllImport("user32.dll")]
    static extern bool GetWindowRect(IntPtr hWnd, ref RECT lpRect);

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }

    static async Task Main(string[] args)
    {
        Console.WriteLine("=== WinAgent OCR - Tab Finder ===\n");
        
        // Default to WinDBG
        IntPtr hwnd = args.Length > 0 ? new IntPtr(Convert.ToInt64(args[0], 16)) : new IntPtr(0x50720);
        
        RECT rect = new RECT();
        GetWindowRect(hwnd, ref rect);
        
        int width = rect.Right - rect.Left;
        int height = rect.Bottom - rect.Top;
        
        Console.WriteLine($"Window: ({rect.Left}, {rect.Top}) {width}x{height}\n");
        
        if (width <= 0 || height <= 0) return;
        
        // Capture screen
        using (Bitmap bitmap = new Bitmap(width, height))
        {
            using (Graphics g = Graphics.FromImage(bitmap))
            {
                g.CopyFromScreen(rect.Left, rect.Top, 0, 0, new System.Drawing.Size(width, height));
            }
            
            string tempFile = Path.Combine(Path.GetTempPath(), "winagent_ocr.png");
            bitmap.Save(tempFile, ImageFormat.Png);
            
            // OCR
            var tabs = await FindTabs(tempFile, rect.Left, rect.Top);
            
            Console.WriteLine("\n=== Found Tabs ===");
            foreach (var tab in tabs)
            {
                Console.WriteLine($"  {tab.name,-20} @ ({tab.x}, {tab.y})");
            }
            
            // Save to JSON
            SaveTabsToJson(tabs);
        }
    }
    
    struct TabInfo { public string name; public int x, y; }
    
    static async Task<List<TabInfo>> FindTabs(string imagePath, int offsetX, int offsetY)
    {
        var tabs = new List<TabInfo>();
        
        var ocrEngine = OcrEngine.TryCreateFromUserProfileLanguages() 
            ?? OcrEngine.TryCreateFromLanguage(new Windows.Globalization.Language("en-US"));
        
        using (var fileStream = File.OpenRead(imagePath))
        {
            var decoder = await BitmapDecoder.CreateAsync(fileStream.AsRandomAccessStream());
            var ocrResult = await ocrEngine.RecognizeAsync(await decoder.GetSoftwareBitmapAsync());
            
            // Find tab-like elements (upper part of window, y < 200)
            foreach (var line in ocrResult.Lines)
            {
                string text = line.Text.Trim();
                if (string.IsNullOrEmpty(text)) continue;
                
                // Get approximate position from first word
                if (line.Words.Count > 0)
                {
                    var firstWord = line.Words[0];
                    var rect = firstWord.BoundingRect;
                    int x = offsetX + (int)rect.X;
                    int y = offsetY + (int)rect.Y;
                    
                    // Filter for likely tabs (in top area)
                    if (y < 250 && text.Length > 1)
                    {
                        tabs.Add(new TabInfo { name = text, x = x, y = y });
                    }
                }
            }
        }
        
        return tabs;
    }
    
    static void SaveTabsToJson(List<TabInfo> tabs)
    {
        string json = "{\n  \"tabs\": [\n";
        for (int i = 0; i < tabs.Count; i++)
        {
            var t = tabs[i];
            json += $"    {{\"name\": \"{t.name}\", \"x\": {t.x}, \"y\": {t.y}}}";
            if (i < tabs.Count - 1) json += ",";
            json += "\n";
        }
        json += "  ]\n}";
        
        File.WriteAllText("D:/Project/WinAgent/windbg_tabs_ocr.json", json);
        Console.WriteLine("\nSaved to windbg_tabs_ocr.json");
    }
}
