using System;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Threading;
using System.Windows.Forms;

namespace SlopeGuardAI;

internal static class Program
{
    private const string Url = "http://127.0.0.1:8765";

    [STAThread]
    private static void Main()
    {
        try
        {
            string appRoot = FindAppRoot();
            Directory.CreateDirectory(Path.Combine(appRoot, "logs"));

            if (!IsBackendReady())
            {
                StartBackend(appRoot);
                WaitForBackend();
            }

            if (!IsBackendReady())
            {
                Fail("SlopeGuard AI backend did not start. Check logs in:\n" + Path.Combine(appRoot, "logs"));
                return;
            }

            OpenDesktopWindow(appRoot);
        }
        catch (Exception ex)
        {
            Fail(ex.Message);
        }
    }

    private static string FindAppRoot()
    {
        string exeDir = AppContext.BaseDirectory;
        string current = Directory.GetCurrentDirectory();
        string[] candidates =
        {
            exeDir,
            Path.Combine(exeDir, "slideagent-ai"),
            Path.Combine(exeDir, "SlopeGuard_AI_App"),
            Path.GetFullPath(Path.Combine(exeDir, "..", "slideagent-ai")),
            Path.GetFullPath(Path.Combine(exeDir, "..", "..", "slideagent-ai")),
            current,
            Path.Combine(current, "slideagent-ai")
        };

        string? appRoot = candidates.FirstOrDefault(dir => File.Exists(Path.Combine(dir, "backend", "server.py")));
        if (appRoot == null)
        {
            throw new InvalidOperationException(
                "Could not find the SlopeGuard AI app folder.\n\n" +
                "Keep this EXE in the delivery folder next to the original slideagent-ai folder, " +
                "or copy the app into a folder named SlopeGuard_AI_App beside the EXE.");
        }
        return appRoot;
    }

    private static bool IsBackendReady()
    {
        try
        {
            using HttpClient client = new() { Timeout = TimeSpan.FromSeconds(1) };
            using HttpResponseMessage response = client.GetAsync(Url + "/api/project").GetAwaiter().GetResult();
            return response.IsSuccessStatusCode;
        }
        catch
        {
            return false;
        }
    }

    private static void StartBackend(string appRoot)
    {
        string python = FindPython();
        string stdout = Path.Combine(appRoot, "logs", "desktop_backend.log");
        string stderr = Path.Combine(appRoot, "logs", "desktop_backend_error.log");

        ProcessStartInfo startInfo = new()
        {
            FileName = python,
            Arguments = "backend\\server.py",
            WorkingDirectory = appRoot,
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true
        };

        Process process = new() { StartInfo = startInfo, EnableRaisingEvents = true };
        process.OutputDataReceived += (_, e) => AppendLine(stdout, e.Data);
        process.ErrorDataReceived += (_, e) => AppendLine(stderr, e.Data);
        process.Start();
        process.BeginOutputReadLine();
        process.BeginErrorReadLine();
    }

    private static string FindPython()
    {
        string bundled = @"C:\Users\Lenovo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe";
        if (File.Exists(bundled)) return bundled;
        return "python";
    }

    private static void WaitForBackend()
    {
        for (int i = 0; i < 60; i++)
        {
            if (IsBackendReady()) return;
            Thread.Sleep(500);
        }
    }

    private static void OpenDesktopWindow(string appRoot)
    {
        string? browser = FindBrowser();
        if (browser == null)
        {
            Process.Start(new ProcessStartInfo(Url) { UseShellExecute = true });
            return;
        }

        string profile = Path.Combine(appRoot, "desktop_profile");
        Directory.CreateDirectory(profile);
        Process.Start(new ProcessStartInfo
        {
            FileName = browser,
            Arguments = $"--app={Url} --window-size=1400,900 --user-data-dir=\"{profile}\"",
            UseShellExecute = false
        });
    }

    private static string? FindBrowser()
    {
        string[] candidates =
        {
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "Microsoft", "Edge", "Application", "msedge.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Microsoft", "Edge", "Application", "msedge.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Google", "Chrome", "Application", "chrome.exe"),
            Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86), "Google", "Chrome", "Application", "chrome.exe")
        };
        return candidates.FirstOrDefault(File.Exists);
    }

    private static void AppendLine(string path, string? line)
    {
        if (line == null) return;
        try
        {
            File.AppendAllText(path, line + Environment.NewLine);
        }
        catch
        {
            // Logging should never prevent the app from opening.
        }
    }

    private static void Fail(string message)
    {
        MessageBox.Show(message, "SlopeGuard AI", MessageBoxButtons.OK, MessageBoxIcon.Error);
    }
}
