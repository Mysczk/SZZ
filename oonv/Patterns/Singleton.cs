namespace oonv.Patterns;

// ── Třída ──────────────────────────────────────────────────────────────────
// private konstruktor → nikdo zvenku nemůže volat new AppConfig()
// static Instance → jediný způsob jak se dostat k instanci
// ??= → vytvoří instanci jen pokud ještě neexistuje

public class AppConfig
{
    private static AppConfig? _instance;
    public static AppConfig Instance => _instance ??= new AppConfig();

    public string AppName  { get; set; } = "MojeAplikace";
    public bool   DebugMode { get; set; } = false;

    private AppConfig() { }
}

// ── Demo ───────────────────────────────────────────────────────────────────
public static class SingletonDemo
{
    public static void Run()
    {
        Console.WriteLine("=== Singleton ===\n");

        AppConfig.Instance.DebugMode = true;
        AppConfig.Instance.AppName   = "SuperApp";

        // Druhý přístup vrátí stejnou instanci
        var config = AppConfig.Instance;
        Console.WriteLine($"AppName:   {config.AppName}");
        Console.WriteLine($"DebugMode: {config.DebugMode}");

        // Důkaz že jde o stejný objekt
        Console.WriteLine($"\nStejna instance: {ReferenceEquals(AppConfig.Instance, config)}");
    }
}
