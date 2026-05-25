namespace oonv.Patterns;

// ── Třída s Clone() ────────────────────────────────────────────────────────
public class Contact
{
    public string Name  { get; set; } = "";
    public string Phone { get; set; } = "";
    public string Email { get; set; } = "";

    public Contact Clone() => new Contact
    {
        Name  = Name,
        Phone = Phone,
        Email = Email
    };

    public override string ToString() => $"{Name} | {Phone} | {Email}";
}

// ── Demo ───────────────────────────────────────────────────────────────────
public static class PrototypeDemo
{
    public static void Run()
    {
        Console.WriteLine("=== Prototype ===\n");

        var original = new Contact { Name = "Jan Novák", Phone = "123456789", Email = "jan@email.cz" };
        Console.WriteLine($"Originál: {original}");

        // Klonujeme a upravíme jen co potřebujeme
        var klon = original.Clone();
        klon.Name = "Petr Novák";
        klon.Email = "petr@email.cz";
        Console.WriteLine($"Klon:     {klon}");

        // Originál nezměněn
        Console.WriteLine($"Originál po změně klonu: {original}");

        // Důkaz že jde o různé objekty
        Console.WriteLine($"\nRůzné objekty: {!ReferenceEquals(original, klon)}");
    }
}
