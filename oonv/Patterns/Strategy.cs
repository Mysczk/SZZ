namespace oonv.Patterns;

// ── Rozhraní strategie ─────────────────────────────────────────────────────
public interface ISortStrategy
{
    void Sort(List<int> data);
    string Name { get; }
}

// ── Konkrétní strategie ────────────────────────────────────────────────────
public class AscendingSort : ISortStrategy
{
    public string Name => "Vzestupně";
    public void Sort(List<int> data) => data.Sort();
}

public class DescendingSort : ISortStrategy
{
    public string Name => "Sestupně";
    public void Sort(List<int> data) => data.Sort((a, b) => b.CompareTo(a));
}

public class AbsoluteSort : ISortStrategy
{
    public string Name => "Podle abs. hodnoty";
    public void Sort(List<int> data) => data.Sort((a, b) => Math.Abs(a).CompareTo(Math.Abs(b)));
}

// ── Context ────────────────────────────────────────────────────────────────
public class Sorter
{
    private ISortStrategy _strategy;

    public Sorter(ISortStrategy strategy) => _strategy = strategy;

    // Strategie lze vyměnit za běhu
    public void SetStrategy(ISortStrategy strategy)
    {
        _strategy = strategy;
        Console.WriteLine($"  Strategie změněna na: {strategy.Name}");
    }

    public void Sort(List<int> data)
    {
        _strategy.Sort(data);
        Console.WriteLine($"  [{_strategy.Name}] {string.Join(", ", data)}");
    }
}

// ── Demo ───────────────────────────────────────────────────────────────────
public static class StrategyDemo
{
    public static void Run()
    {
        Console.WriteLine("=== Strategy ===\n");

        var data   = new List<int> { 5, -2, 8, -1, 9, 3 };
        var sorter = new Sorter(new AscendingSort());

        Console.WriteLine($"  Vstup: {string.Join(", ", data)}");
        sorter.Sort(new List<int>(data));

        sorter.SetStrategy(new DescendingSort());
        sorter.Sort(new List<int>(data));

        sorter.SetStrategy(new AbsoluteSort());
        sorter.Sort(new List<int>(data));
    }
}
