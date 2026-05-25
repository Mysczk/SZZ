namespace oonv.Patterns;

// ── Rozhraní ───────────────────────────────────────────────────────────────
public interface IMessage
{
    string GetText();
}

// ── Základní implementace ──────────────────────────────────────────────────
public class SimpleMessage : IMessage
{
    private readonly string _text;
    public SimpleMessage(string text) => _text = text;
    public string GetText() => _text;
}

// ── Dekorátory ─────────────────────────────────────────────────────────────
// Každý obalí předchozí objekt a přidá chování

public class BracketDecorator : IMessage
{
    private readonly IMessage _inner;
    public BracketDecorator(IMessage inner) => _inner = inner;
    public string GetText() => $"[{_inner.GetText()}]";
}

public class ExclamationDecorator : IMessage
{
    private readonly IMessage _inner;
    public ExclamationDecorator(IMessage inner) => _inner = inner;
    public string GetText() => _inner.GetText() + "!!!";
}

public class UpperCaseDecorator : IMessage
{
    private readonly IMessage _inner;
    public UpperCaseDecorator(IMessage inner) => _inner = inner;
    public string GetText() => _inner.GetText().ToUpper();
}

// ── Demo ───────────────────────────────────────────────────────────────────
public static class DecoratorDemo
{
    public static void Run()
    {
        Console.WriteLine("=== Decorator ===\n");

        IMessage msg = new SimpleMessage("ahoj");
        Console.WriteLine($"Základní:    {msg.GetText()}");

        msg = new BracketDecorator(msg);
        Console.WriteLine($"+ Závorky:   {msg.GetText()}");

        msg = new ExclamationDecorator(msg);
        Console.WriteLine($"+ Vykřičník: {msg.GetText()}");

        msg = new UpperCaseDecorator(msg);
        Console.WriteLine($"+ Uppercase: {msg.GetText()}");

        // Různé kombinace
        Console.WriteLine("\nRůzné kombinace:");
        Console.WriteLine(new ExclamationDecorator(new SimpleMessage("čau")).GetText());
        Console.WriteLine(new UpperCaseDecorator(new BracketDecorator(new SimpleMessage("test"))).GetText());
    }
}
