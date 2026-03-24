// WinAgent OCR - Using Windows.Media.Ocr
// Compile: csc /r:"C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETCore\v5.0\System.Runtime.WindowsRuntime.dll" /r:"C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETCore\v5.0\Windows.UI.Xaml.dll" /r:"C:\Program Files (x86)\Reference Assemblies\Microsoft\Framework\.NETCore\v5.0\Windows.Foundation.dll" ocr.cs

using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Runtime.InteropServices;
using System.Windows;
using System.Windows.Media.Imaging;

class OcrApp
{
    [DllImport("user32.dll")]
    static extern bool GetWindowRect(IntPtr hWnd, ref RECT rect);

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT
    {
        public int Left;
        public int Top;
        public int Right;
        public int Bottom;
    }

    public static void Main(string[] args)
    {
        // Get WinDBG window
        IntPtr hwnd = new IntPtr(0x50720);
        
        RECT rect = new RECT();
        GetWindowRect(hwnd, ref rect);
        
        int width = rect.Right - rect.Left;
        int height = rect.Bottom - rect.Top;
        
        Console.WriteLine($"Window: {rect.Left}, {rect.Top}, {width}x{height}");
        
        // Take screenshot
        using (Bitmap bitmap = new Bitmap(width, height))
        {
            using (Graphics g = Graphics.FromImage(bitmap))
            {
                g.CopyFromScreen(rect.Left, rect.Top, 0, 0, new System.Drawing.Size(width, height));
            }
            
            string tempPath = Path.Combine(Path.GetTempPath(), "windbg_screen.png");
            bitmap.Save(tempPath, ImageFormat.Png);
            Console.WriteLine($"Screenshot saved: {tempPath}");
        }
        
        // Use Windows OCR
        try
        {
            var asyncOp = Windows.Media.Ocr.OcrEngine.TryCreateFromUserProfileLanguages();
            var ocrEngine = asyncOp.GetResults();
            
            if (ocrEngine == null)
            {
                Console.WriteLine("OCR Engine not available");
                return;
            }
            
            // Load image
            using (var fileStream = File.OpenRead(Path.Combine(Path.GetTempPath(), "windbg_screen.png")))
            {
                var decoder = BitmapDecoder.Create(fileStream, BitmapCreateOptions.PreservePixelFormat, BitmapCacheOption.OnLoad);
                var bitmap = decoder.Frames[0];
                
                var ocrResult = ocrEngine.RecognizeAsync(bitmap).GetResults();
                
                Console.WriteLine("\n=== OCR Results ===");
                foreach (var line in ocrResult.Lines)
                {
                    Console.WriteLine(line.Text);
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"OCR Error: {ex.Message}");
        }
    }
}
