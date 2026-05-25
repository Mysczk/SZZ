namespace oonv.Patterns;

// ── Implementační rozhraní ─────────────────────────────────────────────────
public interface IRenderer
{
    void Render(string shape);
}

public class ConsoleRenderer : IRenderer
{
    public void Render(string shape) => Console.WriteLine($"Konzole: {shape}");
}

public class FileRenderer : IRenderer
{
    public void Render(string shape) => Console.WriteLine($"Soubor:  {shape}");
}

// ── Abstrakce ──────────────────────────────────────────────────────────────
// Drží referenci na implementaci – lze ji vyměnit za běhu
public abstract class Shape
{
    protected IRenderer _renderer;
    protected Shape(IRenderer renderer) => _renderer = renderer;
    public abstract void Draw();
}

public class Circle : Shape
{
    public Circle(IRenderer r) : base(r) { }
    public override void Draw() => _renderer.Render("Kruh");
}

public class Square : Shape
{
    public Square(IRenderer r) : base(r) { }
    public override void Draw() => _renderer.Render("Čtverec");
}

// ── Demo ───────────────────────────────────────────────────────────────────
public static class BridgeDemo
{
    public static void Run()
    {
        Console.WriteLine("=== Bridge ===\n");

        // Libovolná kombinace tvaru a rendereru
        new Circle(new ConsoleRenderer()).Draw();
        new Circle(new FileRenderer()).Draw();
        new Square(new ConsoleRenderer()).Draw();
        new Square(new FileRenderer()).Draw();
    }
}
