namespace oonv.Patterns;

// ── Rozhraní ───────────────────────────────────────────────────────────────
public interface IObserver
{
    void Update(string message);
    string Name { get; }
}

// ── Subject ────────────────────────────────────────────────────────────────
public class EventSource
{
    private readonly List<IObserver> _observers = new();

    public void Subscribe(IObserver o)
    {
        _observers.Add(o);
        Console.WriteLine($"  + {o.Name} se přihlásil");
    }

    public void Unsubscribe(IObserver o)
    {
        _observers.Remove(o);
        Console.WriteLine($"  - {o.Name} se odhlásil");
    }

    private void Notify(string message)
    {
        foreach (var o in _observers)
            o.Update(message);
    }

    private string _status = "";
    public string Status
    {
        get => _status;
        set
        {
            _status = value;
            Console.WriteLine($"\n  [Zdroj] Nový stav: {value}");
            Notify(value);
        }
    }
}

// ── Observeři ─────────────────────────────────────────────────────────────
public class LogObserver : IObserver
{
    public string Name { get; }
    public LogObserver(string name) => Name = name;
    public void Update(string message) => Console.WriteLine($"    [{Name}] přijal: {message}");
}

// ── Demo ───────────────────────────────────────────────────────────────────
public static class ObserverDemo
{
    public static void Run()
    {
        Console.WriteLine("=== Observer ===\n");

        var source = new EventSource();
        var a = new LogObserver("Logger A");
        var b = new LogObserver("Logger B");
        var c = new LogObserver("Logger C");

        source.Subscribe(a);
        source.Subscribe(b);
        source.Subscribe(c);

        source.Status = "Spuštěno";

        source.Unsubscribe(b);

        source.Status = "Zastaveno";
    }
}
