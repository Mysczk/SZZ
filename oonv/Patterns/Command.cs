namespace oonv.Patterns;

// ── Rozhraní ───────────────────────────────────────────────────────────────
public interface ICommand
{
    void Execute();
    void Undo();
    string Description { get; }
}

// ── Konkrétní příkazy ──────────────────────────────────────────────────────
public class AddCommand : ICommand
{
    private readonly List<string> _list;
    private readonly string _item;

    public string Description => $"Přidán: {_item}";

    public AddCommand(List<string> list, string item)
        => (_list, _item) = (list, item);

    public void Execute() => _list.Add(_item);
    public void Undo()    => _list.Remove(_item);
}

public class ClearCommand : ICommand
{
    private readonly List<string> _list;
    private List<string> _backup = new();

    public string Description => "Smazáno vše";

    public ClearCommand(List<string> list) => _list = list;

    public void Execute() { _backup = new List<string>(_list); _list.Clear(); }
    public void Undo()    { _list.Clear(); _list.AddRange(_backup); }
}

// ── Invoker ────────────────────────────────────────────────────────────────
public class CommandManager
{
    private readonly Stack<ICommand> _history = new();

    public void Execute(ICommand cmd)
    {
        cmd.Execute();
        _history.Push(cmd);
        Console.WriteLine($"  ✓ {cmd.Description}");
    }

    public void Undo()
    {
        if (_history.Count == 0) { Console.WriteLine("  Nic k vrácení."); return; }
        var cmd = _history.Pop();
        cmd.Undo();
        Console.WriteLine($"  ↩ Vráceno: {cmd.Description}");
    }
}

// ── Demo ───────────────────────────────────────────────────────────────────
public static class CommandDemo
{
    public static void Run()
    {
        Console.WriteLine("=== Command ===\n");

        var list    = new List<string>();
        var manager = new CommandManager();

        manager.Execute(new AddCommand(list, "Jablko"));
        manager.Execute(new AddCommand(list, "Hruška"));
        manager.Execute(new AddCommand(list, "Švestka"));
        Console.WriteLine($"  Seznam: {string.Join(", ", list)}");

        manager.Execute(new ClearCommand(list));
        Console.WriteLine($"  Seznam: [{string.Join(", ", list)}]");

        Console.WriteLine("\nUndo:");
        manager.Undo();
        Console.WriteLine($"  Seznam: {string.Join(", ", list)}");

        manager.Undo();
        Console.WriteLine($"  Seznam: {string.Join(", ", list)}");
    }
}
