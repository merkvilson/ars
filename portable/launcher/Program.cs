using System.Diagnostics;
using System.Text;

static class Program
{
    [STAThread]
    public static int Main(string[] args)
    {
        var exePath = Environment.ProcessPath;
        if (string.IsNullOrWhiteSpace(exePath))
        {
            exePath = Process.GetCurrentProcess().MainModule?.FileName;
        }
        if (string.IsNullOrWhiteSpace(exePath))
        {
            exePath = Path.Combine(AppContext.BaseDirectory, "ARS.exe");
        }

        var exeDir = Path.GetDirectoryName(exePath) ?? AppContext.BaseDirectory;

        // Expected layout:
        // <root>\python_embeded\python.exe
        // <root>\main.py
        // <root>\portable\ARS.exe (this launcher)
        // But make this robust by searching upward for main.py.
        var root = FindRoot(exeDir) ?? Path.GetFullPath(Path.Combine(exeDir, "..", ".."));
        var pyRoot = Path.Combine(root, "python_embeded");
        var pyExe = Path.Combine(pyRoot, "python.exe");
        var mainPy = Path.Combine(root, "main.py");
        var logPath = Path.Combine(root, "portable", "portable_run.log");

        WriteLog(logPath,
            $"\n=== ARS Launcher ===\n" +
            $"exePath: {exePath}\n" +
            $"exeDir : {exeDir}\n" +
            $"root   : {root}\n" +
            $"pyExe  : {pyExe}\n" +
            $"mainPy : {mainPy}\n");

        if (!File.Exists(pyExe))
        {
            WriteLog(logPath, $"[ERROR] Embedded python not found: {pyExe}\n");
            ShowMessage($"Embedded python not found.\n\nExpected:\n{pyExe}\n\nBuild it first using:\nportable\\build_portable.ps1");
            return 2;
        }

        if (!File.Exists(mainPy))
        {
            WriteLog(logPath, $"[ERROR] main.py not found: {mainPy}\n");
            ShowMessage($"main.py not found:\n{mainPy}");
            return 3;
        }

        try
        {
            // Help DLL discovery for packages like PyQt6 (Qt DLLs)
            var qtBin = Path.Combine(pyRoot, "Lib", "site-packages", "PyQt6", "Qt6", "bin");
            var currentPath = Environment.GetEnvironmentVariable("PATH") ?? string.Empty;
            var newPath = new StringBuilder();
            if (Directory.Exists(qtBin))
            {
                newPath.Append(qtBin).Append(';');
            }
            newPath.Append(pyRoot).Append(';');
            newPath.Append(Path.Combine(pyRoot, "Scripts")).Append(';');
            newPath.Append(currentPath);

            var psi = new ProcessStartInfo
            {
                FileName = pyExe,
                WorkingDirectory = root,
                UseShellExecute = false,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                CreateNoWindow = true,
            };

            // Avoid encoding-related exceptions and keep logs readable.
            psi.StandardOutputEncoding = Encoding.UTF8;
            psi.StandardErrorEncoding = Encoding.UTF8;

            // Let main.py run normally; it will handle stderr redirection unless ARS_SHOW_STDERR=1.
            psi.Environment["PATH"] = newPath.ToString();

            // Make prints/logging deterministic across no-console launches.
            psi.Environment["PYTHONUTF8"] = "1";
            // Use an explicit error handler so printing odd glyphs can never crash the process.
            psi.Environment["PYTHONIOENCODING"] = "utf-8:backslashreplace";
            // Some Windows setups behave better with legacy stdio when there's no console.
            psi.Environment["PYTHONLEGACYWINDOWSSTDIO"] = "1";

            // Preserve any user-provided ARS_SHOW_STDERR, otherwise default off.
            if (string.IsNullOrEmpty(Environment.GetEnvironmentVariable("ARS_SHOW_STDERR")))
            {
                psi.Environment["ARS_SHOW_STDERR"] = "0";
            }

            // Pass through args to main.py.
            psi.ArgumentList.Add("-u");
            psi.ArgumentList.Add(mainPy);
            foreach (var a in args) psi.ArgumentList.Add(a);

            using var process = new Process();
            process.StartInfo = psi;
            process.EnableRaisingEvents = true;

            object logLock = new();
            const long maxLogBytes = 5L * 1024 * 1024; // keep logs bounded
            long writtenBytes = 0;

            void WriteLineSafe(string prefix, string? line)
            {
                if (string.IsNullOrEmpty(line))
                {
                    return;
                }

                lock (logLock)
                {
                    if (writtenBytes > maxLogBytes)
                    {
                        return;
                    }

                    var text = prefix + line + "\n";
                    // Rough byte count; good enough for limiting.
                    writtenBytes += Encoding.UTF8.GetByteCount(text);
                    WriteLog(logPath, text);
                }
            }

            process.OutputDataReceived += (_, e) => WriteLineSafe("", e.Data);
            process.ErrorDataReceived += (_, e) => WriteLineSafe("[stderr] ", e.Data);

            if (!process.Start())
            {
                WriteLog(logPath, "[ERROR] Failed to start python process.\n");
                ShowMessage("Failed to start python process.");
                return 4;
            }

            process.BeginOutputReadLine();
            process.BeginErrorReadLine();
            var startedAt = DateTime.UtcNow;
            process.WaitForExit();

            var elapsedMs = (int)(DateTime.UtcNow - startedAt).TotalMilliseconds;

            WriteLog(logPath, $"exitCode: {process.ExitCode}\n" + $"elapsedMs: {elapsedMs}\n");

            // If it fails, show a friendly message and point to the log.
            if (process.ExitCode != 0)
            {
                ShowMessage($"ARS exited with code {process.ExitCode}.\n\nLog:\n{logPath}");
            }
            else if (elapsedMs < 1500)
            {
                // Exited almost immediately; that's usually unexpected for a GUI app.
                ShowMessage($"ARS exited immediately.\n\nLog:\n{logPath}");
            }

            return process.ExitCode;
        }
        catch (Exception ex)
        {
            WriteLog(logPath, $"[ERROR] Launcher exception:\n{ex}\n");
            ShowMessage($"Launcher exception.\n\nLog:\n{logPath}");
            return 5;
        }
    }

    private static void WriteLog(string path, string text)
    {
        try
        {
            Directory.CreateDirectory(Path.GetDirectoryName(path) ?? ".");
            File.AppendAllText(path, text);
        }
        catch
        {
            // ignore
        }
    }

    private static void ShowMessage(string message)
    {
        try
        {
            // Avoid a WinForms/WPF dependency; MessageBox exists in Win32.
            _ = NativeMessageBox(IntPtr.Zero, message, "ARS", 0);
        }
        catch
        {
            // ignore
        }
    }

    [System.Runtime.InteropServices.DllImport("user32.dll", CharSet = System.Runtime.InteropServices.CharSet.Unicode)]
    private static extern int NativeMessageBox(IntPtr hWnd, string text, string caption, uint type);

    private static string? FindRoot(string startDir)
    {
        try
        {
            var dir = new DirectoryInfo(startDir);
            for (var i = 0; i < 8 && dir != null; i++)
            {
                var candidate = dir.FullName;
                if (File.Exists(Path.Combine(candidate, "main.py")))
                {
                    return candidate;
                }
                dir = dir.Parent;
            }
        }
        catch
        {
            // ignore
        }

        return null;
    }
}
