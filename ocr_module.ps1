# WinAgent OCR Module - Using Windows.Media.Ocr

Add-Type -AssemblyName System.Runtime.WindowsRuntime
Add-Type -AssemblyName Windows.Foundation

# Load Windows Media OCR
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType=WindowsRuntime]

# Check if OCR is supported
$isSupported = [Windows.Media.Ocr.OcrEngine]::IsSupported
Write-Host "OCR Supported: $isSupported"

if ($isSupported) {
    # Create OCR engine with user profile languages
    $asyncOp = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
    $ocrEngine = $asyncOp.GetResults()
    
    Write-Host "OCR Engine created successfully"
    
    # Function to capture screen and OCR
    function Get-ScreenOcr {
        param(
            [int]$X,
            [int]$Y,
            [int]$Width,
            [int]$Height
        )
        
        # Capture screen region
        Add-Type -AssemblyName System.Drawing
        
        $bitmap = New-Object System.Drawing.Bitmap($Width, $Height)
        $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
        $graphics.CopyFromScreen($X, $Y, 0, 0, (New-Object System.Drawing.Size($Width, $Height)))
        
        # Convert to BitmapImage for OCR
        $stream = New-Object System.IO.MemoryStream
        $bitmap.Save($stream, [System.Drawing.Imaging.ImageFormat]::Png)
        $stream.Seek(0, [System.IO.SeekOrigin]::Begin) | Out-Null
        
        # Create BitmapDecoder
        $bitmapImage = New-Object Windows.Storage.Streams.InMemoryRandomAccessStream
        $bitmapImage.AsStream().Write($stream.ToArray(), 0, $stream.Length)
        $bitmapImage.Seek(0) | Out-Null
        
        # Run OCR
        $decoder = [Windows.Storage.BitmapDecoder]::CreateAsync($bitmapImage)
        $decoderTask = $decoder.AsTask()
        $decodedImage = $decoderTask.Result
        
        $ocrTask = $ocrEngine.RecognizeAsync($decodedImage)
        $ocrResult = $ocrTask.Result
        
        # Extract text with positions
        $results = @()
        foreach ($line in $ocrResult.Lines) {
            $bounds = $line.BoundingRect
            $results += [PSCustomObject]@{
                Text = $line.Text
                X = $bounds.X
                Y = $bounds.Y
                Width = $bounds.Width
                Height = $bounds.Height
            }
            Write-Host "Found: $($line.Text) @ ($($bounds.X), $($bounds.Y))"
        }
        
        # Cleanup
        $graphics.Dispose()
        $bitmap.Dispose()
        $stream.Dispose()
        $bitmapImage.Dispose()
        
        return $results
    }
    
    # Export function
    New-Alias -Name Get-WinDbgOcr -Value Get-ScreenOcr -Scope Global
    
    Write-Host ""
    Write-Host "OCR functions loaded:"
    Write-Host "  Get-ScreenOcr -X -Y -Width -Height"
    Write-Host "  Get-WinDbgOcr -X -Y -Width -Height"
}
else {
    Write-Host "OCR is not supported on this system"
}
