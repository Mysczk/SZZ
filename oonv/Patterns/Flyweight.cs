namespace oonv.Patterns;

// ── Sdílený stav (intrinsic) ───────────────────────────────────────────────
// Vytvoří se jen jednou pro každý typ stromu
public class TreeType
{
    public string Name  { get; }
    public string Color { get; }

    public TreeType(string name, string color)
        => (Name, Color) = (name, color);

    public void Display(int x, int y)
        => Console.WriteLine($"  [{x,2},{y,2}] {Name} ({Color})");
}

// ── Factory – sdílí instance ───────────────────────────────────────────────
public class TreeFactory
{
    private readonly Dictionary<string, TreeType> _cache = new();

    public TreeType Get(string name, string color)
    {
        var key = $"{name}_{color}";
        if (!_cache.ContainsKey(key))
        {
            _cache[key] = new TreeType(name, color);
            Console.WriteLine($"  [Factory] Vytvořen nový TreeType: {key}");
        }
        return _cache[key];
    }

    public int CachedCount => _cache.Count;
}

// ── Unikátní stav (extrinsic) ──────────────────────────────────────────────
public class Tree
{
    public int      X    { get; set; }
    public int      Y    { get; set; }
    public TreeType Type { get; set; } = null!;

    public void Display() => Type.Display(X, Y);
}

// ── Demo ───────────────────────────────────────────────────────────────────
public static class FlyweightDemo
{
    public static void Run()
    {
        Console.WriteLine("=== Flyweight ===\n");

        var factory = new TreeFactory();

        var trees = new List<Tree>
        {
            new() { X=1,  Y=2,  Type = factory.Get("Dub",      "Zelená") },
            new() { X=5,  Y=8,  Type = factory.Get("Dub",      "Zelená") },  // sdílí TreeType
            new() { X=3,  Y=1,  Type = factory.Get("Borovice", "Tmavá")  },
            new() { X=7,  Y=4,  Type = factory.Get("Dub",      "Zelená") },  // sdílí TreeType
            new() { X=2,  Y=9,  Type = factory.Get("Borovice", "Tmavá")  },  // sdílí TreeType
        };

        Console.WriteLine("\nStromu celkem: " + trees.Count);
        Console.WriteLine("TreeType objektů: " + factory.CachedCount);
        Console.WriteLine("\nVšechny stromy:");
        trees.ForEach(t => t.Display());
    }
}
