namespace oonv.Patterns;

// ── Produkt ────────────────────────────────────────────────────────────────
public abstract class Animal
{
    public abstract void Speak();
}

public class Dog : Animal
{
    public override void Speak() => Console.WriteLine("Haf!");
}

public class Cat : Animal
{
    public override void Speak() => Console.WriteLine("Mňau!");
}

// ── Továrna ────────────────────────────────────────────────────────────────
// Abstraktní třída s tovární metodou Create()
// Každá podtřída rozhoduje co se vytvoří

public abstract class AnimalFactory
{
    public abstract Animal Create();

    public void CreateAndSpeak()
    {
        var animal = Create();           // zavolá konkrétní továrnu
        Console.Write("Zvíře říká: ");
        animal.Speak();
    }
}

public class DogFactory : AnimalFactory
{
    public override Animal Create() => new Dog();
}

public class CatFactory : AnimalFactory
{
    public override Animal Create() => new Cat();
}

// ── Demo ───────────────────────────────────────────────────────────────────
public static class FactoryMethodDemo
{
    public static void Run()
    {
        Console.WriteLine("=== Factory Method ===\n");

        AnimalFactory factory = new DogFactory();
        factory.CreateAndSpeak();    // Haf!

        factory = new CatFactory();
        factory.CreateAndSpeak();    // Mňau!

        // Polymorfismus – kód klienta nezná konkrétní typ
        var factories = new List<AnimalFactory> { new DogFactory(), new CatFactory(), new DogFactory() };
        Console.WriteLine("\nVšechna zvířata:");
        foreach (var f in factories)
            f.CreateAndSpeak();
    }
}
