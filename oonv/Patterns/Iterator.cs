namespace oonv.Patterns;

// ── Kolekce implementující IEnumerable<T> ──────────────────────────────────
public class NumberCollection : IEnumerable<int>
{
    private readonly List<int> _numbers = new();

    public void Add(int n) => _numbers.Add(n);

    // Deleguje na List<int> – foreach automaticky funguje
    public IEnumerator<int> GetEnumerator() => _numbers.GetEnumerator();
    System.Collections.IEnumerator System.Collections.IEnumerable.GetEnumerator()
        => GetEnumerator();

    // Vlastní iterátor přes yield return – vrací prvky líně (lazy)
    public IEnumerable<int> GetEvenNumbers()
    {
        foreach (var n in _numbers)
            if (n % 2 == 0)
                yield return n;
    }

    public IEnumerable<int> GetLargerThan(int threshold)
    {
        foreach (var n in _numbers)
            if (n > threshold)
                yield return n;
    }
}

// ── Demo ───────────────────────────────────────────────────────────────────
public static class IteratorDemo
{
    public static void Run()
    {
        Console.WriteLine("=== Iterator ===\n");

        var col = new NumberCollection();
        foreach (var n in new[] { 3, 7, 2, 8, 1, 6, 4, 9, 5 })
            col.Add(n);

        Console.Write("Všechna čísla:   ");
        foreach (var n in col) Console.Write(n + " ");

        Console.Write("\nSudá čísla:      ");
        foreach (var n in col.GetEvenNumbers()) Console.Write(n + " ");

        Console.Write("\nVětší než 5:     ");
        foreach (var n in col.GetLargerThan(5)) Console.Write(n + " ");

        Console.WriteLine();
    }
}
