namespace oonv.Patterns;

// ── Co klient očekává ──────────────────────────────────────────────────────
public interface ILogger
{
    void Log(string message);
    void LogError(string message);
}

// ── Stará třída kterou nemůžeme změnit ────────────────────────────────────
public class OldPrinter
{
    public void PrintLine(string text, string level)
        => Console.WriteLine($"[{level}] {text}");
}

// ── Adaptér ────────────────────────────────────────────────────────────────
// Obalí OldPrinter a přizpůsobí ho rozhraní ILogger
public class PrinterAdapter : ILogger
{
    private readonly OldPrinter _printer = new();

    public void Log(string message)      => _printer.PrintLine(message, "INFO");
    public void LogError(string message) => _printer.PrintLine(message, "ERROR");
}

// ── Demo ───────────────────────────────────────────────────────────────────
public static class AdapterDemo
{
    public static void Run()
    {
        Console.WriteLine("=== Adapter ===\n");

        // Klient pracuje jen s ILogger – neví nic o OldPrinter
        ILogger logger = new PrinterAdapter();
        logger.Log("Aplikace spuštěna");
        logger.LogError("Něco se pokazilo");
    }
}
