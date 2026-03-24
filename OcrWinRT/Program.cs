// WinAgent OCR - Using Windows Runtime OCR
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Runtime.InteropServices;
using System.Threading.Tasks;
using Windows.Graphics.Imaging;
using Windows.Media.Ocr;
using Windows.Storage.Streams;

class Program
{
    [DllImport("user32.dll")]
    static extern bool GetWindowRect(IntPtr hWnd, ref RECT lpRect);

    [StructLayout(LayoutKind.Sequential)]
    public struct RECT
    {
        public int Left, Top, Right, Bottom;
    }

    static async Task Main(string[] args)
    {
        // Get WinDBG window handle
        IntPtr hwnd = new IntPtr(0x50720); // Change as needed
        
        RECT rect = new RECT();
        GetWindowRect(hwnd, ref rect);
        
        int width = rect.Right - rect.Left;
        int height = rect.Bottom - rect.Top;
        
        Console.WriteLine($"Window: {rect.Left}, {rect.Top}, {width}x{height}");
        
        // Capture screen
        using (Bitmap bitmap = new Bitmap(width, height))
        {
            using (Graphics g = Graphics.FromImage(bitmap))
            {
                g.CopyFromScreen(rect.Left, rect.Top, 0, 0, new System.Drawing.Size(width, height));
            }
            
            string tempFile = Path.Combine(Path.GetTempPath(), "winagent_ocr.png");
            bitmap.Save(tempFile, ImageFormat.Png);
            Console.WriteLine($"Screenshot: {tempFile}");
            
            // OCR
            await PerformOcr(tempFile);
        }
    }
    
    static async Task PerformOcr(string imagePath)
    {
        try
        {
            // Check if OCR is supported
            if (!OcrEngine.IsSupported)
            {
                Console.WriteLine("OCR not supported");
                return;
            }
            
            // Create OCR engine
            var ocrEngine = OcrEngine.TryCreateFromUserProfileLanguages();
            Console.WriteLine("OCR Engine created");
            
            // Load image
            using (var fileStream = File.OpenRead(imagePath))
            {
                var decoder = await BitmapDecoder.CreateAsync(fileStream.AsRandomAccessStream());
                var softwareBitmap = await decoder.GetSoftwareBitmapAsync();
                
                // Recognize text
                var ocrResult = await ocrEngine.RecognizeAsync(softwareBitmap);
                
                Console.WriteLine("\n=== OCR Results ===");
                foreach (var line in ocrResult.Lines)
                {
                    var bounds = line.BoundingRect;
                    Console.WriteLine($"[{bounds.X},{bounds.Y}] {line.Text}");
                }
            }
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Error: {ex.Message}");
        }
    }
}
