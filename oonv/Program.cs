using oonv.Patterns;

while (true)
{
    Console.Clear();
    Console.WriteLine("=== Návrhové vzory ===\n");
    Console.WriteLine(" 1) Singleton");
    Console.WriteLine(" 2) Factory Method");
    Console.WriteLine(" 3) Prototype");
    Console.WriteLine(" 4) Adapter");
    Console.WriteLine(" 5) Decorator");
    Console.WriteLine(" 6) Bridge");
    Console.WriteLine(" 7) Flyweight");
    Console.WriteLine(" 8) Command");
    Console.WriteLine(" 9) Observer");
    Console.WriteLine("10) Iterator");
    Console.WriteLine("11) Memento");
    Console.WriteLine("12) Strategy");
    Console.WriteLine("\n 0) Konec");
    Console.Write("\nVyber vzor: ");

    switch (Console.ReadLine()?.Trim())
    {
        case "1":  SingletonDemo.Run();     break;
        case "2":  FactoryMethodDemo.Run(); break;
        case "3":  PrototypeDemo.Run();     break;
        case "4":  AdapterDemo.Run();       break;
        case "5":  DecoratorDemo.Run();     break;
        case "6":  BridgeDemo.Run();        break;
        case "7":  FlyweightDemo.Run();     break;
        case "8":  CommandDemo.Run();       break;
        case "9":  ObserverDemo.Run();      break;
        case "10": IteratorDemo.Run();      break;
        case "11": MementoDemo.Run();       break;
        case "12": StrategyDemo.Run();      break;
        case "0":  return;
        default:   Console.WriteLine("Neznámá volba."); break;
    }

    Console.WriteLine("\nStiskni Enter...");
    Console.ReadLine();
}
