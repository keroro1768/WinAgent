// Standalone test: dotnet run -- --test
// Add this to Program.cs Main() to test without GUI

using System;
using System.Threading.Tasks;
using WinAgent.Services;

namespace WinAgent;

public static class TestRunner
{
    public static async Task RunTest()
    {
        Console.WriteLine("=== ClaudeManager Test ===");
        Console.WriteLine();

        // Test 1: FindClaudePath (via constructor)
        Console.WriteLine("[Test 1] Creating ClaudeManager...");
        var manager = new ClaudeManager(workingDirectory: @"D:\Project\WinAgent");
        Console.WriteLine("[Test 1] OK - ClaudeManager created");
        Console.WriteLine();

        // Test 2: One-shot
        Console.WriteLine("[Test 2] Testing one-shot: 'Say hello in one sentence.'");
        var result = await manager.ExecuteOneShotAsync("Say hello in one sentence.", timeoutSeconds: 30);
        Console.WriteLine($"  Success: {result.Success}");
        Console.WriteLine($"  ExitCode: {result.ExitCode}");
        Console.WriteLine($"  Output: {result.Output}");
        if (!string.IsNullOrEmpty(result.Error))
            Console.WriteLine($"  Error: {result.Error}");
        Console.WriteLine();

        // Test 3: AskClaude convenience
        Console.WriteLine("[Test 3] Testing AskClaudeAsync...");
        string? answer = await manager.AskClaudeAsync("What is 2+2? Reply with just the number.", timeoutSeconds: 30);
        Console.WriteLine($"  Answer: {answer ?? "(null)"}");
        Console.WriteLine();

        Console.WriteLine("=== Tests Complete ===");
    }
}
