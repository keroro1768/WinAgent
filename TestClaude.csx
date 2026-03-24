// Quick test script - run with: dotnet-script TestClaude.csx
// Or just use dotnet run approach below

using System.Diagnostics;
using System.Text;

string claudePath = @"C:\Users\Keror\.local\bin\claude.exe";
string workDir = @"D:\Project\WinAgent";
string prompt = "Say hello in one sentence.";

Console.WriteLine($"Claude path: {claudePath}");
Console.WriteLine($"Exists: {File.Exists(claudePath)}");
Console.WriteLine($"Testing one-shot...");

var args = $"--print --output-format text --dangerously-skip-permissions -p \"{prompt}\"";
Console.WriteLine($"Args: {args}");

var psi = new ProcessStartInfo
{
    FileName = claudePath,
    Arguments = args,
    UseShellExecute = false,
    RedirectStandardOutput = true,
    RedirectStandardError = true,
    CreateNoWindow = true,
    WorkingDirectory = workDir
};

var outputSb = new StringBuilder();
var errorSb = new StringBuilder();

var process = new Process { StartInfo = psi };
process.OutputDataReceived += (s, e) => { if (e.Data != null) outputSb.AppendLine(e.Data); };
process.ErrorDataReceived += (s, e) => { if (e.Data != null) errorSb.AppendLine(e.Data); };

process.Start();
Console.WriteLine($"PID: {process.Id}");
process.BeginOutputReadLine();
process.BeginErrorReadLine();

bool exited = process.WaitForExit(60000);
Console.WriteLine($"Exited: {exited}, ExitCode: {(exited ? process.ExitCode : -1)}");
Console.WriteLine($"--- STDOUT ---");
Console.WriteLine(outputSb.ToString());
Console.WriteLine($"--- STDERR ---");
Console.WriteLine(errorSb.ToString());
